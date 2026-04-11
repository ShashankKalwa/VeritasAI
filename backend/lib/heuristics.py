"""
VeritasAI Heuristic Fake News Detection Engine v2.0
Content-type pre-classification + 5-label taxonomy + multi-signal analysis.
Implements false-positive prevention rules from master system prompt.
"""
import re
from dataclasses import dataclass

@dataclass
class Signal:
    pattern: re.Pattern
    weight: int
    label: str

# ─── FAKE SIGNALS (Conspiracy / Pseudoscience / Manipulation) ───
FAKE_HIGH = [
    Signal(re.compile(r"they\s+don'?t\s+want\s+you\s+to\s+know", re.I), 15, "Conspiracy framing"),
    Signal(re.compile(r"mainstream\s+media\s+(hiding|silent|refusing|won'?t)", re.I), 14, "Media conspiracy claim"),
    Signal(re.compile(r"secret(ly)?\s+(government|cabal|plan|document)", re.I), 13, "Secret government action"),
    Signal(re.compile(r"cover[- ]?up", re.I), 12, "Cover-up allegation"),
    Signal(re.compile(r"miracle\s+cure", re.I), 15, "Miracle cure claim"),
    Signal(re.compile(r"suppress(ed|ion|ing)", re.I), 12, "Suppression narrative"),
    Signal(re.compile(r"whistleblower\s+reveals?", re.I), 11, "Anonymous whistleblower claim"),
    Signal(re.compile(r"shocking\s+(truth|new|revelation)", re.I), 11, "Shock value language"),
    Signal(re.compile(r"big\s+pharma", re.I), 12, "Big Pharma conspiracy"),
    Signal(re.compile(r"wake\s+up\s+sheeple", re.I), 15, "Conspiracy rhetoric"),
    Signal(re.compile(r"new\s+world\s+order", re.I), 14, "NWO conspiracy theory"),
    Signal(re.compile(r"chemtrail", re.I), 15, "Chemtrail conspiracy"),
    Signal(re.compile(r"5g\s+cause", re.I), 14, "5G conspiracy claim"),
    Signal(re.compile(r"flat\s+earth", re.I), 15, "Flat Earth claim"),
    Signal(re.compile(r"mind\s+control", re.I), 14, "Mind control conspiracy"),
    Signal(re.compile(r"population\s+control", re.I), 13, "Population control conspiracy"),
    Signal(re.compile(r"cures?\s+(all\s+)?cancer", re.I), 14, "Universal cancer cure claim"),
    Signal(re.compile(r"ancient\s+alien", re.I), 13, "Ancient aliens pseudoscience"),
    Signal(re.compile(r"perpetual\s+motion", re.I), 15, "Physics-violating claim"),
    Signal(re.compile(r"moon\s+(landing|hoax)\s+(was\s+)?faked?", re.I), 15, "Moon landing hoax"),
    Signal(re.compile(r"hollow\s+earth", re.I), 15, "Hollow Earth pseudoscience"),
    Signal(re.compile(r"portal\s+to\s+hell", re.I), 15, "Religious conspiracy"),
    Signal(re.compile(r"microchip\s+(implant|inject|track)", re.I), 13, "Microchip conspiracy"),
]

FAKE_MEDIUM = [
    Signal(re.compile(r"insider\s+reveals?", re.I), 8, "Insider claim"),
    Signal(re.compile(r"doctors?\s+don'?t\s+want", re.I), 9, "Anti-medical establishment"),
    Signal(re.compile(r"ancient\s+secret", re.I), 8, "Ancient secret claim"),
    Signal(re.compile(r"what\s+.+\s+doesn'?t?\s+want", re.I), 8, "Gatekeeping conspiracy"),
    Signal(re.compile(r"rigged", re.I), 7, "Rigging allegation"),
    Signal(re.compile(r"finally\s+(admit|reveal|confirm)", re.I), 7, "Delayed revelation claim"),
]

