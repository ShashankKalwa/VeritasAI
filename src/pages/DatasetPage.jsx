export default function DatasetPage() {
  const engines = [
    {
      id: 1,
      name: 'Heuristic NLP Engine',
      icon: '🔍',
      type: 'Rule-Based',
      status: 'Always Active',
      description: 'Custom pattern-matching engine with 60+ regex rules analyzing linguistic signals, rhetorical devices, source credibility, emotional manipulation, and conspiracy framing patterns. In v2, provides a manipulation_signal (0-100) where 100 = no manipulation detected.',
      specs: [
        { label: 'Rules', value: '60+' },
        { label: 'Categories', value: '4 pattern groups' },
        { label: 'Latency', value: '<5ms' },
        { label: 'v2 Weight', value: '20%' },
      ],
      patterns: ['Manipulation detection', 'Conspiracy indicators', 'Source attribution', 'Emotional manipulation', 'Sensationalist language', 'Credibility markers'],
      color: '#3b82f6',
    },
    {
      id: 2,
      name: 'HuggingFace BERT Detector',
      icon: '🤗',
      type: 'Transformer (Linguistic Signal)',
      status: 'Active',
      description: 'Pre-trained BERT-based model fine-tuned on fake news datasets. In v2, repurposed as a linguistic credibility signal (0-100) measuring writing style consistency with credible reporting, not used as a direct truth verdict.',
      specs: [
        { label: 'Model', value: 'jy46604790/Fake-News-Bert-Detect' },
        { label: 'Architecture', value: 'BERT Base' },
        { label: 'v2 Role', value: 'Linguistic signal' },
        { label: 'v2 Weight', value: '15%' },
      ],
      patterns: ['Deep semantic analysis', 'Writing style assessment', 'Contextual embeddings', 'Credibility pattern recognition'],
      color: '#f59e0b',
    },
    {
      id: 3,
      name: 'ClaimBuster DeBERTaV2',
      icon: '🔎',
      type: 'Check-Worthiness Gate',
      status: 'Active',
      description: 'DeBERTa-V2 transformer that scores claims for check-worthiness (0-100). In v2, acts as a GATE: claims scoring below 40% skip evidence retrieval and are labeled "Opinion / Not Fact-Checkable". Score is informational only — zero weight in the final verdict.',
      specs: [
        { label: 'Model', value: 'whispAI/ClaimBuster-DeBERTaV2' },
        { label: 'Gate Threshold', value: '40%' },
        { label: 'v2 Role', value: 'Check-worthiness gate' },
        { label: 'v2 Weight', value: '0% (gate only)' },
      ],
      patterns: ['Check-worthy Factual Statements (CFS)', 'Opinion vs fact separation', 'Claim detection scoring', 'Pipeline efficiency gate'],
      color: '#8b5cf6',
    },
    {
      id: 4,
      name: 'Google Fact Check Tools API',
      icon: '✅',
      type: 'Evidence Source',
      status: 'Active',
      description: 'Cross-references claims against a global database of verified fact-checks from PolitiFact, Snopes, FactCheck.org and more. In v2, treated as high-credibility evidence (85-95 score) fed into the evidence reasoning pipeline.',
      specs: [
        { label: 'Provider', value: 'Google Cloud' },
        { label: 'Credibility', value: '85-95 (fact-checkers)' },
        { label: 'v2 Role', value: 'Evidence source' },
        { label: 'v2 Weight', value: '15%' },
      ],
      patterns: ['PolitiFact ratings', 'Snopes verification', 'AFP fact-checks', 'International fact-checker network'],
      color: '#22c55e',
    },
    {
      id: 5,
      name: 'Gemini LLM (Claim Extraction + Reasoning)',
      icon: '🧠',
      type: 'LLM (New in v2)',
      status: 'Active',
      description: 'Google Gemini powers two critical pipeline steps: (1) extracting atomic, checkable claims from article text, and (2) reasoning over retrieved evidence to classify each piece as supporting, contradicting, or unclear relative to each claim.',
      specs: [
        { label: 'Extraction', value: 'gemini-2.5-flash' },
        { label: 'Reasoning', value: 'gemini-2.5-flash' },
        { label: 'Max Claims', value: '5 per article' },
        { label: 'v2 Role', value: 'Claim extraction + reasoning' },
      ],
      patterns: ['Atomic claim extraction', 'Evidence classification', 'Multi-source reasoning', 'Credibility-weighted analysis'],
      color: '#ec4899',
    },
    {
      id: 6,
      name: 'Tavily Search (Evidence Retrieval)',
      icon: '🌐',
      type: 'Search API (New in v2)',
      status: 'Active',
      description: 'Retrieves real-time evidence from the web for each check-worthy claim. Results are scored by source credibility using a curated database of 50+ domain scores. Prioritizes high-credibility sources while not excluding others.',
      specs: [
        { label: 'Provider', value: 'Tavily' },
        { label: 'Max Evidence', value: '6 per claim' },
        { label: 'Credibility DB', value: '50+ domains scored' },
        { label: 'v2 Role', value: 'Evidence retrieval + scoring' },
      ],
      patterns: ['Real-time web search', 'Source credibility scoring', 'Evidence deduplication', 'Date-sorted evidence ranking'],
      color: '#06b6d4',
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Verification Pipeline</h1>
        <p className="page-subtitle">
          VeritasAI v2 uses a 12-step retrieval-augmented pipeline for claim-level verification
        </p>
      </div>

      {/* Pipeline Overview */}
      <div className="dataset-stats-bar">
        <span className="ds-stat"><strong>6</strong> Pipeline Engines</span>
        <span className="ds-stat"><strong>12</strong> Pipeline Steps</span>
        <span className="ds-stat"><strong>50+</strong> Credibility Rules</span>
        <span className="ds-stat"><strong>Evidence</strong> Weighted Scoring</span>
      </div>

      {/* Engine Cards */}
      <div className="engines-grid">
        {engines.map(engine => (
          <div key={engine.id} className="engine-card" style={{ borderTopColor: engine.color }}>
            <div className="engine-card-header">
              <span className="engine-card-icon">{engine.icon}</span>
              <div>
                <h3 className="engine-card-name">{engine.name}</h3>
                <div className="engine-card-meta">
                  <span className="engine-type-badge">{engine.type}</span>
                  <span className="engine-status-badge">{engine.status}</span>
                </div>
              </div>
            </div>

            <p className="engine-card-desc">{engine.description}</p>

            <div className="engine-specs">
              <h4>Specifications</h4>
              <div className="specs-grid">
                {engine.specs.map((spec, i) => (
                  <div key={i} className="spec-item">
                    <span className="spec-label">{spec.label}</span>
                    <span className="spec-value">{spec.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="engine-capabilities">
              <h4>Capabilities</h4>
              <div className="indicator-pills">
                {engine.patterns.map((p, i) => (
                  <span key={i} className="indicator-pill indicator-real" style={{
                    borderColor: `${engine.color}40`,
                    color: engine.color,
                    background: `${engine.color}12`,
                  }}>{p}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Ensemble Explanation */}
      <div className="engine-card" style={{ borderTopColor: '#ef4444', marginTop: '1.5rem' }}>
        <div className="engine-card-header">
          <span className="engine-card-icon">⚡</span>
          <div>
            <h3 className="engine-card-name">Ensemble Verdict v2</h3>
            <div className="engine-card-meta">
              <span className="engine-type-badge">Credibility-Weighted</span>
              <span className="engine-status-badge">Core System</span>
            </div>
          </div>
        </div>
        <p className="engine-card-desc">
          Per-claim verdicts are computed using credibility-weighted evidence scoring. 
          5 low-credibility blogs (score 20) do NOT outvote 1 Reuters article (score 95).
          The overall article verdict uses a worst-case dominant rule: if any claim is "False" 
          with high confidence, the article verdict is "False".
        </p>
        <div className="engine-specs">
          <h4>v2 Weight Distribution</h4>
          <div className="specs-grid">
            <div className="spec-item"><span className="spec-label">Evidence (credibility-weighted)</span><span className="spec-value">50%</span></div>
            <div className="spec-item"><span className="spec-label">Heuristic NLP</span><span className="spec-value">20%</span></div>
            <div className="spec-item"><span className="spec-label">BERT Linguistic</span><span className="spec-value">15%</span></div>
            <div className="spec-item"><span className="spec-label">Google Fact Check</span><span className="spec-value">15%</span></div>
            <div className="spec-item"><span className="spec-label">ClaimBuster</span><span className="spec-value">0% (gate only)</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
