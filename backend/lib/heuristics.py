"""
VeritasAI Heuristic Fake News Detection Engine v4.0
Content-type 3-class classifier + structured indicator flags + 6-label taxonomy.

Verdict taxonomy: CREDIBLE → MOSTLY_TRUE → MIXED → MOSTLY_FALSE → FALSE → INSUFFICIENT_DATA
Content types:   NEWS_REPORT | OPINION_SATIRE | SOCIAL_POST
"""
import re
from dataclasses import dataclass, field

# ─────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────

@dataclass
class Signal:
    pattern: re.Pattern
    weight: int
    label: str
    indicator_id: str = ""  # Structured indicator ID for FIX-004


@dataclass
class IndicatorFlag:
    """Structured indicator returned to the frontend."""
    id: str
    label: str
    description: str
    source: str        # heuristic_nlp | google_fact_check | claimbuster_deberta
    weight: float      # 0-1 importance


# ─────────────────────────────────────────────────────────
# INDICATOR ID REGISTRY (FIX-004)
# ─────────────────────────────────────────────────────────

INDICATOR_IDS = {
    "EMO_MANIP": "Emotional Manipulation",
    "CLICKBAIT": "Clickbait Language",
    "UNVERIFIED_SRC": "Unverified Source",
    "SRC_CRED": "Source Credibility Issues",
    "CONSPIRACY": "Conspiracy Narrative",
    "FC_CONTRADICT": "Contradicted by Fact Checks",
    "UNSUPPORTED": "Unsupported Claim",
    "MISLEAD_HEAD": "Misleading Headline",
    "SENSATIONAL": "Sensationalist Language",
    "PSEUDO_SCI": "Pseudoscience Claim",
    "MISINFO_HEALTH": "Health Misinformation",
    "EXCESSIVE_CAPS": "Excessive Capitalization",
    "URGENCY": "Urgency/Fear Language",
    "ABSOLUTE_LANG": "Absolute Language",
    "COVERUP": "Cover-up Allegation",
    "SUPPRESSION": "Suppression Narrative",
    "EXPERT_ATTR": "Expert Attribution",
    "PEER_REVIEW": "Peer-Reviewed Reference",
    "OFFICIAL_SRC": "Official Source Attribution",
    "DATA_DRIVEN": "Data-Driven Language",
    "WIRE_SERVICE": "Wire Service Attribution",
    "ACADEMIC_REF": "Academic Institution Reference",
    "PRECISE_STAT": "Precise Statistical Figure",
    "STRUCTURED_REPORT": "Structured Reporting",
    "NO_RED_FLAGS": "No Red Flags Detected",
}

INDICATOR_DESCRIPTIONS = {
    "EMO_MANIP": "Excessive emotional language, fear/anger/outrage triggers detected",
    "CLICKBAIT": "Hyperbolic headline, ALL CAPS, excessive punctuation",
    "UNVERIFIED_SRC": "Anonymous source, 'sources say', no named attribution",
    "SRC_CRED": "Domain flagged as low credibility in source database",
    "CONSPIRACY": "Deep state, cover-up, 'they don't want you to know' patterns",
    "FC_CONTRADICT": "Google Fact Check API returned FALSE or MISLEADING verdict",
    "UNSUPPORTED": "ClaimBuster score > 0.7 but no fact-check verification found",
    "MISLEAD_HEAD": "Headline sentiment contradicts article body tone analysis",
    "SENSATIONAL": "Bombshell, shocking, jaw-dropping language patterns",
    "PSEUDO_SCI": "Pseudoscientific claims contradicting established science",
    "MISINFO_HEALTH": "Health misinformation — miracle cures, anti-vax, Big Pharma conspiracy",
    "EXCESSIVE_CAPS": "Over 40% uppercase characters — common in misinformation",
    "URGENCY": "Act now, share before deleted, emergency language",
    "ABSOLUTE_LANG": "Always, never, every, no one — absolute generalizations",
    "COVERUP": "Cover-up, suppression, hidden truth allegations",
    "SUPPRESSION": "Claims of deliberate suppression by media/government",
    "EXPERT_ATTR": "Named experts, researchers, or scientists cited",
    "PEER_REVIEW": "Peer-reviewed study, clinical trial, or journal referenced",
    "OFFICIAL_SRC": "Official statement, confirmed by, government agency cited",
    "DATA_DRIVEN": "Data-driven language with statistical evidence",
    "WIRE_SERVICE": "Reuters, AP, AFP, or major wire service attribution",
    "ACADEMIC_REF": "University, institute, or department referenced",
    "PRECISE_STAT": "Precise percentage, dollar figure, or vote count",
    "STRUCTURED_REPORT": "Standard reporting language with attribution",
    "NO_RED_FLAGS": "No specific misinformation patterns detected",
}