# Scientific contradiction patterns (strong FAKE indicators)
SCIENCE_CONTRADICTIONS = [
    Signal(re.compile(r"vaccine[s]?\s+(cause|alter|modify|change)\s+(DNA|autism|infertil)", re.I), 15, "Vaccine misinformation"),
    Signal(re.compile(r"(grow|use|power)\s+(plant|crop)s?\s+(using|with|from)\s+moonlight\s+alone", re.I), 14, "Violates photosynthesis science"),
    Signal(re.compile(r"learn\s+(language|skill)s?\s+while\s+sleep", re.I), 12, "Debunked sleep-learning claim"),
    Signal(re.compile(r"invisible\s+(phone|smartphone|screen)", re.I), 12, "Impossible technology claim"),
    Signal(re.compile(r"no\s+screen", re.I), 8, "Screenless smartphone claim"),
    Signal(re.compile(r"earth\s+is\s+flat", re.I), 15, "Flat Earth claim"),
    Signal(re.compile(r"climate\s+change\s+(hoax|fake|scam|myth)", re.I), 14, "Climate denial"),
]

FAKE_LINGUISTIC = [
    Signal(re.compile(r"!!!|!{2,}"), 6, "Excessive punctuation"),
    Signal(re.compile(r"\b(100|1000)\s*%"), 5, "Extreme percentage claim"),
    Signal(re.compile(r"\b(destroy|obliterate|annihilate)\b", re.I), 4, "Extreme action language"),
    Signal(re.compile(r"\bconspiracy\b", re.I), 5, "Conspiracy reference"),
    Signal(re.compile(r"\bhoax\b", re.I), 6, "Hoax allegation"),
]

# ─── REAL SIGNALS (Credibility markers) ───
REAL_SIGNALS = [
    # Source attribution
    Signal(re.compile(r"according\s+to\s+(reuters|ap|associated\s+press)", re.I), -12, "Major wire service attribution"),
    Signal(re.compile(r"per\s+the\s+(fda|cdc|who|nih|epa|fbi|noaa)", re.I), -10, "Government agency attribution"),
    Signal(re.compile(r"(reuters|bloomberg|ap\s+news|bbc|nyt|wsj|nature|lancet|science\.org)", re.I), -10, "Credible source reference"),
    Signal(re.compile(r"university\s+of|institute\s+of|department\s+of", re.I), -8, "Academic institution reference"),
    Signal(re.compile(r"(researcher|scientist|professor|dr\.)\s+(say|found|report|confirm|publish)", re.I), -9, "Expert attribution"),
    # Scientific method
    Signal(re.compile(r"study\s+published\s+in", re.I), -11, "Peer-reviewed study reference"),
    Signal(re.compile(r"clinical\s+trial", re.I), -10, "Clinical trial reference"),
    Signal(re.compile(r"peer[- ]reviewed", re.I), -12, "Peer review mention"),
    # Official language
    Signal(re.compile(r"said\s+in\s+a\s+statement", re.I), -9, "Official statement attribution"),
    Signal(re.compile(r"confirmed\s+by", re.I), -8, "Confirmation attribution"),
    Signal(re.compile(r"data\s+shows", re.I), -7, "Data-driven language"),
    Signal(re.compile(r"\d+\.\d+\s*percent", re.I), -7, "Precise statistical figure"),
    # Legislative / financial
    Signal(re.compile(r"\b(senate|congress|parliament|supreme\s+court)\b", re.I), -6, "Legislative institution reference"),
    Signal(re.compile(r"voted?\s+\d+-\d+", re.I), -8, "Specific vote count"),
    Signal(re.compile(r"\$\d+[\.\d]*\s*(billion|million|trillion)", re.I), -7, "Specific financial figure"),
    Signal(re.compile(r"regulation|legislation|amendment|bill", re.I), -5, "Legal/regulatory language"),
    Signal(re.compile(r"quarter|fiscal\s+year|q[1-4]", re.I), -6, "Financial reporting context"),
    Signal(re.compile(r"percent\s+of", re.I), -5, "Statistical language"),
    # Common legitimate news language
    Signal(re.compile(r"\b(announce|announced|announces|announcing)\b", re.I), -6, "Official announcement language"),
    Signal(re.compile(r"\b(upgrade|improve|develop|launch|introduce|plan|report)s?\b", re.I), -5, "Constructive action language"),
    Signal(re.compile(r"\b(government|ministry|official|authority|agency)\b", re.I), -5, "Government institution reference"),
    Signal(re.compile(r"\b(safety|infrastructure|system|platform|service)\b", re.I), -4, "Infrastructure/service language"),
    Signal(re.compile(r"\b(global|international|nationwide|regional|country|countries)\b", re.I), -3, "Geographic scope language"),
    Signal(re.compile(r"\b(startup|tech|technology|digital|AI|software)\b", re.I), -4, "Technology sector language"),
    Signal(re.compile(r"\b(record|temperature|climate|weather|heatwave|flood|storm)\b", re.I), -4, "Climate/weather reporting"),
    Signal(re.compile(r"\b(railway|road|highway|airport|transport)\b", re.I), -4, "Transport infrastructure language"),
    Signal(re.compile(r"\b(battery|energy|power|charge|renewable|solar)\b", re.I), -4, "Energy technology language"),
    Signal(re.compile(r"\b(outage|downtime|disruption|restore|recover)\b", re.I), -3, "Service disruption reporting"),
    Signal(re.compile(r"\b(social\s+media|platform|app|facebook|instagram|twitter|whatsapp)\b", re.I), -4, "Social media reference"),
    Signal(re.compile(r"\b(researcher|scientist)s?\s+(discover|develop|find|create|build|design)", re.I), -6, "Research-driven reporting"),
    Signal(re.compile(r"\b(billionaire|entrepreneur|founder|CEO)\s+(plan|build|invest|launch|fund)", re.I), -4, "Business figure reporting"),
]

