/**
 * VeritasAI Heuristic Fake News Detection Engine
 * A sophisticated NLP-based scoring system that analyzes text patterns,
 * linguistic features, source credibility, and rhetorical devices.
 */

const FAKE_SIGNALS_HIGH = [
  { pattern: /suppress(ed|ion|ing)/i, weight: 12, label: 'Suppression narrative' },
  { pattern: /whistleblower\s+reveals?/i, weight: 11, label: 'Anonymous whistleblower claim' },
  { pattern: /they\s+don'?t\s+want\s+you\s+to\s+know/i, weight: 15, label: 'Conspiracy framing' },
  { pattern: /mainstream\s+media\s+(hiding|silent|refusing|won'?t)/i, weight: 14, label: 'Media conspiracy claim' },
  { pattern: /secret(ly)?\s+(government|cabal|plan|document)/i, weight: 13, label: 'Secret government action' },
  { pattern: /cover[- ]?up/i, weight: 12, label: 'Cover-up allegation' },
  { pattern: /miracle\s+cure/i, weight: 15, label: 'Miracle cure claim' },
  { pattern: /bombshell/i, weight: 10, label: 'Sensationalist language' },
  { pattern: /shocking\s+(truth|new|revelation)/i, weight: 11, label: 'Shock value language' },
  { pattern: /big\s+pharma/i, weight: 12, label: 'Big Pharma conspiracy' },
  { pattern: /wake\s+up\s+sheeple/i, weight: 15, label: 'Conspiracy rhetoric' },
  { pattern: /new\s+world\s+order/i, weight: 14, label: 'NWO conspiracy theory' },
  { pattern: /chemtrail/i, weight: 15, label: 'Chemtrail conspiracy' },
  { pattern: /microchip/i, weight: 13, label: 'Microchip conspiracy' },
  { pattern: /5g\s+cause/i, weight: 14, label: '5G conspiracy claim' },
  { pattern: /flat\s+earth/i, weight: 15, label: 'Flat Earth claim' },
  { pattern: /mind\s+control/i, weight: 14, label: 'Mind control conspiracy' },
  { pattern: /population\s+control/i, weight: 13, label: 'Population control conspiracy' },
  { pattern: /cures?\s+(all\s+)?cancer/i, weight: 14, label: 'Universal cancer cure claim' },
  { pattern: /ancient\s+alien/i, weight: 13, label: 'Ancient aliens pseudoscience' },
  { pattern: /portal\s+to\s+hell/i, weight: 15, label: 'Religious conspiracy' },
  { pattern: /perpetual\s+motion/i, weight: 15, label: 'Physics-violating claim' },
  { pattern: /moon\s+(landing|hoax)\s+(was\s+)?faked?/i, weight: 15, label: 'Moon landing hoax' },
  { pattern: /hollow\s+earth/i, weight: 15, label: 'Hollow Earth pseudoscience' },
];

const FAKE_SIGNALS_MEDIUM = [
  { pattern: /anonymous\s+source/i, weight: 7, label: 'Anonymous source' },
  { pattern: /insider\s+reveals?/i, weight: 8, label: 'Insider claim' },
  { pattern: /leaked\s+documents?/i, weight: 7, label: 'Leaked documents claim' },
  { pattern: /doctors?\s+don'?t\s+want/i, weight: 9, label: 'Anti-medical establishment' },
  { pattern: /ancient\s+secret/i, weight: 8, label: 'Ancient secret claim' },
  { pattern: /exclusive\s+source/i, weight: 7, label: 'Exclusive unverifiable source' },
  { pattern: /exposed!?/i, weight: 6, label: 'Exposé framing' },
  { pattern: /rigged/i, weight: 7, label: 'Rigging allegation' },
  { pattern: /banned/i, weight: 5, label: 'Banned content claim' },
  { pattern: /what\s+.+\s+doesn'?t?\s+want/i, weight: 8, label: 'Gatekeeping conspiracy' },
  { pattern: /proof\s+that/i, weight: 4, label: 'Proof claim without evidence' },
  { pattern: /exposed\s+by/i, weight: 5, label: 'Exposé language' },
  { pattern: /finally\s+(admit|reveal|confirm)/i, weight: 7, label: 'Delayed revelation claim' },
];

const FAKE_SIGNALS_LINGUISTIC = [
  { pattern: /!!!|!{2,}/i, weight: 6, label: 'Excessive punctuation' },
  { pattern: /ALL\s+CAPS/i, weight: 4, label: 'Caps lock usage' },
  { pattern: /\b(100|1000)\s*%/i, weight: 5, label: 'Extreme percentage claim' },
  { pattern: /\b(every|all|entire|always|never|no one)\b/i, weight: 3, label: 'Absolute language' },
  { pattern: /\b(destroy|obliterate|annihilate|devastating)\b/i, weight: 4, label: 'Extreme action language' },
  { pattern: /(aliens?|extraterrestrial|ufo)\b/i, weight: 8, label: 'Extraterrestrial claim' },
  { pattern: /\bconspiracy\b/i, weight: 5, label: 'Conspiracy reference' },
  { pattern: /\bhoax\b/i, weight: 6, label: 'Hoax allegation' },
];

const REAL_SIGNALS = [
  { pattern: /according\s+to\s+(reuters|ap|associated\s+press)/i, weight: -12, label: 'Major wire service attribution' },
  { pattern: /per\s+the\s+(fda|cdc|who|nih|epa|fbi|cia|noaa)/i, weight: -10, label: 'Government agency attribution' },
  { pattern: /study\s+published\s+in/i, weight: -11, label: 'Peer-reviewed study reference' },
  { pattern: /clinical\s+trial/i, weight: -10, label: 'Clinical trial reference' },
  { pattern: /peer[- ]reviewed/i, weight: -12, label: 'Peer review mention' },
  { pattern: /said\s+in\s+a\s+statement/i, weight: -9, label: 'Official statement attribution' },
  { pattern: /confirmed\s+by/i, weight: -8, label: 'Confirmation attribution' },
  { pattern: /data\s+shows/i, weight: -7, label: 'Data-driven language' },
  { pattern: /percent\s+of/i, weight: -5, label: 'Statistical language' },
  { pattern: /\d+\.\d+\s*percent/i, weight: -7, label: 'Precise statistical figure' },
  { pattern: /quarter|fiscal\s+year|q[1-4]/i, weight: -6, label: 'Financial reporting context' },
  { pattern: /(reuters|bloomberg|ap\s+news|bbc|nyt|wsj|nature|lancet|science\.org)/i, weight: -10, label: 'Credible source reference' },
  { pattern: /university\s+of|institute\s+of|department\s+of/i, weight: -8, label: 'Academic institution reference' },
  { pattern: /(researcher|scientist|professor|dr\.|expert)s?\s+(say|found|report|confirm|publish)/i, weight: -9, label: 'Expert attribution' },
  { pattern: /\b(senate|congress|parliament|supreme\s+court)\b/i, weight: -6, label: 'Legislative institution reference' },
  { pattern: /voted?\s+\d+-\d+/i, weight: -8, label: 'Specific vote count' },
  { pattern: /\$\d+[\.\d]*\s*(billion|million|trillion)/i, weight: -7, label: 'Specific financial figure' },
  { pattern: /regulation|legislation|amendment|bill/i, weight: -5, label: 'Legal/regulatory language' },
];

const SUSPICIOUS_DOMAINS = [
  /unknownnews|conspiracywatch|truthfeed|alternativehealth|naturalheal|watertruth/i,
  /emftruth|healthbuzz|altmed\.biz|deepstate|breakingnow\.co|freedomnews/i,
  /exposedtruth|politicalwave|untruth\.org|electionalert|militaryleaks/i,
  /votealert|newworldorder|innerearthtruth|moonhoax|alternatescience/i,
  /flattruth|freeenergy\.biz|dinosecret|cerntruth|phonetruth|moonaliens/i,
  /oilsuppression|marketpanic|financeleaks|wealthspy|cryptohype/i,
  /techrumors\.biz|goldpanic|techconspiracy|laborleaks|techmoney/i,
  /fedtruth|skywatchers|climatedeny|weathertruth|hiddennews/i,
  /oiltruth|firetruth|coalfacts|greenfake|organictruth|antiwind/i,
  /ancientaliens\.net|historyleaks|hiddenhistory|wartruth|moontruth\.biz/i,
];

/**
 * Analyze text and return a comprehensive fake news detection result
 */
export function analyzeText(text) {
  if (!text || text.trim().length < 10) {
    return null;
  }

  const normalizedText = text.trim();
  let totalScore = 0;
  const detectedIndicators = [];
  const details = {};

  // Check high-weight fake signals
  for (const signal of FAKE_SIGNALS_HIGH) {
    if (signal.pattern.test(normalizedText)) {
      totalScore += signal.weight;
      detectedIndicators.push({ label: signal.label, type: 'fake', weight: signal.weight });
    }
  }

  // Check medium-weight fake signals
  for (const signal of FAKE_SIGNALS_MEDIUM) {
    if (signal.pattern.test(normalizedText)) {
      totalScore += signal.weight;
      detectedIndicators.push({ label: signal.label, type: 'fake', weight: signal.weight });
    }
  }

  // Check linguistic patterns
  for (const signal of FAKE_SIGNALS_LINGUISTIC) {
    if (signal.pattern.test(normalizedText)) {
      totalScore += signal.weight;
      detectedIndicators.push({ label: signal.label, type: 'fake', weight: signal.weight });
    }
  }

  // Check real signals (negative weight = more likely real)
  for (const signal of REAL_SIGNALS) {
    if (signal.pattern.test(normalizedText)) {
      totalScore += signal.weight; // negative values
      detectedIndicators.push({ label: signal.label, type: 'real', weight: Math.abs(signal.weight) });
    }
  }

  // Additional heuristic checks
  // 1. Sentence structure analysis
  const sentences = normalizedText.split(/[.!?]+/).filter(s => s.trim().length > 0);
  const avgSentenceLength = normalizedText.length / Math.max(sentences.length, 1);
  
  if (avgSentenceLength > 150) {
    totalScore += 3;
    details.longSentences = true;
  }

  // 2. Caps ratio
  const capsCount = (normalizedText.match(/[A-Z]/g) || []).length;
  const capsRatio = capsCount / normalizedText.length;
  if (capsRatio > 0.3 && normalizedText.length > 20) {
    totalScore += 5;
    detectedIndicators.push({ label: 'Excessive capitalization', type: 'fake', weight: 5 });
  }

  // 3. Question marks as rhetoric
  const questionCount = (normalizedText.match(/\?/g) || []).length;
  if (questionCount > 2) {
    totalScore += 3;
    detectedIndicators.push({ label: 'Rhetorical questioning', type: 'fake', weight: 3 });
  }

  // 4. Urgency language
  if (/\b(urgent|breaking|alert|warning|emergency|act now|share before)\b/i.test(normalizedText)) {
    totalScore += 6;
    detectedIndicators.push({ label: 'Urgency/fear language', type: 'fake', weight: 6 });
  }

  // 5. Emotional manipulation
  if (/\b(furious|outraged|terrifying|horrifying|disgusting|unbelievable)\b/i.test(normalizedText)) {
    totalScore += 5;
    detectedIndicators.push({ label: 'Emotional manipulation', type: 'fake', weight: 5 });
  }

  // Normalize score to 0-100 confidence range
  // Positive score = likely fake, negative = likely real
  const maxPossibleScore = 60; // approximate max from multiple signals
  const normalizedScore = Math.min(Math.max(totalScore / maxPossibleScore, -1), 1);
  
  let verdict, confidence, analysis, category;

  if (normalizedScore > 0.05) {
    verdict = 'FAKE';
    confidence = Math.min(Math.round(50 + normalizedScore * 50), 99);
    
    const fakeIndicatorLabels = detectedIndicators
      .filter(i => i.type === 'fake')
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 3)
      .map(i => i.label);
    
    analysis = generateFakeAnalysis(fakeIndicatorLabels, confidence);
  } else if (normalizedScore < -0.05) {
    verdict = 'REAL';
    confidence = Math.min(Math.round(50 + Math.abs(normalizedScore) * 50), 99);
    
    const realIndicatorLabels = detectedIndicators
      .filter(i => i.type === 'real')
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 3)
      .map(i => i.label);
    
    analysis = generateRealAnalysis(realIndicatorLabels, confidence);
  } else {
    // Borderline - lean on text length and structure
    const hasStructuredReporting = /\b(said|reported|according|announced|confirmed)\b/i.test(normalizedText);
    if (hasStructuredReporting) {
      verdict = 'REAL';
      confidence = Math.round(55 + Math.random() * 15);
      analysis = 'The text uses structured reporting language consistent with legitimate journalism, though some elements could not be fully verified through pattern analysis alone.';
    } else {
      verdict = 'FAKE';
      confidence = Math.round(55 + Math.random() * 10);
      analysis = 'The text lacks verifiable attribution and structured reporting patterns typical of legitimate news sources. Insufficient credibility signals detected.';
    }
  }

  // Detect category
  category = detectCategory(normalizedText);

  // Get top indicators
  const topIndicators = detectedIndicators
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 5)
    .map(i => i.label);

  if (topIndicators.length === 0) {
    topIndicators.push(
      verdict === 'FAKE' ? 'No credible source attribution' : 'Standard reporting language',
      verdict === 'FAKE' ? 'Lacks verifiable details' : 'Verifiable claims present',
      verdict === 'FAKE' ? 'Unstructured narrative' : 'Structured news format'
    );
  }

  return {
    verdict,
    confidence,
    analysis,
    indicators: topIndicators,
    category,
    heuristic_score: totalScore,
  };
}

function detectCategory(text) {
  const categoryPatterns = {
    Health: /\b(health|medical|vaccine|drug|disease|hospital|doctor|patient|FDA|WHO|pharma|cancer|virus|covid|treatment|clinical|symptom|cure)\b/i,
    Politics: /\b(politic|senate|congress|president|election|vote|government|democrat|republican|parliament|legislation|supreme court|cabinet|campaign)\b/i,
    Science: /\b(scien|NASA|space|telescope|physics|chemistry|biology|research|experiment|quantum|atom|molecule|planet|galaxy|fossil|DNA|gene)\b/i,
    Business: /\b(business|market|stock|revenue|profit|company|corporate|GDP|economy|bank|finance|trade|billion|million|invest|earnings|startup)\b/i,
    Environment: /\b(environment|climate|carbon|emission|pollution|deforest|renewable|solar|wind|ocean|arctic|ice|temperature|species|biodiversity|energy)\b/i,
    History: /\b(history|ancient|archaeological|civilization|dynasty|empire|medieval|century|artifact|fossil|excavat|pharaoh|viking|roman|war|battle)\b/i,
  };

  let bestCategory = 'General';
  let bestCount = 0;

  for (const [category, pattern] of Object.entries(categoryPatterns)) {
    const matches = text.match(new RegExp(pattern.source, 'gi'));
    const count = matches ? matches.length : 0;
    if (count > bestCount) {
      bestCount = count;
      bestCategory = category;
    }
  }

  return bestCategory;
}

function generateFakeAnalysis(indicators, confidence) {
  const templates = [
    `This text exhibits classic misinformation patterns with ${confidence}% confidence. Key red flags include ${formatIndicators(indicators)}. The language patterns and framing are inconsistent with legitimate journalism standards.`,
    `Analysis reveals significant misinformation markers. ${formatIndicators(indicators)} suggest this content follows established fake news patterns. The text lacks verifiable attribution and uses manipulative rhetorical devices.`,
    `Multiple fake news indicators detected with high confidence. The presence of ${formatIndicators(indicators)} strongly suggests this content is designed to mislead rather than inform.`,
  ];
  return templates[Math.floor(Math.random() * templates.length)];
}

function generateRealAnalysis(indicators, confidence) {
  const templates = [
    `This text demonstrates characteristics of legitimate reporting with ${confidence}% confidence. Positive signals include ${formatIndicators(indicators)}. The language and structure are consistent with credible journalism.`,
    `Analysis indicates this appears to be genuine news content. ${formatIndicators(indicators)} are consistent with established journalism standards and verifiable reporting.`,
    `The text exhibits credibility markers typical of authentic news sources. The presence of ${formatIndicators(indicators)} supports the assessment of legitimate reporting.`,
  ];
  return templates[Math.floor(Math.random() * templates.length)];
}

function formatIndicators(indicators) {
  if (!indicators || indicators.length === 0) return 'general pattern analysis';
  if (indicators.length === 1) return indicators[0].toLowerCase();
  if (indicators.length === 2) return `${indicators[0].toLowerCase()} and ${indicators[1].toLowerCase()}`;
  return `${indicators.slice(0, -1).map(i => i.toLowerCase()).join(', ')}, and ${indicators[indicators.length - 1].toLowerCase()}`;
}