# ─────────────────────────────────────────────────────────
# FALSE SIGNALS (positive weight = increases false score)
# ─────────────────────────────────────────────────────────

FALSE_HIGH = [
    Signal(re.compile(r"they\s+don'?t\s+want\s+you\s+to\s+know", re.I), 15, "Conspiracy framing", "CONSPIRACY"),
    Signal(re.compile(r"mainstream\s+media\s+(hiding|silent|refusing|won'?t)", re.I), 14, "Media conspiracy claim", "CONSPIRACY"),
    Signal(re.compile(r"secret(ly)?\s+(government|cabal|plan|document)", re.I), 13, "Secret government action", "CONSPIRACY"),
    Signal(re.compile(r"cover[- ]?up", re.I), 12, "Cover-up allegation", "COVERUP"),
    Signal(re.compile(r"miracle\s+cure", re.I), 15, "Miracle cure claim", "MISINFO_HEALTH"),
    Signal(re.compile(r"suppress(ed|ion|ing)", re.I), 12, "Suppression narrative", "SUPPRESSION"),
    Signal(re.compile(r"whistleblower\s+reveals?", re.I), 11, "Anonymous whistleblower claim", "UNVERIFIED_SRC"),
    Signal(re.compile(r"shocking\s+(truth|new|revelation)", re.I), 11, "Shock value language", "SENSATIONAL"),
    Signal(re.compile(r"bombshell", re.I), 10, "Bombshell language", "SENSATIONAL"),
    Signal(re.compile(r"big\s+pharma", re.I), 12, "Big Pharma conspiracy", "MISINFO_HEALTH"),
    Signal(re.compile(r"wake\s+up\s+sheeple", re.I), 15, "Conspiracy rhetoric", "CONSPIRACY"),
    Signal(re.compile(r"new\s+world\s+order", re.I), 14, "NWO conspiracy theory", "CONSPIRACY"),
    Signal(re.compile(r"chemtrail", re.I), 15, "Chemtrail conspiracy", "PSEUDO_SCI"),
    Signal(re.compile(r"5g\s+cause", re.I), 14, "5G conspiracy claim", "PSEUDO_SCI"),
    Signal(re.compile(r"flat\s+earth", re.I), 15, "Flat Earth claim", "PSEUDO_SCI"),
    Signal(re.compile(r"mind\s+control", re.I), 14, "Mind control conspiracy", "CONSPIRACY"),
    Signal(re.compile(r"population\s+control", re.I), 13, "Population control conspiracy", "CONSPIRACY"),
    Signal(re.compile(r"cures?\s+(all\s+)?cancer", re.I), 14, "Universal cancer cure claim", "MISINFO_HEALTH"),
    Signal(re.compile(r"ancient\s+alien", re.I), 13, "Ancient aliens pseudoscience", "PSEUDO_SCI"),
    Signal(re.compile(r"perpetual\s+motion", re.I), 15, "Physics-violating claim", "PSEUDO_SCI"),
    Signal(re.compile(r"moon\s+(landing|hoax)\s+(was\s+)?faked?", re.I), 15, "Moon landing hoax", "PSEUDO_SCI"),
    Signal(re.compile(r"hollow\s+earth", re.I), 15, "Hollow Earth pseudoscience", "PSEUDO_SCI"),
    Signal(re.compile(r"portal\s+to\s+hell", re.I), 15, "Religious conspiracy", "CONSPIRACY"),
    Signal(re.compile(r"microchip\s+(implant|inject|track)", re.I), 13, "Microchip conspiracy", "CONSPIRACY"),
]

