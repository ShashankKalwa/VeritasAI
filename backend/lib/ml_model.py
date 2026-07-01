"""
VeritasAI ML Model — Multi-Engine Detection System (Parallel, Pooled)

Engines:
1. HuggingFace BERT Fake News Detector
2. ClaimBuster DeBERTaV2 (claim worthiness)
3. Google Fact Check Tools API
"""
import os
import logging
import httpx
from lib import cache

logger = logging.getLogger(__name__)

HF_FAKE_NEWS_MODEL = "jy46604790/Fake-News-Bert-Detect"
HF_BASE_URL = "https://api-inference.huggingface.co/models"
GOOGLE_FACTCHECK_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

# Shared async client — connection pooling for speed
_shared_client: httpx.AsyncClient | None = None


async def _client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(timeout=5.0)
    return _shared_client


def _get_hf_token():
    return os.getenv("HF_API_TOKEN", "")

def _get_cb_model():
    return os.getenv("CLAIMBUSTER_HF_MODEL", "whispAI/ClaimBuster-DeBERTaV2")

def _get_gfc_key():
    return os.getenv("GOOGLE_FACTCHECK_API_KEY", "")


class HuggingFaceDetector:
    def __init__(self):
        self.token = _get_hf_token()
        self.available = bool(self.token)
        if self.available:
            logger.info(f"✅ HF Fake News detector: {HF_FAKE_NEWS_MODEL}")

    async def predict(self, text: str) -> dict | None:
        if not self.available:
            return None
            
        cached = cache.get_hf("bert", text)
        if cached is not None:
            return cached

        try:
            c = await _client()
            resp = await c.post(
                f"{HF_BASE_URL}/{HF_FAKE_NEWS_MODEL}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"inputs": text[:512]},
            )
            if resp.status_code != 200:
                logger.warning(f"HF API: {resp.status_code}")
                return None
            results = resp.json()
            if not results or not isinstance(results, list):
                return None
            preds = results[0] if isinstance(results[0], list) else results
            fake_score, real_score = 0.0, 0.0
            for p in preds:
                label = p.get("label", "").upper()
                score = p.get("score", 0.0)
                if "FAKE" in label or label == "LABEL_0":
                    fake_score = score
                elif "REAL" in label or label == "LABEL_1":
                    real_score = score
            if fake_score == 0.0 and real_score > 0:
                fake_score = 1.0 - real_score
            elif real_score == 0.0 and fake_score > 0:
                real_score = 1.0 - fake_score
            verdict = "FAKE" if fake_score > real_score else "REAL"
            confidence = min(round(max(fake_score, real_score) * 100), 99)
            logger.info(f"HF: {verdict} ({confidence}%)")
            
            result = {"verdict": verdict, "confidence": confidence, "engine": "huggingface_bert"}
            cache.set_hf("bert", text, result)
            return result
        except httpx.TimeoutException:
            logger.warning("HF timeout")
            return None
        except Exception as e:
            logger.error(f"HF error: {e}")
            return None


class ClaimBusterHF:
    def __init__(self):
        self.token = _get_hf_token()
        self.model = _get_cb_model()
        self.available = bool(self.token)
        if self.available:
            logger.info(f"✅ ClaimBuster: {self.model}")

    async def check(self, text: str) -> dict | None:
        if not self.available:
            return None
            
        cached = cache.get_hf("claimbuster", text)
        if cached is not None:
            return cached

        try:
            c = await _client()
            resp = await c.post(
                f"{HF_BASE_URL}/{self.model}",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"inputs": text[:512]},
            )
            if resp.status_code != 200:
                logger.warning(f"ClaimBuster API: {resp.status_code}")
                return None
            results = resp.json()
            if not results or not isinstance(results, list):
                return None
            preds = results[0] if isinstance(results[0], list) else results
            cfs_score, nfs_score = 0.0, 0.0
            for p in preds:
                label = p.get("label", "").upper()
                score = p.get("score", 0.0)
                if "CFS" in label or "CHECK" in label or "CLAIM" in label:
                    cfs_score = score
                elif "NFS" in label or "NON" in label:
                    nfs_score = score
            is_checkworthy = cfs_score > 0.5
            logger.info(f"ClaimBuster: CFS={cfs_score:.3f}, cw={is_checkworthy}")
            result = {
                "cfs_score": round(cfs_score, 4),
                "nfs_score": round(nfs_score, 4),
                "is_checkworthy": is_checkworthy,
                "engine": "claimbuster_deberta",
            }
            cache.set_hf("claimbuster", text, result)
            return result
        except Exception as e:
            logger.error(f"ClaimBuster error: {e}")
            return None


