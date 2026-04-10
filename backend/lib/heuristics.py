"""
VeritasAI Heuristic Fake News Detection Engine (Python)
60+ pattern rules for linguistic, rhetorical, and source analysis.
"""
import re
from dataclasses import dataclass

@dataclass
class Signal:
    pattern: re.Pattern
    weight: int
    label: str

FAKE_HIGH = [
    Signal(re.compile(r"suppress(ed|ion|ing)", re.I), 12, "Suppression narrative"),
    Signal(re.compile(r"whistleblower\s+reveals?", re.I), 11, "Anonymous whistleblower claim"),
    Signal(re.compile(r"they\s+don'?t\s+want\s+you\s+to\s+know", re.I), 15, "Conspiracy framing"),
    Signal(re.compile(r"mainstream\s+media\s+(hiding|silent|refusing|won'?t)", re.I), 14, "Media conspiracy claim"),
    Signal(re.compile(r"secret(ly)?\s+(government|cabal|plan|document)", re.I), 13, "Secret government action"),
    Signal(re.compile(r"cover[- ]?up", re.I), 12, "Cover-up allegation"),
    Signal(re.compile(r"miracle\s+cure", re.I), 15, "Miracle cure claim"),
    Signal(re.compile(r"bombshell", re.I), 10, "Sensationalist language"),
    Signal(re.compile(r"shocking\s+(truth|new|revelation)", re.I), 11, "Shock value language"),
    Signal(re.compile(r"big\s+pharma", re.I), 12, "Big Pharma conspiracy"),
    Signal(re.compile(r"wake\s+up\s+sheeple", re.I), 15, "Conspiracy rhetoric"),
    Signal(re.compile(r"new\s+world\s+order", re.I), 14, "NWO conspiracy theory"),
    Signal(re.compile(r"chemtrail", re.I), 15, "Chemtrail conspiracy"),
    Signal(re.compile(r"microchip", re.I), 13, "Microchip conspiracy"),
    Signal(re.compile(r"5g\s+cause", re.I), 14, "5G conspiracy claim"),
    Signal(re.compile(r"flat\s+earth", re.I), 15, "Flat Earth claim"),
    Signal(re.compile(r"mind\s+control", re.I), 14, "Mind control conspiracy"),
    Signal(re.compile(r"population\s+control", re.I), 13, "Population control conspiracy"),
    Signal(re.compile(r"cures?\s+(all\s+)?cancer", re.I), 14, "Universal cancer cure claim"),
    Signal(re.compile(r"ancient\s+alien", re.I), 13, "Ancient aliens pseudoscience"),
    Signal(re.compile(r"portal\s+to\s+hell", re.I), 15, "Religious conspiracy"),
    Signal(re.compile(r"perpetual\s+motion", re.I), 15, "Physics-violating claim"),
    Signal(re.compile(r"moon\s+(landing|hoax)\s+(was\s+)?faked?", re.I), 15, "Moon landing hoax"),
    Signal(re.compile(r"hollow\s+earth", re.I), 15, "Hollow Earth pseudoscience"),
]

FAKE_MEDIUM = [
    Signal(re.compile(r"anonymous\s+source", re.I), 7, "Anonymous source"),
    Signal(re.compile(r"insider\s+reveals?", re.I), 8, "Insider claim"),
    Signal(re.compile(r"leaked\s+documents?", re.I), 7, "Leaked documents claim"),
    Signal(re.compile(r"doctors?\s+don'?t\s+want", re.I), 9, "Anti-medical establishment"),
    Signal(re.compile(r"ancient\s+secret", re.I), 8, "Ancient secret claim"),
    Signal(re.compile(r"exclusive\s+source", re.I), 7, "Exclusive unverifiable source"),
    Signal(re.compile(r"exposed!?", re.I), 6, "Exposé framing"),
    Signal(re.compile(r"rigged", re.I), 7, "Rigging allegation"),
    Signal(re.compile(r"what\s+.+\s+doesn'?t?\s+want", re.I), 8, "Gatekeeping conspiracy"),
    Signal(re.compile(r"finally\s+(admit|reveal|confirm)", re.I), 7, "Delayed revelation claim"),
]

FAKE_LINGUISTIC = [
    Signal(re.compile(r"!!!|!{2,}"), 6, "Excessive punctuation"),
    Signal(re.compile(r"\b(100|1000)\s*%"), 5, "Extreme percentage claim"),
    Signal(re.compile(r"\b(every|all|entire|always|never|no one)\b", re.I), 3, "Absolute language"),
    Signal(re.compile(r"\b(destroy|obliterate|annihilate|devastating)\b", re.I), 4, "Extreme action language"),
    Signal(re.compile(r"(aliens?|extraterrestrial|ufo)\b", re.I), 8, "Extraterrestrial claim"),
    Signal(re.compile(r"\bconspiracy\b", re.I), 5, "Conspiracy reference"),
    Signal(re.compile(r"\bhoax\b", re.I), 6, "Hoax allegation"),
]