FALSE_MEDIUM = [
    Signal(re.compile(r"anonymous\s+source", re.I), 7, "Anonymous source", "UNVERIFIED_SRC"),
    Signal(re.compile(r"insider\s+reveals?", re.I), 8, "Insider claim", "UNVERIFIED_SRC"),
    Signal(re.compile(r"leaked\s+documents?", re.I), 7, "Leaked documents claim", "UNVERIFIED_SRC"),
    Signal(re.compile(r"doctors?\s+don'?t\s+want", re.I), 9, "Anti-medical establishment", "MISINFO_HEALTH"),
    Signal(re.compile(r"ancient\s+secret", re.I), 8, "Ancient secret claim", "PSEUDO_SCI"),
    Signal(re.compile(r"exclusive\s+source", re.I), 7, "Exclusive unverifiable source", "UNVERIFIED_SRC"),
    Signal(re.compile(r"exposed!?", re.I), 6, "Exposé framing", "SENSATIONAL"),
    Signal(re.compile(r"rigged", re.I), 7, "Rigging allegation", "CONSPIRACY"),
    Signal(re.compile(r"banned", re.I), 5, "Banned content claim", "SENSATIONAL"),
    Signal(re.compile(r"what\s+.+\s+doesn'?t?\s+want", re.I), 8, "Gatekeeping conspiracy", "CONSPIRACY"),
    Signal(re.compile(r"finally\s+(admit|reveal|confirm)", re.I), 7, "Delayed revelation claim", "SENSATIONAL"),
]

SCIENCE_CONTRADICTIONS = [
    Signal(re.compile(r"vaccine[s]?\s+(cause|alter|modify|change)\s+(DNA|autism|infertil)", re.I), 15, "Vaccine misinformation", "MISINFO_HEALTH"),
    Signal(re.compile(r"earth\s+is\s+flat", re.I), 15, "Flat Earth claim", "PSEUDO_SCI"),
    Signal(re.compile(r"climate\s+change\s+(hoax|fake|scam|myth)", re.I), 14, "Climate denial", "PSEUDO_SCI"),
    Signal(re.compile(r"no\s+screen", re.I), 8, "Screenless smartphone claim", "PSEUDO_SCI"),
]

FALSE_LINGUISTIC = [
    Signal(re.compile(r"!!!|!{2,}"), 6, "Excessive punctuation", "CLICKBAIT"),
    Signal(re.compile(r"\b(100|1000)\s*%"), 5, "Extreme percentage claim", "CLICKBAIT"),
    Signal(re.compile(r"\b(destroy|obliterate|annihilate)\b", re.I), 4, "Extreme action language", "SENSATIONAL"),
    Signal(re.compile(r"\bconspiracy\b", re.I), 5, "Conspiracy reference", "CONSPIRACY"),
    Signal(re.compile(r"\bhoax\b", re.I), 6, "Hoax allegation", "CONSPIRACY"),
]


# ─────────────────────────────────────────────────────────
# CREDIBLE SIGNALS (negative weight = increases credibility)
# ─────────────────────────────────────────────────────────

