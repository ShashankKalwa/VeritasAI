/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';

const VERDICT_CONFIG = {
  'Credible':                      { icon: '✓', color: '#22c55e', bgColor: '#22c55e18' },
  'Likely True':                   { icon: '◐', color: '#86efac', bgColor: '#86efac18' },
  'Mixed / Misleading':            { icon: '⚠', color: '#eab308', bgColor: '#eab30818' },
  'Likely False':                  { icon: '✕', color: '#f97316', bgColor: '#f9731618' },
  'False':                         { icon: '✕', color: '#ef4444', bgColor: '#ef444418' },
  'Insufficient Evidence':         { icon: '?', color: '#94a3b8', bgColor: '#94a3b818' },
  'Opinion / Not Fact-Checkable':  { icon: '💬', color: '#6366f1', bgColor: '#6366f118' },
};

function getVerdictCfg(verdict) {
  return VERDICT_CONFIG[verdict] || VERDICT_CONFIG['Insufficient Evidence'];
}

export default function ResultCard({ result }) {
  const [visible, setVisible] = useState(false);
  const [expandedClaim, setExpandedClaim] = useState(0);
  const [activeEvidenceTab, setActiveEvidenceTab] = useState({});
  const [showExplainability, setShowExplainability] = useState(false);

  useEffect(() => {
    if (result) {
      setVisible(false);
      setExpandedClaim(0);
      setActiveEvidenceTab({});
      setShowExplainability(false);
      setTimeout(() => setVisible(true), 50);
    }
  }, [result]);

  if (!result) return null;

  const overallCfg = getVerdictCfg(result.overall_verdict);
  const claims = result.claims || [];
  const explainability = result.explainability || {};

  const handleShare = () => {
    const shareText = `VeritasAI: ${result.overall_verdict} (${result.overall_confidence || '?'}%)\n\n${explainability.primary_signal || ''}`;
    navigator.clipboard.writeText(shareText).then(() => alert('Copied to clipboard!'));
  };

  return (
    <div className={`result-card ${visible ? 'visible' : ''}`}
         style={{ borderColor: overallCfg.color + '40' }}>

      {/* ── Overall Verdict Header ── */}
      <div className="result-header-v2">
        <div className="verdict-badge-v2" style={{
          background: overallCfg.bgColor,
          borderColor: overallCfg.color + '60',
          color: overallCfg.color,
        }}>
          <span className="verdict-icon">{overallCfg.icon}</span>
          <span className="verdict-label">{result.overall_verdict}</span>
        </div>
        {result.overall_confidence != null && (
          <div className="confidence-pill" style={{ color: overallCfg.color }}>
            {result.overall_confidence}% confidence
          </div>
        )}
        {result.content_type && result.content_type !== 'news_report' && (
          <span className="content-type-tag-v2">{result.content_type.replace(/_/g, ' ')}</span>
        )}
      </div>

      {/* ── API Quota Exceeded Warning ── */}
      {explainability.api_rate_limited && (
        <div className="api-limit-warning" style={{
          backgroundColor: '#ef444420',
          border: '1px solid #ef4444',
          color: '#ef4444',
          padding: '12px 16px',
          borderRadius: '8px',
          margin: '0 0 16px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontWeight: '500'
        }}>
          <span style={{ fontSize: '1.2rem' }}>⚠️</span>
          <span>
            <strong>Search API Quota Exceeded:</strong> Live evidence retrieval is temporarily paused. Results shown may be incomplete or based solely on cached data and internal heuristics.
          </span>
        </div>
      )}

      {/* ── Primary Signal ── */}
      {explainability.primary_signal && (
        <div className="primary-signal">
          <span className="signal-icon">💡</span>
          <span>{explainability.primary_signal}</span>
        </div>
      )}

      {/* ── Per-Claim Breakdown ── */}
      {claims.length > 0 && (
        <div className="claims-section">
          <h4 className="section-title">
            Claims Analyzed ({claims.length})
          </h4>
          <div className="claims-list">
            {claims.map((claim, idx) => {
              const claimCfg = getVerdictCfg(claim.verdict);
              const isExpanded = expandedClaim === idx;
              const evidenceTab = activeEvidenceTab[idx] || 'supporting';
              const evidence = claim.evidence || {};

              return (
                <div key={claim.claim_id || idx} className="claim-item"
                     style={{ borderLeftColor: claimCfg.color }}>
                  {/* Claim header — clickable to expand */}
                  <div className="claim-header" onClick={() => setExpandedClaim(isExpanded ? -1 : idx)}>
                    <div className="claim-header-left">
                      <span className="claim-number">#{idx + 1}</span>
                      <span className="claim-text-preview">{claim.claim_text}</span>
                    </div>
                    <div className="claim-header-right">
                      <span className="claim-verdict-mini" style={{
                        background: claimCfg.bgColor,
                        color: claimCfg.color,
                        borderColor: claimCfg.color + '40',
                      }}>
                        {claimCfg.icon} {claim.verdict}
                      </span>
                      {claim.confidence != null && (
                        <span className="claim-confidence">{claim.confidence}%</span>
                      )}
                      <span className={`claim-chevron ${isExpanded ? 'expanded' : ''}`}>▾</span>
                    </div>
                  </div>

                  {/* Expanded claim details */}
                  {isExpanded && (
                    <div className="claim-details">
                      {/* Evidence Tabs */}
                      <div className="evidence-tabs">
                        {[
                          { key: 'supporting', label: 'Supporting', count: (evidence.supporting || []).length, color: '#22c55e' },
                          { key: 'contradicting', label: 'Contradicting', count: (evidence.contradicting || []).length, color: '#ef4444' },
                          { key: 'unclear', label: 'Unclear', count: (evidence.unclear || []).length, color: '#94a3b8' },
                        ].map(tab => (
                          <button
                            key={tab.key}
                            className={`evidence-tab ${evidenceTab === tab.key ? 'active' : ''}`}
                            onClick={() => setActiveEvidenceTab(prev => ({ ...prev, [idx]: tab.key }))}
                            style={evidenceTab === tab.key ? { borderBottomColor: tab.color, color: tab.color } : {}}
                          >
                            {tab.label} ({tab.count})
                          </button>
                        ))}
                      </div>

                      {/* Evidence Items */}
                      <div className="evidence-list">
                        {(evidence[evidenceTab] || []).length === 0 ? (
                          <p className="evidence-empty">No {evidenceTab} evidence found.</p>
                        ) : (
                          (evidence[evidenceTab] || []).map((item, eidx) => (
                            <div key={eidx} className="evidence-item">
                              <div className="evidence-item-header">
                                <span className="evidence-source">{item.source_name || 'Unknown'}</span>
                                {item.credibility_score > 0 && (
                                  <span className={`credibility-badge ${
                                    item.credibility_score >= 80 ? 'cred-high' :
                                    item.credibility_score >= 50 ? 'cred-mid' : 'cred-low'
                                  }`}>
                                    {item.credibility_score}
                                  </span>
                                )}
                                {item.published_date && (
                                  <span className="evidence-date">{item.published_date}</span>
                                )}
                              </div>
                              {item.title && <p className="evidence-title">{item.title}</p>}
                              {item.snippet && <p className="evidence-snippet">{item.snippet}</p>}
                              {item.url && (
                                <a href={item.url} target="_blank" rel="noopener noreferrer"
                                   className="evidence-link">View source →</a>
                              )}
                            </div>
                          ))
                        )}
                      </div>

                      {/* Claim Reasoning */}
                      {claim.reasoning && (
                        <div className="claim-reasoning">
                          <span className="reasoning-label">AI Reasoning:</span>
                          <span>{claim.reasoning}</span>
                        </div>
                      )}

                      {/* Model Signals for this claim */}
                      {claim.model_signals && (
                        <div className="model-signals">
                          <div className="signal-row">
                            <span className="signal-name">BERT Linguistic</span>
                            <div className="signal-bar-bg">
                              <div className="signal-bar-fill" style={{
                                width: `${claim.model_signals.bert_linguistic_signal || 50}%`,
                                backgroundColor: (claim.model_signals.bert_linguistic_signal || 50) > 60 ? '#22c55e' : '#eab308',
                              }} />
                            </div>
                            <span className="signal-value">{claim.model_signals.bert_linguistic_signal || 50}</span>
                          </div>
                          <div className="signal-row">
                            <span className="signal-name">Manipulation Check</span>
                            <div className="signal-bar-bg">
                              <div className="signal-bar-fill" style={{
                                width: `${claim.model_signals.heuristic_manipulation_signal || 50}%`,
                                backgroundColor: (claim.model_signals.heuristic_manipulation_signal || 50) > 60 ? '#22c55e' : '#eab308',
                              }} />
                            </div>
                            <span className="signal-value">{claim.model_signals.heuristic_manipulation_signal || 50}</span>
                          </div>
                          <div className="signal-row">
                            <span className="signal-name">Check-Worthiness</span>
                            <div className="signal-bar-bg">
                              <div className="signal-bar-fill" style={{
                                width: `${claim.model_signals.claimbuster_check_worthiness || 50}%`,
                                backgroundColor: '#a855f7',
                              }} />
                            </div>
                            <span className="signal-value">{claim.model_signals.claimbuster_check_worthiness || 50}</span>
                          </div>
                          {claim.model_signals.google_factcheck_match && (
                            <div className="signal-row gfc-match">
                              <span className="signal-name">✅ Google Fact Check Match</span>
                              <span className="signal-value gfc-detail">
                                {claim.model_signals.google_factcheck_details || 'Match found'}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Explainability Panel ── */}
      <div className="explainability-section">
        <button className="explainability-toggle" onClick={() => setShowExplainability(!showExplainability)}>
          <span>🔬 Explainability Report</span>
          <span className={`claim-chevron ${showExplainability ? 'expanded' : ''}`}>▾</span>
        </button>

        {showExplainability && (
          <div className="explainability-content">
            {explainability.primary_signal && (
              <div className="explain-primary">
                <strong>Primary Signal:</strong> {explainability.primary_signal}
              </div>
            )}

            {explainability.secondary_signals && explainability.secondary_signals.length > 0 && (
              <div className="explain-secondary">
                <strong>Supporting Signals:</strong>
                <ul>
                  {explainability.secondary_signals.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {explainability.top_sources && explainability.top_sources.length > 0 && (
              <div className="explain-sources">
                <strong>Top Sources:</strong>
                <ul>
                  {explainability.top_sources.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
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
          {claims.length} claim{claims.length !== 1 ? 's' : ''} analyzed
          {result.content_type && ` · ${result.content_type.replace(/_/g, ' ')}`}
        </span>
      </div>
    </div>
  );
}