# ─── CONTENT-TYPE DETECTION ───
CONTENT_TYPE_PATTERNS = {
    "SATIRE": [
        re.compile(r"\b(satire|parody|not\s+real|humor|joke)\b", re.I),
        re.compile(r"\b(baffled|rolls\s+eyes|confused\s+economists)\b", re.I),
    ],
    "OPINION": [
        re.compile(r"\b(opinion|editorial|commentary|op-?ed|i\s+think|i\s+believe)\b", re.I),
        re.compile(r"^(opinion|editorial)\s*:\s*", re.I),
    ],
    "BREAKING": [
        re.compile(r"^breaking\s*:", re.I),
        re.compile(r"\bbreaking\s+news\b", re.I),
    ],
}

CATEGORY_PATTERNS = {
    "Health": re.compile(r"\b(health|medical|vaccine|drug|disease|hospital|doctor|patient|FDA|WHO|pharma|cancer|virus|covid|treatment|clinical|symptom|cure)\b", re.I),
    "Politics": re.compile(r"\b(politic|senate|congress|president|election|vote|government|democrat|republican|parliament|legislation|supreme court|cabinet|campaign)\b", re.I),
    "Science": re.compile(r"\b(scien|NASA|space|telescope|physics|chemistry|biology|research|experiment|quantum|atom|molecule|planet|galaxy|fossil|DNA|gene)\b", re.I),
    "Business": re.compile(r"\b(business|market|stock|revenue|profit|company|corporate|GDP|economy|bank|finance|trade|billion|million|invest|earnings|startup)\b", re.I),
    "Environment": re.compile(r"\b(environment|climate|carbon|emission|pollution|deforest|renewable|solar|wind|ocean|arctic|ice|temperature|species|biodiversity|energy)\b", re.I),
    "Technology": re.compile(r"\b(tech|smartphone|app|AI|software|digital|battery|robot|internet|cyber|data|algorithm|platform|cloud)\b", re.I),
    "History": re.compile(r"\b(history|ancient|archaeological|civilization|dynasty|empire|medieval|century|artifact|fossil|excavat|pharaoh|viking|roman|war|battle)\b", re.I),
}


def detect_content_type(text: str) -> str:
    """Pre-classify content type: HARD_NEWS, SATIRE, OPINION, BREAKING."""
    for ctype, patterns in CONTENT_TYPE_PATTERNS.items():
        for p in patterns:
            if p.search(text):
                return ctype
    return "HARD_NEWS"


def detect_category(text: str) -> str:
    best_cat = "General"
    best_count = 0
    for cat, pattern in CATEGORY_PATTERNS.items():
        matches = pattern.findall(text)
        if len(matches) > best_count:
            best_count = len(matches)
            best_cat = cat
    return best_cat


