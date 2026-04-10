export default function DatasetPage() {
  const engines = [
    {
      id: 1,
      name: 'Heuristic NLP Engine',
      icon: '🔍',
      type: 'Rule-Based',
      status: 'Always Active',
      description: 'Custom pattern-matching engine with 60+ regex rules analyzing linguistic signals, rhetorical devices, source credibility, emotional manipulation, and conspiracy framing patterns.',
      specs: [
        { label: 'Rules', value: '60+' },
        { label: 'Categories', value: '4 pattern groups' },
        { label: 'Latency', value: '<5ms' },
        { label: 'Weight', value: '30%' },
      ],
      patterns: ['Sensationalist language', 'Conspiracy indicators', 'Miracle cure claims', 'Suppression narratives', 'Anonymous sourcing', 'Emotional manipulation'],
      color: '#3b82f6',
    },
    {
      id: 2,
      name: 'HuggingFace BERT Fake News Detector',
      icon: '🤗',
      type: 'Transformer (Pre-trained)',
      status: 'Active',
      description: 'Pre-trained BERT-based deep learning model fine-tuned on large-scale fake news datasets. Uses contextual embeddings to understand semantic meaning and detect misinformation patterns.',
      specs: [
        { label: 'Model', value: 'jy46604790/Fake-News-Bert-Detect' },
        { label: 'Architecture', value: 'BERT Base' },
        { label: 'API', value: 'HuggingFace Inference' },
        { label: 'Weight', value: '35%' },
      ],
      patterns: ['Deep semantic analysis', 'Contextual embeddings', 'Transfer learning from large corpus', 'Binary classification (FAKE/REAL)'],
      color: '#f59e0b',
    },
    {
      id: 3,
      name: 'ClaimBuster DeBERTaV2',
      icon: '🔎',
      type: 'Claim Detection (Transformer)',
      status: 'Active',
      description: 'DeBERTa-V2 transformer model trained by the ClaimBuster team to identify check-worthy factual claims. Distinguishes between factual claims that need verification and non-factual statements.',
      specs: [
        { label: 'Model', value: 'whispAI/ClaimBuster-DeBERTaV2' },
        { label: 'Architecture', value: 'DeBERTa V2' },
        { label: 'Output', value: 'CFS / UFS / NFS scores' },
        { label: 'Weight', value: '15%' },
      ],
      patterns: ['Check-worthy Factual Statements (CFS)', 'Unimportant Factual Statements (UFS)', 'Non-Factual Statements (NFS)', 'Claim detection scoring'],
      color: '#8b5cf6',
    },
    {
      id: 4,
      name: 'Google Fact Check Tools API',
      icon: '✅',
      type: 'External Fact-Check Database',
      status: 'Active',
      description: 'Google\'s Fact Check Tools API cross-references input text against a database of verified fact-checks from reputable organizations worldwide including PolitiFact, Snopes, FactCheck.org, and more.',
      specs: [
        { label: 'Provider', value: 'Google Cloud' },
        { label: 'Database', value: 'Global fact-checkers' },
        { label: 'Output', value: 'VERIFIED / DEBUNKED / MIXED' },
        { label: 'Weight', value: '20%' },
      ],
      patterns: ['PolitiFact ratings', 'Snopes verification', 'FactCheck.org cross-reference', 'International fact-checker network'],
      color: '#22c55e',
    },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Detection Engines</h1>
        <p className="page-subtitle">
          VeritasAI uses a multi-engine ensemble of 4 AI systems for maximum accuracy
        </p>
      </div>

      {/* Ensemble Overview */}
      <div className="dataset-stats-bar">
        <span className="ds-stat"><strong>4</strong> Active Engines</span>
        <span className="ds-stat"><strong>2</strong> Transformer Models</span>
        <span className="ds-stat"><strong>60+</strong> Heuristic Rules</span>
        <span className="ds-stat"><strong>Weighted</strong> Ensemble Voting</span>
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
            <h3 className="engine-card-name">Ensemble Merger</h3>
            <div className="engine-card-meta">
              <span className="engine-type-badge">Weighted Voting</span>
              <span className="engine-status-badge">Core System</span>
            </div>
          </div>
        </div>
        <p className="engine-card-desc">
          All engines run in parallel and vote on the verdict. Each engine's vote is weighted by its assigned importance.
          When engines agree, confidence is boosted. When they disagree, the confidence is capped to reflect uncertainty.
          The final verdict is determined by weighted majority voting across all available engines.
        </p>
        <div className="engine-specs">
          <h4>Weight Distribution</h4>
          <div className="specs-grid">
            <div className="spec-item"><span className="spec-label">Heuristic NLP</span><span className="spec-value">30%</span></div>
            <div className="spec-item"><span className="spec-label">HF BERT</span><span className="spec-value">35%</span></div>
            <div className="spec-item"><span className="spec-label">ClaimBuster</span><span className="spec-value">15%</span></div>
            <div className="spec-item"><span className="spec-label">Google Fact Check</span><span className="spec-value">20%</span></div>
          </div>
        </div>
      </div>
    </div>
  );
}
