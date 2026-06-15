import { useState, useEffect } from 'react';

// ─── Engine display order and colors (FIX-002) ───
const ENGINE_ORDER = ['bert_huggingface', 'heuristic_nlp', 'claimbuster_deberta', 'google_fact_check'];

const ENGINE_ICONS = {
  bert_huggingface: '🤖',
  heuristic_nlp: '🔍',
  claimbuster_deberta: '🔎',
  google_fact_check: '✓',
};

// ─── 6-label verdict config (FIX-003) ───
const VERDICT_CONFIG = {
  CREDIBLE:          { icon: '✓', label: 'CREDIBLE',            cssClass: 'result-credible',      badgeClass: 'badge-credible',      barClass: 'bar-credible' },
  MOSTLY_TRUE:       { icon: '◐', label: 'MOSTLY TRUE',         cssClass: 'result-mostly-true',   badgeClass: 'badge-mostly-true',   barClass: 'bar-mostly-true' },
  MIXED:             { icon: '⚠', label: 'MIXED / MISLEADING',  cssClass: 'result-mixed',         badgeClass: 'badge-mixed',         barClass: 'bar-mixed' },
  MOSTLY_FALSE:      { icon: '✕', label: 'MOSTLY FALSE',        cssClass: 'result-mostly-false',  badgeClass: 'badge-mostly-false',  barClass: 'bar-mostly-false' },
  FALSE:             { icon: '✕', label: 'FALSE',               cssClass: 'result-false',         badgeClass: 'badge-false',         barClass: 'bar-false' },
  INSUFFICIENT_DATA: { icon: '?', label: 'INSUFFICIENT DATA',   cssClass: 'result-insufficient',  badgeClass: 'badge-insufficient',  barClass: 'bar-insufficient' },
};