CREDIBLE_SIGNALS = [
    # Wire service / major source attribution
    Signal(re.compile(r"according\s+to\s+(reuters|ap|associated\s+press)", re.I), -12, "Major wire service attribution", "WIRE_SERVICE"),
    Signal(re.compile(r"per\s+the\s+(fda|cdc|who|nih|epa|fbi|noaa)", re.I), -10, "Government agency attribution", "OFFICIAL_SRC"),
    Signal(re.compile(r"(reuters|bloomberg|ap\s+news|bbc|nyt|wsj|nature|lancet|science\.org)", re.I), -10, "Credible source reference", "WIRE_SERVICE"),
    Signal(re.compile(r"university\s+of|institute\s+of|department\s+of", re.I), -8, "Academic institution reference", "ACADEMIC_REF"),
    Signal(re.compile(r"(researcher|scientist|professor|dr\.)\s+(say|found|report|confirm|publish)", re.I), -9, "Expert attribution", "EXPERT_ATTR"),
    # Scientific method
    Signal(re.compile(r"study\s+published\s+in", re.I), -11, "Peer-reviewed study reference", "PEER_REVIEW"),
    Signal(re.compile(r"clinical\s+trial", re.I), -10, "Clinical trial reference", "PEER_REVIEW"),
    Signal(re.compile(r"peer[- ]reviewed", re.I), -12, "Peer review mention", "PEER_REVIEW"),
    # Official language
    Signal(re.compile(r"said\s+in\s+a\s+statement", re.I), -9, "Official statement attribution", "OFFICIAL_SRC"),
    Signal(re.compile(r"confirmed\s+by", re.I), -8, "Confirmation attribution", "OFFICIAL_SRC"),
    Signal(re.compile(r"data\s+shows", re.I), -7, "Data-driven language", "DATA_DRIVEN"),
    Signal(re.compile(r"\d+\.\d+\s*percent", re.I), -7, "Precise statistical figure", "PRECISE_STAT"),
    # Legislative / financial
    Signal(re.compile(r"\b(senate|congress|parliament|supreme\s+court)\b", re.I), -6, "Legislative institution reference", "OFFICIAL_SRC"),
    Signal(re.compile(r"voted?\s+\d+-\d+", re.I), -8, "Specific vote count", "PRECISE_STAT"),
    Signal(re.compile(r"\$\d+[\.\d]*\s*(billion|million|trillion)", re.I), -7, "Specific financial figure", "PRECISE_STAT"),
    Signal(re.compile(r"regulation|legislation|amendment|bill", re.I), -5, "Legal/regulatory language", "OFFICIAL_SRC"),
    Signal(re.compile(r"quarter|fiscal\s+year|q[1-4]", re.I), -6, "Financial reporting context", "DATA_DRIVEN"),
    Signal(re.compile(r"percent\s+of", re.I), -5, "Statistical language", "DATA_DRIVEN"),
    # Common legitimate news language
    Signal(re.compile(r"\b(announce|announced|announces|announcing)\b", re.I), -6, "Official announcement language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(upgrade|improve|develop|launch|introduce|plan|report)s?\b", re.I), -5, "Constructive action language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(government|ministry|official|authority|agency)\b", re.I), -5, "Government institution reference", "OFFICIAL_SRC"),
    Signal(re.compile(r"\b(safety|infrastructure|system|platform|service)\b", re.I), -4, "Infrastructure/service language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(global|international|nationwide|regional)\b", re.I), -3, "Geographic scope language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(startup|tech|technology|digital|AI|software)\b", re.I), -4, "Technology sector language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(record|temperature|climate|weather|heatwave|flood|storm)\b", re.I), -4, "Climate/weather reporting", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(railway|road|highway|airport|transport)\b", re.I), -4, "Transport infrastructure language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(battery|energy|power|charge|renewable|solar)\b", re.I), -4, "Energy technology language", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(social\s+media|platform|app|facebook|instagram|twitter|whatsapp)\b", re.I), -4, "Social media reference", "STRUCTURED_REPORT"),
    Signal(re.compile(r"\b(researcher|scientist)s?\s+(discover|develop|find|create|build|design)", re.I), -6, "Research-driven reporting", "EXPERT_ATTR"),
    Signal(re.compile(r"\b(billionaire|entrepreneur|founder|CEO)\s+(plan|build|invest|launch|fund)", re.I), -4, "Business figure reporting", "STRUCTURED_REPORT"),
]


# ─────────────────────────────────────────────────────────
# CONTENT-TYPE DETECTION (FIX-006) — 3 types
# ─────────────────────────────────────────────────────────

def classify_content_type(text: str) -> dict:
    """
    3-type classifier: NEWS_REPORT | OPINION_SATIRE | SOCIAL_POST
    Default: NEWS_REPORT (most common input type).
    """
    # SOCIAL_POST: short content, hashtags, no structure
    has_hashtags = bool(re.search(r"#\w+", text))
    is_short = len(text.strip()) < 350
    social_domains = re.search(
        r"\b(twitter\.com|x\.com|reddit\.com|facebook\.com|instagram\.com|tiktok\.com)\b",
        text, re.I
    )
    if (is_short and has_hashtags) or social_domains:
        return {"id": "SOCIAL_POST", "label": "Social Media Post", "confidence": 0.85}

    # OPINION_SATIRE: first-person, subjective, satire keywords
    first_person = len(re.findall(r"\b(I\s+think|I\s+believe|in\s+my\s+opinion|my\s+view|we\s+should)\b", text, re.I))
    satire_kw = bool(re.search(r"\b(satire|parody|not\s+real\s+news|humor|joke|baffled|onion)\b", text, re.I))
    opinion_header = bool(re.search(r"^(opinion|editorial|commentary|op-?ed)\s*:", text, re.I))
    if satire_kw or opinion_header or first_person >= 2:
        return {"id": "OPINION_SATIRE", "label": "Opinion / Satire", "confidence": 0.80}

    # Default: NEWS_REPORT
    return {"id": "NEWS_REPORT", "label": "News Report", "confidence": 0.85}


# ─────────────────────────────────────────────────────────
# CATEGORY DETECTION
# ─────────────────────────────────────────────────────────

