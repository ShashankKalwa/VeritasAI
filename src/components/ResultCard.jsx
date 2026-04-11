import { useState, useEffect } from 'react';

const ENGINE_LABELS = {
  heuristic_nlp: '🔍 Heuristic NLP',
  huggingface_bert: '🤗 HuggingFace BERT',
  claimbuster_deberta: '🔎 ClaimBuster DeBERTa',
  google_factcheck: '✅ Google Fact Check',
};

const VERDICT_CONFIG = {
  REAL: { icon: '✓', label: 'VERIFIED REAL', cssClass: 'result-real', badgeClass: 'badge-real', barClass: 'bar-real' },
  PARTIALLY_TRUE: { icon: '◐', label: 'PARTIALLY TRUE', cssClass: 'result-partial', badgeClass: 'badge-partial', barClass: 'bar-partial' },
  MISLEADING: { icon: '⚠', label: 'MISLEADING', cssClass: 'result-misleading', badgeClass: 'badge-misleading', barClass: 'bar-misleading' },
  FAKE: { icon: '✕', label: 'FAKE', cssClass: 'result-fake', badgeClass: 'badge-fake', barClass: 'bar-fake' },
  UNCERTAIN: { icon: '?', label: 'UNCERTAIN', cssClass: 'result-uncertain', badgeClass: 'badge-uncertain', barClass: 'bar-uncertain' },
};

const CONTENT_TYPE_LABELS = {
  HARD_NEWS: 'Hard News',
  BREAKING: '⚡ Breaking News',
  OPINION: '💬 Opinion',
  SATIRE: '🎭 Satire',
};

export default function ResultCard({ result }) {
  const [visible, setVisible] = useState(false);
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    if (result) {
      setVisible(false);
      setBarWidth(0);
      setTimeout(() => setVisible(true), 50);
      setTimeout(() => setBarWidth(result.confidence), 200);
    }
  }, [result]);

  if (!result) return null;

  const cfg = VERDICT_CONFIG[result.verdict] || VERDICT_CONFIG.UNCERTAIN;

  const handleShare = () => {
    const shareText = `VeritasAI: ${cfg.label} (${result.confidence}%)\n\n${result.analysis}`;
    navigator.clipboard.writeText(shareText).then(() => alert('Copied to clipboard!'));
  };

  return (
    <div className={`result-card ${visible ? 'visible' : ''} ${cfg.cssClass}`}>
      <div className="result-header">
        <div className={`verdict-badge ${cfg.badgeClass}`}>
          {cfg.icon} {cfg.label}
        </div>
        <div className="result-meta">
          <span className="result-category">{result.category}</span>
          {result.content_type && result.content_type !== 'HARD_NEWS' && (
            <span className="content-type-tag">{CONTENT_TYPE_LABELS[result.content_type] || result.content_type}</span>
          )}
        </div>
      </div>

      <div className="confidence-section">
        <div className="confidence-label">
          <span>Confidence Level</span>
          <span className="confidence-value">{result.confidence}%</span>
        </div>
        <div className="confidence-bar-bg">
          <div
            className={`confidence-bar-fill ${cfg.barClass}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {/* Engines Used */}
      {result.engines_used && result.engines_used.length > 0 && (
        <div className="result-engines">
          <h4>Detection Engines ({result.engines_used.length})</h4>
          <div className="engine-badges">
            {result.engines_used.map((engine, i) => (
              <span key={i} className="engine-badge">
                {ENGINE_LABELS[engine] || engine}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="result-analysis">
        <h4>Analysis</h4>
        <p>{result.analysis}</p>
      </div>

      <div className="result-indicators">
        <h4>Key Indicators</h4>
        <div className="indicator-pills">
          {result.indicators && result.indicators.map((indicator, i) => (
            <span key={i} className={`indicator-pill indicator-${result.verdict === 'REAL' ? 'real' : result.verdict === 'FAKE' ? 'fake' : 'neutral'}`}>
              {indicator}
            </span>
          ))}
        </div>
      </div>

      {/* Google Fact Check Results */}
      {result.google_factcheck_found && result.google_factcheck_claims && (
        <div className="fact-check-section">
          <h4>🔍 Existing Fact-Checks Found</h4>
          {result.google_factcheck_rating && (
            <div className="fact-check-item">
              <span className="fc-label">Overall Rating:</span>
              <span className={`fc-value ${result.google_factcheck_rating === 'DEBUNKED' ? 'fc-suspicious' : 'fc-ok'}`}>
                {result.google_factcheck_rating}
              </span>
            </div>
          )}
          {result.google_factcheck_claims.map((claim, i) => (
            <div key={i} className="fact-check-item">
              <span className="fc-label">{claim.publisher}:</span>
              <span className="fc-value">{claim.rating}</span>
            </div>
          ))}
        </div>
      )}

      {/* ClaimBuster Score */}
      {result.claimbuster_score != null && (
        <div className="fact-check-section">
          <h4>🔎 Claim Analysis</h4>
          <div className="fact-check-item">
            <span className="fc-label">Check-worthiness:</span>
            <span className={`fc-value ${result.claimbuster_checkworthy ? 'fc-suspicious' : 'fc-ok'}`}>
              {(result.claimbuster_score * 100).toFixed(1)}%
              {result.claimbuster_checkworthy ? ' — Needs verification' : ' — Low priority'}
            </span>
          </div>
        </div>
      )}

      <div className="result-footer">
        <button className="btn-share" onClick={handleShare}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
            <polyline points="16 6 12 2 8 6"/>
            <line x1="12" y1="2" x2="12" y2="15"/>
          </svg>
          Share
        </button>
        <span className="result-score">
          {result.engines_used?.length || 1} engines · {result.source_type || 'text'}
          {result.convergence_signals > 0 && ` · ${result.convergence_signals} signals`}
        </span>
      </div>
    </div>
  );
}