export default function ResultCard({ result }) {
  const [visible, setVisible] = useState(false);
  const [barWidth, setBarWidth] = useState(0);
  const [showFcDetails, setShowFcDetails] = useState(false);

  useEffect(() => {
    if (result) {
      setVisible(false);
      setBarWidth(0);
      setShowFcDetails(false);
      setTimeout(() => setVisible(true), 50);
      setTimeout(() => setBarWidth(result.verdict?.confidence_pct || result.confidence || 0), 200);
    }
  }, [result]);

  if (!result) return null;

  // Support both new nested schema and legacy flat schema
  const verdictLabel = result.verdict?.label || result.verdict_label || result.verdict || 'MIXED';
  const confidencePct = result.verdict?.confidence_pct || result.confidence_pct || result.confidence || 0;
  const confidenceTier = result.verdict?.confidence_tier || 'MEDIUM';
  const contentType = result.content_type?.label || result.content_type || 'News Report';
  const contentTypeId = result.content_type?.id || 'NEWS_REPORT';
  const analysisSummary = result.analysis_summary || result.analysis || '';
  const engines = result.engines || [];
  const indicators = result.indicators || {};
  const primaryIssue = indicators.primary_issue || null;
  const secondaryIssues = indicators.secondary_issues || [];
  const factCheck = result.fact_check || null;
  const claimAnalysis = result.claim_analysis || null;
  const meta = result.meta || {};
  const category = result.category || 'General';

  const cfg = VERDICT_CONFIG[verdictLabel] || VERDICT_CONFIG.MIXED;

  const handleShare = () => {
    const shareText = `VeritasAI: ${cfg.label} (${confidencePct}%)\n\n${analysisSummary}`;
    navigator.clipboard.writeText(shareText).then(() => alert('Copied to clipboard!'));
  };

  // Sort engines by display order
  const sortedEngines = [...engines].sort(
    (a, b) => ENGINE_ORDER.indexOf(a.id) - ENGINE_ORDER.indexOf(b.id)
  );

  return (
    <div className={`result-card ${visible ? 'visible' : ''} ${cfg.cssClass}`}>

      {/* ── HEADER: Verdict badge + content type ── */}
      <div className="result-header">
        <div className={`verdict-badge ${cfg.badgeClass}`}>
          {cfg.icon} {cfg.label}
        </div>
        <div className="result-meta">
          <span className="content-type-tag">{contentType}</span>
          <span className="result-category">{category}</span>
        </div>
      </div>

      {/* ── CONFIDENCE BAR ── */}
      <div className="confidence-section">
        <div className="confidence-label">
          <span>Confidence Level</span>
          <span className="confidence-value-row">
            <span className="confidence-value">{confidencePct}%</span>
            <span className={`confidence-tier tier-${confidenceTier.toLowerCase()}`}>
              {confidenceTier === 'LOW' && '⚠ LOW CONFIDENCE'}
              {confidenceTier === 'MEDIUM' && ''}
              {confidenceTier === 'HIGH' && '✓ HIGH CONFIDENCE'}
            </span>
          </span>
        </div>
        <div className="confidence-bar-bg">
          <div
            className={`confidence-bar-fill ${cfg.barClass}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      {/* ── INSUFFICIENT DATA state ── */}
      {verdictLabel === 'INSUFFICIENT_DATA' && (
        <div className="insufficient-data-msg">
          <span className="insuff-icon">ℹ️</span>
          <p>Insufficient signals to make a reliable determination. Submit more context or a longer text for better analysis.</p>
        </div>
      )}

      {/* ── DETECTION ENGINES (FIX-002 — always show all 4) ── */}
      <div className="result-engines">
        <h4>Detection Engines ({sortedEngines.filter(e => e.status === 'active').length})</h4>
        <div className="engine-badges">
          {sortedEngines.map((engine) => (
            <span
              key={engine.id}
              className={`engine-chip ${engine.status === 'active' ? '' : 'engine-unavailable'}`}
              style={engine.status === 'active' ? {
                borderColor: engine.color + '40',
                color: engine.color,
                background: engine.color + '15',
              } : {}}
            >
              <span className={`engine-dot ${engine.status === 'active' ? 'dot-active' : 'dot-inactive'}`}
                style={engine.status === 'active' ? { background: engine.color } : {}}
              />
              {ENGINE_ICONS[engine.id] || '●'} {engine.name}
              {engine.status !== 'active' && <span className="chip-unavailable">Unavailable</span>}
            </span>
          ))}
        </div>
      </div>

      {/* ── ANALYSIS SUMMARY ── */}
      {analysisSummary && verdictLabel !== 'INSUFFICIENT_DATA' && (
        <div className="result-analysis">
          <h4>Analysis</h4>
          <p>{analysisSummary}</p>
        </div>
      )}

      {/* ── PRIMARY ISSUE (FIX-004) ── */}
      {primaryIssue && verdictLabel !== 'INSUFFICIENT_DATA' && (
        <div className="primary-issue-section">
          <h4>Primary Issue</h4>
          <div className={`primary-issue-badge issue-${
            verdictLabel === 'CREDIBLE' || verdictLabel === 'MOSTLY_TRUE' ? 'credible' :
            verdictLabel === 'FALSE' || verdictLabel === 'MOSTLY_FALSE' ? 'false' : 'neutral'
          }`}>
            <span className="issue-label">{primaryIssue.label}</span>
            {primaryIssue.description && (
              <span className="issue-desc">{primaryIssue.description}</span>
            )}
          </div>
        </div>
      )}

      {/* ── SECONDARY ISSUES (FIX-004) ── */}
      {secondaryIssues.length > 0 && verdictLabel !== 'INSUFFICIENT_DATA' && (
        <div className="secondary-issues-section">
          <h4>Secondary Issues</h4>
          <div className="secondary-issues-row">
            {secondaryIssues.map((issue, i) => (
              <span key={i} className={`secondary-issue-chip issue-${
                verdictLabel === 'CREDIBLE' || verdictLabel === 'MOSTLY_TRUE' ? 'credible' :
                verdictLabel === 'FALSE' || verdictLabel === 'MOSTLY_FALSE' ? 'false' : 'neutral'
              }`}>
                {issue.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── CLAIM ANALYSIS (FIX-005) ── */}
      {claimAnalysis && (
        <div className="claim-analysis-section">
          <h4>🔎 Claim Analysis</h4>
          <div className="claim-analysis-row">
            <span className="ca-label">Check-worthiness:</span>
            <span className={`ca-value ${claimAnalysis.check_worthiness_pct > 70 ? 'ca-high' : 'ca-low'}`}>
              {claimAnalysis.check_worthiness_pct}% — {claimAnalysis.label}
            </span>
          </div>
        </div>
      )}

      {/* ── FACT-CHECK MATCHES (FIX-005) ── */}
      {factCheck && factCheck.matches_found > 0 && (
        <div className="fact-check-matches-section">
          <h4>
            ✓ Fact-Check Matches
            <button
              className="fc-toggle-btn"
              onClick={() => setShowFcDetails(!showFcDetails)}
            >
              {showFcDetails ? 'Hide' : 'View All'}
            </button>
          </h4>
          <p className="fc-summary">
            {factCheck.matches_found} matching verified fact-check{factCheck.matches_found > 1 ? 's' : ''} found
          </p>
          {showFcDetails && (
            <div className="fc-details">
              {factCheck.results.map((fc, i) => (
                <div key={i} className="fc-detail-item">
                  <span className="fc-publisher">{fc.publisher}:</span>
                  <span className={`fc-rating ${
                    fc.rating.toLowerCase().includes('false') ? 'fc-rating-false' : 'fc-rating-other'
                  }`}>
                    "{fc.rating}"
                  </span>
                  {fc.url && (
                    <a href={fc.url} target="_blank" rel="noopener noreferrer" className="fc-link">↗</a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Opinion/Satire disclaimer (FIX-006) ── */}
      {contentTypeId === 'OPINION_SATIRE' && (
        <div className="content-disclaimer">
          ℹ️ Opinion and satire content is scored differently from factual reporting.
        </div>
      )}

      {/* ── FOOTER ── */}
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
          {meta.engines_used || engines.filter(e => e.status === 'active').length} engines
          · {contentType.toLowerCase?.() || 'text'}
          {meta.signals_detected > 0 && ` · ${meta.signals_detected} signals`}
        </span>
      </div>
    </div>
  );
}