CATEGORY_PATTERNS = {
    "Health": re.compile(r"\b(health|medical|vaccine|drug|disease|hospital|doctor|patient|FDA|WHO|pharma|cancer|virus|covid|treatment|clinical|symptom|cure)\b", re.I),
    "Politics": re.compile(r"\b(politic|senate|congress|president|election|vote|government|democrat|republican|parliament|legislation|supreme court|cabinet|campaign)\b", re.I),
    "Science": re.compile(r"\b(scien|NASA|space|telescope|physics|chemistry|biology|research|experiment|quantum|atom|molecule|planet|galaxy|fossil|DNA|gene)\b", re.I),
    "Business": re.compile(r"\b(business|market|stock|revenue|profit|company|corporate|GDP|economy|bank|finance|trade|billion|million|invest|earnings|startup)\b", re.I),
    "Environment": re.compile(r"\b(environment|climate|carbon|emission|pollution|deforest|renewable|solar|wind|ocean|arctic|ice|temperature|species|biodiversity|energy)\b", re.I),
    "Technology": re.compile(r"\b(tech|smartphone|app|AI|software|digital|battery|robot|internet|cyber|data|algorithm|platform|cloud)\b", re.I),
    "History": re.compile(r"\b(history|ancient|archaeological|civilization|dynasty|empire|medieval|century|artifact|fossil|excavat|pharaoh|viking|roman|war|battle)\b", re.I),
}


def detect_category(text: str) -> str:
    best_cat, best_count = "General", 0
    for cat, pattern in CATEGORY_PATTERNS.items():
        matches = pattern.findall(text)
        if len(matches) > best_count:
            best_count = len(matches)
            best_cat = cat
    return best_cat


# ─────────────────────────────────────────────────────────
# MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────────────────────