REAL_SIGNALS = [
    Signal(re.compile(r"according\s+to\s+(reuters|ap|associated\s+press)", re.I), -12, "Major wire service attribution"),
    Signal(re.compile(r"per\s+the\s+(fda|cdc|who|nih|epa|fbi|noaa)", re.I), -10, "Government agency attribution"),
    Signal(re.compile(r"study\s+published\s+in", re.I), -11, "Peer-reviewed study reference"),
    Signal(re.compile(r"clinical\s+trial", re.I), -10, "Clinical trial reference"),
    Signal(re.compile(r"peer[- ]reviewed", re.I), -12, "Peer review mention"),
    Signal(re.compile(r"said\s+in\s+a\s+statement", re.I), -9, "Official statement attribution"),
    Signal(re.compile(r"confirmed\s+by", re.I), -8, "Confirmation attribution"),
    Signal(re.compile(r"data\s+shows", re.I), -7, "Data-driven language"),
    Signal(re.compile(r"percent\s+of", re.I), -5, "Statistical language"),
    Signal(re.compile(r"\d+\.\d+\s*percent", re.I), -7, "Precise statistical figure"),
    Signal(re.compile(r"quarter|fiscal\s+year|q[1-4]", re.I), -6, "Financial reporting context"),
    Signal(re.compile(r"(reuters|bloomberg|ap\s+news|bbc|nyt|wsj|nature|lancet|science\.org)", re.I), -10, "Credible source reference"),
    Signal(re.compile(r"university\s+of|institute\s+of|department\s+of", re.I), -8, "Academic institution reference"),
    Signal(re.compile(r"(researcher|scientist|professor|dr\.)\s+(say|found|report|confirm|publish)", re.I), -9, "Expert attribution"),
    Signal(re.compile(r"\b(senate|congress|parliament|supreme\s+court)\b", re.I), -6, "Legislative institution reference"),
    Signal(re.compile(r"voted?\s+\d+-\d+", re.I), -8, "Specific vote count"),
    Signal(re.compile(r"\$\d+[\.\d]*\s*(billion|million|trillion)", re.I), -7, "Specific financial figure"),
    Signal(re.compile(r"regulation|legislation|amendment|bill", re.I), -5, "Legal/regulatory language"),
]

CATEGORY_PATTERNS = {
    "Health": re.compile(r"\b(health|medical|vaccine|drug|disease|hospital|doctor|patient|FDA|WHO|pharma|cancer|virus|covid|treatment|clinical|symptom|cure)\b", re.I),
    "Politics": re.compile(r"\b(politic|senate|congress|president|election|vote|government|democrat|republican|parliament|legislation|supreme court|cabinet|campaign)\b", re.I),
    "Science": re.compile(r"\b(scien|NASA|space|telescope|physics|chemistry|biology|research|experiment|quantum|atom|molecule|planet|galaxy|fossil|DNA|gene)\b", re.I),
    "Business": re.compile(r"\b(business|market|stock|revenue|profit|company|corporate|GDP|economy|bank|finance|trade|billion|million|invest|earnings|startup)\b", re.I),
    "Environment": re.compile(r"\b(environment|climate|carbon|emission|pollution|deforest|renewable|solar|wind|ocean|arctic|ice|temperature|species|biodiversity|energy)\b", re.I),
    "History": re.compile(r"\b(history|ancient|archaeological|civilization|dynasty|empire|medieval|century|artifact|fossil|excavat|pharaoh|viking|roman|war|battle)\b", re.I),
}


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
    """Run full heuristic analysis on text. Returns dict with score and indicators."""
    text = text.strip()
    if len(text) < 10:
        return None

    total_score = 0
    indicators = []

    all_signals = FAKE_HIGH + FAKE_MEDIUM + FAKE_LINGUISTIC + REAL_SIGNALS
    for signal in all_signals:
        if signal.pattern.search(text):
            total_score += signal.weight
            ind_type = "fake" if signal.weight > 0 else "real"
            indicators.append({"label": signal.label, "type": ind_type, "weight": abs(signal.weight)})

    # Caps ratio check
    caps = sum(1 for c in text if c.isupper())
    if len(text) > 20 and caps / len(text) > 0.3:
        total_score += 5
        indicators.append({"label": "Excessive capitalization", "type": "fake", "weight": 5})

    # Urgency language
    if re.search(r"\b(urgent|breaking|alert|warning|emergency|act now|share before)\b", text, re.I):
        total_score += 6
        indicators.append({"label": "Urgency/fear language", "type": "fake", "weight": 6})

    # Emotional manipulation
    if re.search(r"\b(furious|outraged|terrifying|horrifying|disgusting|unbelievable)\b", text, re.I):
        total_score += 5
        indicators.append({"label": "Emotional manipulation", "type": "fake", "weight": 5})

    # Normalize
    max_score = 60.0
    normalized = max(min(total_score / max_score, 1.0), -1.0)

    if normalized > 0.05:
        verdict = "FAKE"
        confidence = min(round(50 + normalized * 50), 99)
    elif normalized < -0.05:
        verdict = "REAL"
        confidence = min(round(50 + abs(normalized) * 50), 99)
    else:
        has_reporting = bool(re.search(r"\b(said|reported|according|announced|confirmed)\b", text, re.I))
        if has_reporting:
            verdict = "REAL"
            confidence = 58
        else:
            verdict = "FAKE"
            confidence = 57

    category = detect_category(text)

    top_indicators = sorted(indicators, key=lambda x: x["weight"], reverse=True)[:5]
    indicator_labels = [i["label"] for i in top_indicators]

    if not indicator_labels:
        if verdict == "FAKE":
            indicator_labels = ["No credible source attribution", "Lacks verifiable details", "Unstructured narrative"]
        else:
            indicator_labels = ["Standard reporting language", "Verifiable claims present", "Structured news format"]

    return {
        "verdict": verdict,
        "confidence": confidence,
        "indicators": indicator_labels,
        "category": category,
        "heuristic_score": total_score,
    }