class GoogleFactChecker:
    def __init__(self):
        self.api_key = _get_gfc_key()
        self.available = bool(self.api_key)
        if self.available:
            logger.info("✅ Google Fact Check API ready")

    async def check(self, text: str) -> dict | None:
        if not self.available:
            return None
        try:
            c = await _client()
            resp = await c.get(
                GOOGLE_FACTCHECK_URL,
                params={"query": text[:200].strip(), "key": self.api_key, "languageCode": "en"},
            )
            if resp.status_code != 200:
                logger.warning(f"Google FC: {resp.status_code}")
                return None
            data = resp.json()
            claims = data.get("claims", [])
            if not claims:
                return {"found": False, "claims": [], "engine": "google_factcheck"}
            processed = []
            for cl in claims[:3]:
                review = cl.get("claimReview", [{}])[0] if cl.get("claimReview") else {}
                processed.append({
                    "text": cl.get("text", ""),
                    "claimant": cl.get("claimant", "Unknown"),
                    "rating": review.get("textualRating", "Unknown"),
                    "publisher": review.get("publisher", {}).get("name", "Unknown"),
                    "url": review.get("url", ""),
                })
            ratings = " ".join(p["rating"].lower() for p in processed)
            false_kw = ["false", "pants on fire", "misleading", "incorrect", "fake"]
            true_kw = ["true", "correct", "accurate", "verified", "mostly true"]
            f_count = sum(1 for k in false_kw if k in ratings)
            t_count = sum(1 for k in true_kw if k in ratings)
            overall = "DEBUNKED" if f_count > t_count else "VERIFIED" if t_count > f_count else "MIXED"
            logger.info(f"Google FC: {len(processed)} claims, {overall}")
            return {
                "found": True, "overall_rating": overall,
                "num_claims": len(processed), "claims": processed,
                "engine": "google_factcheck",
            }
        except Exception as e:
            logger.error(f"Google FC error: {e}")
            return None


# Lazy singletons
_hf, _cb, _gfc = None, None, None

def get_hf_detector():
    global _hf
    if _hf is None: _hf = HuggingFaceDetector()
    return _hf

def get_claimbuster_hf():
    global _cb
    if _cb is None: _cb = ClaimBusterHF()
    return _cb

def get_google_factcheck():
    global _gfc
    if _gfc is None: _gfc = GoogleFactChecker()
    return _gfc


# ═══════════════════════════════════════════════════════
# v2 WRAPPER FUNCTIONS — new async-friendly signal APIs
# These wrap the existing classes above. Do NOT modify
# the existing HuggingFaceDetector, ClaimBusterHF, or
# GoogleFactChecker classes.
# ═══════════════════════════════════════════════════════

async def bert_signal_async(text: str) -> float:
    """
    v2 wrapper: Run BERT fake news detector and return a
    linguistic_credibility_signal (0-100).

    Mapping:
        REAL with 90% confidence → signal = 90
        FAKE with 80% confidence → signal = 20
    """
    hf = get_hf_detector()
    if not hf.available:
        return 50.0  # Neutral signal when unavailable

    try:
        import asyncio
        result = await asyncio.wait_for(hf.predict(text), timeout=5.0)
        if not result:
            return 50.0
        verdict = result.get("verdict", "REAL")
        confidence = result.get("confidence", 50) / 100.0  # 0-1

        if verdict == "REAL":
            # REAL: higher confidence → higher signal
            return round(confidence * 100, 1)
        else:
            # FAKE: higher confidence → lower signal
            return round((1.0 - confidence) * 100, 1)
    except Exception as e:
        logger.warning(f"BERT signal error: {e}")
        return 50.0


async def claimbuster_score_async(claim_text: str) -> float:
    """
    v2 wrapper: Run ClaimBuster on a single claim and return
    check-worthiness score (0-100).
    """
    cb = get_claimbuster_hf()
    if not cb.available:
        return 50.0  # Default mid-range

    try:
        import asyncio
        result = await asyncio.wait_for(cb.check(claim_text), timeout=5.0)
        if not result:
            return 50.0
        cfs_score = result.get("cfs_score", 0.5)
        return round(cfs_score * 100, 1)
    except Exception as e:
        logger.warning(f"ClaimBuster score error: {e}")
        return 50.0


# Sync-style wrappers (for use in non-async contexts)
def bert_signal(text: str) -> float:
    """Sync wrapper — prefer bert_signal_async in async routes."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        # If already in an async context, this won't work — use _async version
        return 50.0
    except RuntimeError:
        return asyncio.run(bert_signal_async(text))


def claimbuster_score(claim_text: str) -> float:
    """Sync wrapper — prefer claimbuster_score_async in async routes."""
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        return 50.0
    except RuntimeError:
        return asyncio.run(claimbuster_score_async(claim_text))

