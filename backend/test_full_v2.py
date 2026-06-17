"""
VeritasAI V2 — Comprehensive Test Suite
Tests every module in the pipeline without external API keys.
"""
import asyncio, os, sys, json, traceback
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault("GOOGLE_AI_API_KEY", "test_dummy_key")
os.environ.setdefault("SEARCH_API_KEY", "test_dummy_key")

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []

def record(name, passed, detail=""):
    results.append((name, passed, detail))
    print(f"  {PASS if passed else FAIL}  {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("  VeritasAI V2 — Full Test Suite")
print("=" * 60)

# --- Test 1: Module imports ---
print("\n[1/8] Module imports...")
for mod in ["lib.file_parser","lib.input_handler","lib.claim_extractor","lib.ml_model",
            "lib.heuristics","lib.evidence_retriever","lib.source_credibility",
            "lib.evidence_reasoner","lib.ensemble_verdict_v2","lib.explainability_formatter",
            "lib.supabase_client","routes.analyze","routes.stats","routes.feed","routes.dataset","main"]:
    try:
        __import__(mod); record(f"import {mod}", True)
    except Exception as e:
        record(f"import {mod}", False, str(e))

# --- Test 2: file_parser ---
print("\n[2/8] File parser...")
from lib.file_parser import extract_text_from_txt, is_meaningful_content
txt = extract_text_from_txt(b"Hello World, this is a test article.")
record("extract_text_from_txt", txt == "Hello World, this is a test article.", f"{len(txt)} chars")
v, r = is_meaningful_content("This is valid text content with enough words to pass the checks easily.")
record("is_meaningful_content (valid)", v, r)
v2, r2 = is_meaningful_content("hi")
record("is_meaningful_content (invalid)", not v2, r2)

# --- Test 3: input_handler ---
print("\n[3/8] Input handler...")
from lib.input_handler import normalize_and_detect_type
t, ct = normalize_and_detect_type("text", "  Federal Reserve holds rates steady.  ", None)
record("normalize text", t.strip() != "" and ct == "news_report", f"type={ct}")
t2, ct2 = normalize_and_detect_type("text", "I think in my opinion this is fine, in my view", None)
record("detect opinion", ct2 == "opinion_satire", f"type={ct2}")
t3, ct3 = normalize_and_detect_type("text", "Any", "social_media_post")
record("explicit type", ct3 == "social_media_post", f"type={ct3}")

# --- Test 4: claim_extractor ---
print("\n[4/8] Claim extractor (stub)...")
from lib.claim_extractor import extract_claims
async def t4():
    claims = await extract_claims("NASA confirms water on Mars", "news_report")
    record("extract_claims", isinstance(claims, list) and len(claims) > 0, f"{len(claims)} claims")
    if claims: record("claim has claim_text", "claim_text" in claims[0])
asyncio.run(t4())

# --- Test 5: ML signals ---
print("\n[5/8] ML signals...")
from lib.ml_model import claimbuster_score, bert_signal
from lib.heuristics import manipulation_signal_async
async def t5():
    cb = await claimbuster_score("The earth is round")
    record("claimbuster_score", isinstance(cb, (int, float)), f"{cb}")
    b = await bert_signal("Breaking news: new planet")
    record("bert_signal", isinstance(b, (int, float)), f"{b}")
    m = await manipulation_signal_async("SHOCKING revelation!")
    record("manipulation_signal", isinstance(m, (int, float)), f"{m}")
asyncio.run(t5())

# --- Test 6: Evidence + credibility ---
print("\n[6/8] Evidence retrieval + credibility...")
from lib.evidence_retriever import retrieve_evidence
from lib.source_credibility import score_evidence
async def t6():
    items = await retrieve_evidence("Water on Mars")
    record("retrieve_evidence", isinstance(items, list), f"{len(items)} items")
    scored = score_evidence(items)
    record("score_evidence", isinstance(scored, list), f"{len(scored)} scored")
asyncio.run(t6())

# --- Test 7: Ensemble + explainability ---
print("\n[7/8] Ensemble verdict + explainability...")
from lib.ensemble_verdict_v2 import compute_claim_verdict, compute_overall_verdict
from lib.explainability_formatter import format_explainability
mc = {"claim_id":"t1","claim_text":"Water on Mars","source_span":"Water on Mars",
      "evidence":{"supporting":[{"source_name":"NASA","url":"https://nasa.gov","title":"Mars Water","credibility_score":90}],
                  "contradicting":[],"unclear":[],"reasoning":"NASA confirms."},
      "model_signals":{"bert_linguistic_signal":75.0,"heuristic_manipulation_signal":85.0}}
v, c = compute_claim_verdict(mc)
record("compute_claim_verdict", v in ["Credible","Likely True","Mixed / Misleading","Likely False","False","Insufficient Evidence"], f"{v} ({c}%)")
mc["verdict"], mc["confidence"] = v, c
ov, oc = compute_overall_verdict([mc])
record("compute_overall_verdict", ov in ["Credible","Likely True","Mixed / Misleading","Likely False","False","Opinion / Not Fact-Checkable","Insufficient Evidence"], f"{ov} ({oc}%)")
resp = format_explainability([mc], ov, oc, "news_report")
record("format_explainability", all(k in resp for k in ["overall_verdict","claims","explainability"]))

# --- Test 8: Full pipeline ---
print("\n[8/8] Full pipeline (process_analysis)...")
from routes.analyze import process_analysis
async def t8():
    try:
        r = await process_analysis("text", "A new study in The Lancet confirms eating 5 apples a day cures cancer 100% of the time.", None)
        record("process_analysis returns dict", isinstance(r, dict), str(list(r.keys())))
        record("has overall_verdict", "overall_verdict" in r, r.get("overall_verdict"))
        record("has claims", isinstance(r.get("claims"), list), f"{len(r.get('claims',[]))} claims")
        record("has explainability", "explainability" in r)
        print("\n  Full response:")
        print(json.dumps(r, indent=2))
    except Exception as e:
        record("process_analysis", False, str(e))
        traceback.print_exc()
asyncio.run(t8())

# --- Summary ---
print("\n" + "=" * 60)
p = sum(1 for _,ok,_ in results if ok)
f = sum(1 for _,ok,_ in results if not ok)
print(f"  RESULTS: {p} passed, {f} failed out of {len(results)} tests")
if f:
    print("\n  Failed:")
    for n,ok,d in results:
        if not ok: print(f"    ❌ {n}: {d}")
print("=" * 60)
sys.exit(0 if f == 0 else 1)
