import EvidenceList from './EvidenceList';

const VERDICT_CONFIG = {
  'Credible': { cssClass: 'badge-credible', icon: '✓' },
  'Likely True': { cssClass: 'badge-mostly-true', icon: '◐' },
  'Mixed / Misleading': { cssClass: 'badge-mixed', icon: '⚠' },
  'Likely False': { cssClass: 'badge-mostly-false', icon: '✕' },
  'False': { cssClass: 'badge-false', icon: '✕' },
  'Opinion / Not Fact-Checkable': { cssClass: 'badge-neutral', icon: '💬' },
};

export default function ClaimList({ claims }) {
  if (!claims || claims.length === 0) return null;

  return (
    <div className="claim-list" style={{ marginTop: '1.5rem', borderTop: '1px solid #e5e7eb', paddingTop: '1rem' }}>
      <h4 style={{ marginBottom: '1rem', color: '#111827' }}>Analyzed Claims ({claims.length})</h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {claims.map((claim, idx) => {
        const cfg = VERDICT_CONFIG[claim.verdict] || VERDICT_CONFIG['Opinion / Not Fact-Checkable'];
        return (
          <div key={claim.claim_id || idx} className="claim-item" style={{ padding: '1rem', border: '1px solid #e5e7eb', borderRadius: '8px', backgroundColor: 'white' }}>
            <div className="claim-header" style={{ marginBottom: '0.5rem' }}>
              <span className={`verdict-badge ${cfg.cssClass}`} style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem' }}>
                {cfg.icon} {claim.verdict} ({claim.confidence}%)
              </span>
            </div>
            <p className="claim-text" style={{ fontSize: '1rem', color: '#1f2937', fontWeight: 500, margin: '0.5rem 0' }}>"{claim.claim_text}"</p>
            {claim.evidence && <EvidenceList evidence={claim.evidence} />}
          </div>
        );
      })}
      </div>
    </div>
  );
}
