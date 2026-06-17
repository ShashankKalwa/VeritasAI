import { useState, useEffect } from 'react';
import ClaimList from './ClaimList';

const VERDICT_CONFIG = {
  'Credible': { icon: '✓', label: 'CREDIBLE', cssClass: 'result-credible', badgeClass: 'badge-credible', barClass: 'bar-credible' },
  'Likely True': { icon: '◐', label: 'LIKELY TRUE', cssClass: 'result-mostly-true', badgeClass: 'badge-mostly-true', barClass: 'bar-mostly-true' },
  'Mixed / Misleading': { icon: '⚠', label: 'MIXED / MISLEADING', cssClass: 'result-mixed', badgeClass: 'badge-mixed', barClass: 'bar-mixed' },
  'Likely False': { icon: '✕', label: 'LIKELY FALSE', cssClass: 'result-mostly-false', badgeClass: 'badge-mostly-false', barClass: 'bar-mostly-false' },
  'False': { icon: '✕', label: 'FALSE', cssClass: 'result-false', badgeClass: 'badge-false', barClass: 'bar-false' },
  'Opinion / Not Fact-Checkable': { icon: '💬', label: 'OPINION', cssClass: 'result-neutral', badgeClass: 'badge-neutral', barClass: 'bar-neutral' }
};

export default function ResultCard({ result }) {
  const [visible, setVisible] = useState(false);
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    if (result) {
      setVisible(false);
      setBarWidth(0);
      setTimeout(() => setVisible(true), 50);
      setTimeout(() => setBarWidth(result.overall_confidence), 200);
    }
  }, [result]);

  if (!result) return null;

  const cfg = VERDICT_CONFIG[result.overall_verdict] || VERDICT_CONFIG['Mixed / Misleading'];
  const explainability = result.explainability || {};

  const handleShare = () => {
    const shareText = `VeritasAI: ${cfg.label} (${result.overall_confidence}%)\n\n${explainability.primary_signal}`;
    navigator.clipboard.writeText(shareText).then(() => alert('Copied to clipboard!'));
  };

  return (
    <div className={`result-card ${visible ? 'visible' : ''} ${cfg.cssClass}`}>
      <div className="result-header">
        <div className={`verdict-badge ${cfg.badgeClass}`}>
          {cfg.icon} {cfg.label}
        </div>
        <div className="result-meta">
          <span className="content-type-tag">{result.content_type}</span>
        </div>
      </div>

      <div className="confidence-section">
        <div className="confidence-label">
          <span>Overall Confidence Level</span>
          <span className="confidence-value">{result.overall_confidence}%</span>
        </div>
        <div className="confidence-bar-bg">
          <div
            className={`confidence-bar-fill ${cfg.barClass}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      <div className="result-analysis">
        <h4>Analysis</h4>
        <p>{explainability.primary_signal}</p>
      </div>

      {explainability.secondary_signals && explainability.secondary_signals.length > 0 && (
        <div className="result-indicators">
          <h4>Key Indicators</h4>
          <div className="indicator-pills">
            {explainability.secondary_signals.map((indicator, i) => (
              <span key={i} className={`indicator-pill indicator-neutral`}>
                {indicator}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {explainability.top_sources && explainability.top_sources.length > 0 && (
        <div className="fact-check-section">
           <h4>Top Sources</h4>
           <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.95rem' }}>
             {explainability.top_sources.map((src, i) => (
               <li key={i} style={{ marginBottom: '0.25rem' }}>{src}</li>
             ))}
           </ul>
        </div>
      )}

      {result.claims && result.claims.length > 0 && (
        <ClaimList claims={result.claims} />
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
      </div>
    </div>
  );
}
