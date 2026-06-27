import React from 'react';

const VERDICT_COLORS = {
  'Credible': '#22c55e',
  'Likely True': '#86efac',
  'Mixed / Misleading': '#eab308',
  'Likely False': '#f97316',
  'False': '#ef4444',
  'Insufficient Evidence': '#94a3b8',
  'Opinion / Not Fact-Checkable': '#6366f1'
};

function timeAgo(dateStr) {
  const now = new Date();
  const date = new Date(dateStr);
  const hours = Math.floor((now - date) / (1000 * 60 * 60));
  if (hours < 1) {
    const mins = Math.floor((now - date) / (1000 * 60));
    return `${mins}m ago`;
  }
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function TrendingClaimCard({ claim }) {
  const verdict = claim.current_verdict || 'Insufficient Evidence';
  const color = VERDICT_COLORS[verdict] || '#94a3b8';
  const confidence = claim.current_confidence || 0;
  const history = claim.verdict_history || [];

  return (
    <div className="trending-claim-card">
      <div className="tcc-header">
        <div className="tcc-verdict-wrap">
          <span className="mini-badge" style={{
            background: `${color}20`,
            color: color,
            borderColor: `${color}40`,
          }}>
            {verdict}
          </span>
          {confidence > 0 && (
            <span className="tcc-confidence">{confidence}%</span>
          )}
        </div>
        <div className="tcc-check-count">
          <span className="tcc-count-num">{claim.check_count}</span>
          <span className="tcc-count-text">Checks</span>
        </div>
      </div>

      <p className="tcc-claim-text">{claim.claim_text}</p>

      {claim.supporting_sources && claim.supporting_sources.length > 0 && (
        <div className="tcc-sources">
          {claim.supporting_sources.map((src, idx) => (
            <a 
              key={idx} 
              href={src.url || '#'} 
              target="_blank" 
              rel="noopener noreferrer"
              className="tcc-source-chip"
            >
              {src.name} <span className="tcc-source-score">{src.credibility_score}</span>
            </a>
          ))}
        </div>
      )}

      <div className="tcc-footer">
        <div className="tcc-history">
          {history.map((hist, idx) => {
            const hColor = VERDICT_COLORS[hist.verdict] || '#94a3b8';
            return (
              <div 
                key={idx} 
                className="tcc-history-dot"
                style={{ background: hColor }}
                title={`${hist.verdict} (${timeAgo(hist.checked_at)})`}
              />
            );
          })}
        </div>
        <div className="tcc-time">
          Last checked: {timeAgo(claim.last_checked_at)}
        </div>
      </div>
    </div>
  );
}