def heuristic_analyze(text: str) -> dict:
    """
    Run full heuristic analysis implementing the VeritasAI master system prompt.
    Returns dict with 5-label verdict taxonomy and content-type classification.
    """
    text = text.strip()
    if len(text) < 10:
        return None

    content_type = detect_content_type(text)
    total_score = 0
    indicators = []
    fake_signal_count = 0  # Track distinct fake signal categories for convergence

    # Run all signal patterns
    all_signals = FAKE_HIGH + FAKE_MEDIUM + SCIENCE_CONTRADICTIONS + FAKE_LINGUISTIC + REAL_SIGNALS
    for signal in all_signals:
        if signal.pattern.search(text):
            total_score += signal.weight
            ind_type = "fake" if signal.weight > 0 else "real"
            indicators.append({"label": signal.label, "type": ind_type, "weight": abs(signal.weight)})
            if signal.weight > 0:
                fake_signal_count += 1

    # Caps ratio check (weak signal — max +3)
    caps = sum(1 for c in text if c.isupper())
    if len(text) > 20 and caps / len(text) > 0.4:
        total_score += 3
        indicators.append({"label": "Excessive capitalization", "type": "fake", "weight": 3})

    # Urgency language — WEAK signal per system prompt rule_FP_03
    # "BREAKING", "EXCLUSIVE" etc. are ALSO used in legitimate journalism
    if re.search(r"\b(act now|share before|share this before)\b", text, re.I):
        total_score += 5
        indicators.append({"label": "Viral urgency (share before deleted)", "type": "fake", "weight": 5})
        fake_signal_count += 1

    # Emotional manipulation
    if re.search(r"\b(furious|outraged|terrifying|horrifying|disgusting|unbelievable)\b", text, re.I):
        total_score += 3  # Reduced from 5 — can appear in legitimate news
        indicators.append({"label": "Emotional language", "type": "fake", "weight": 3})

    # ─── CONTENT-TYPE BIAS CORRECTIONS (per system prompt rule_FP_02) ───
    if content_type == "BREAKING":
        total_score -= 8  # Breaking news tolerance
    elif content_type == "OPINION":
        total_score -= 5  # Opinion tolerance

    # ─── VERDICT COMPUTATION (5-label taxonomy) ───
    max_score = 60.0
    normalized = max(min(total_score / max_score, 1.0), -1.0)

    # Multi-signal convergence gate (rule_FP_01):
    # FAKE requires multiple strong fake signals converging
    if normalized > 0.35 and fake_signal_count >= 2:
        verdict = "FAKE"
        confidence = min(round(55 + normalized * 45), 99)
    elif normalized > 0.15 and fake_signal_count >= 1:
        verdict = "MISLEADING"
        confidence = min(round(50 + normalized * 40), 85)
    elif normalized > 0.05:
        verdict = "PARTIALLY_TRUE"
        confidence = min(round(50 + normalized * 30), 75)
    elif normalized < -0.15:
        verdict = "REAL"
        confidence = min(round(60 + abs(normalized) * 40), 99)
    elif normalized < -0.05:
        verdict = "REAL"
        confidence = min(round(55 + abs(normalized) * 35), 85)
    else:
        # Neutral / ambiguous — benefit of the doubt (rule_FP_06)
        has_reporting = bool(re.search(
            r"\b(said|reported|according|announced|confirmed|update|"
            r"plan|launch|introduce|develop|improve|upgrade|affect|"
            r"face|break|discover|unveil|reveal|study|research)\b", text, re.I))
        if has_reporting:
            verdict = "REAL"
            confidence = 65
        else:
            verdict = "UNCERTAIN"
            confidence = 50

    category = detect_category(text)

    top_indicators = sorted(indicators, key=lambda x: x["weight"], reverse=True)[:5]
    indicator_labels = [i["label"] for i in top_indicators]

    if not indicator_labels:
        indicator_map = {
            "FAKE": ["No credible source attribution", "Multiple misinformation patterns detected"],
            "MISLEADING": ["Potentially misleading framing", "Requires fact-checking"],
            "PARTIALLY_TRUE": ["Mixed signals detected", "Some claims need verification"],
            "REAL": ["Standard reporting language", "Verifiable claims present", "Structured news format"],
            "UNCERTAIN": ["Insufficient signals for determination", "More context needed"],
        }
        indicator_labels = indicator_map.get(verdict, ["Analysis complete"])

    return {
        "verdict": verdict,
        "confidence": confidence,
        "indicators": indicator_labels,
        "category": category,
        "content_type": content_type,
        "heuristic_score": total_score,
        "fake_signal_count": fake_signal_count,
    }