def heuristic_analyze(text: str) -> dict | None:
    """
    Run full heuristic analysis. Returns structured result with:
    - verdict, confidence, score
    - content_type (3-type classifier)
    - structured indicators (IndicatorFlag objects as dicts)
    - category
    """
    text = text.strip()
    if len(text) < 10:
        return None

    content_type = classify_content_type(text)
    total_score = 0
    indicators_raw = []  # {id, label, description, source, weight, type}
    indicator_ids_seen = set()

    # ── Run all signal patterns ──
    all_signals = FALSE_HIGH + FALSE_MEDIUM + SCIENCE_CONTRADICTIONS + FALSE_LINGUISTIC + CREDIBLE_SIGNALS
    for signal in all_signals:
        if signal.pattern.search(text):
            total_score += signal.weight
            ind_type = "false" if signal.weight > 0 else "credible"
            ind_id = signal.indicator_id or "GENERAL"

            # Deduplicate by indicator ID — keep the strongest
            if ind_id not in indicator_ids_seen:
                indicator_ids_seen.add(ind_id)
                indicators_raw.append({
                    "id": ind_id,
                    "label": INDICATOR_IDS.get(ind_id, signal.label),
                    "description": INDICATOR_DESCRIPTIONS.get(ind_id, signal.label),
                    "source": "heuristic_nlp",
                    "weight": abs(signal.weight) / 15.0,  # Normalize to 0-1
                    "type": ind_type,
                })

    # ── Additional checks ──
    # Caps ratio
    caps = sum(1 for c in text if c.isupper())
    if len(text) > 20 and caps / len(text) > 0.4:
        total_score += 3
        if "EXCESSIVE_CAPS" not in indicator_ids_seen:
            indicator_ids_seen.add("EXCESSIVE_CAPS")
            indicators_raw.append({
                "id": "EXCESSIVE_CAPS", "label": "Excessive Capitalization",
                "description": INDICATOR_DESCRIPTIONS["EXCESSIVE_CAPS"],
                "source": "heuristic_nlp", "weight": 0.3, "type": "false",
            })

    # Urgency language
    if re.search(r"\b(act now|share before|share this before)\b", text, re.I):
        total_score += 5
        if "URGENCY" not in indicator_ids_seen:
            indicator_ids_seen.add("URGENCY")
            indicators_raw.append({
                "id": "URGENCY", "label": "Urgency/Fear Language",
                "description": INDICATOR_DESCRIPTIONS["URGENCY"],
                "source": "heuristic_nlp", "weight": 0.5, "type": "false",
            })

    # Emotional manipulation
    if re.search(r"\b(furious|outraged|terrifying|horrifying|disgusting|unbelievable)\b", text, re.I):
        total_score += 3
        if "EMO_MANIP" not in indicator_ids_seen:
            indicator_ids_seen.add("EMO_MANIP")
            indicators_raw.append({
                "id": "EMO_MANIP", "label": "Emotional Manipulation",
                "description": INDICATOR_DESCRIPTIONS["EMO_MANIP"],
                "source": "heuristic_nlp", "weight": 0.5, "type": "false",
            })

    # ── Content-type weight adjustment (FIX-006) ──
    opinion_weight_factor = 1.0
    if content_type["id"] == "OPINION_SATIRE":
        opinion_weight_factor = 0.60  # Reduce heuristic weight by 40%

    # ── Compute heuristic verdict ──
    adjusted_score = total_score * opinion_weight_factor
    max_score = 60.0
    normalized = max(min(adjusted_score / max_score, 1.0), -1.0)

    false_indicators = [i for i in indicators_raw if i["type"] == "false"]
    credible_indicators = [i for i in indicators_raw if i["type"] == "credible"]

    # Map normalized score to 0-1 scale for ensemble (0=false, 1=credible)
    # normalized is -1 (most credible) to +1 (most false)
    # heuristic_score_01: 0=false, 1=credible
    heuristic_score_01 = max(0.0, min(1.0, 0.5 - (normalized * 0.5)))

    # Simple heuristic verdict for display
    if normalized > 0.35 and len(false_indicators) >= 2:
        h_verdict = "FALSE"
        h_confidence = min(round(55 + normalized * 45), 99)
    elif normalized > 0.15:
        h_verdict = "MOSTLY_FALSE"
        h_confidence = min(round(50 + normalized * 40), 85)
    elif normalized > 0.05:
        h_verdict = "MIXED"
        h_confidence = min(round(50 + normalized * 30), 75)
    elif normalized < -0.15:
        h_verdict = "CREDIBLE"
        h_confidence = min(round(60 + abs(normalized) * 40), 99)
    elif normalized < -0.05:
        h_verdict = "MOSTLY_TRUE"
        h_confidence = min(round(55 + abs(normalized) * 35), 85)
    else:
        has_reporting = bool(re.search(
            r"\b(said|reported|according|announced|confirmed|update|"
            r"plan|launch|introduce|develop|improve|upgrade|affect|"
            r"face|break|discover|unveil|reveal|study|research)\b", text, re.I))
        if has_reporting:
            h_verdict = "MOSTLY_TRUE"
            h_confidence = 65
        else:
            h_verdict = "MIXED"
            h_confidence = 55

    category = detect_category(text)

    # ── Build structured indicators (FIX-004) ──
    # Sort all indicators by weight descending
    all_sorted = sorted(indicators_raw, key=lambda x: x["weight"], reverse=True)

    # Primary issue = strongest signal
    primary_issue = None
    secondary_issues = []

    if all_sorted:
        primary_issue = {
            "id": all_sorted[0]["id"],
            "label": all_sorted[0]["label"],
            "description": all_sorted[0]["description"],
        }
        secondary_issues = [
            {"id": ind["id"], "label": ind["label"]}
            for ind in all_sorted[1:3]  # Up to 2 secondary
        ]
    else:
        # No signals detected
        if h_verdict in ("CREDIBLE", "MOSTLY_TRUE"):
            primary_issue = {
                "id": "NO_RED_FLAGS",
                "label": "No Red Flags Detected",
                "description": "No specific misinformation patterns detected",
            }
        else:
            primary_issue = {
                "id": "UNVERIFIED_SRC",
                "label": "Unverified Source",
                "description": "No credible source attribution found",
            }

    # Legacy indicator labels for backward compat
    indicator_labels = [ind["label"] for ind in all_sorted[:5]]
    if not indicator_labels:
        indicator_labels = [primary_issue["label"]]

    return {
        "verdict": h_verdict,
        "confidence": h_confidence,
        "heuristic_score": round(adjusted_score, 2),
        "heuristic_score_01": round(heuristic_score_01, 4),  # 0-1 scale for ensemble
        "indicators": indicator_labels,
        "structured_indicators": {
            "primary_issue": primary_issue,
            "secondary_issues": secondary_issues,
        },
        "all_flags": all_sorted,
        "false_flag_count": len(false_indicators),
        "credible_flag_count": len(credible_indicators),
        "category": category,
        "content_type": content_type,
        "opinion_weight_factor": opinion_weight_factor,
    }
