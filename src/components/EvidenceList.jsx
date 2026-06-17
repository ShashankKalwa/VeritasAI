export default function EvidenceList({ evidence }) {
  if (!evidence) return null;
  const { supporting_evidence = [], contradicting_evidence = [], unclear_evidence = [], reasoning } = evidence;
  
  if (supporting_evidence.length === 0 && contradicting_evidence.length === 0 && unclear_evidence.length === 0) {
     return <div className="evidence-list" style={{ marginTop: '0.5rem', fontSize: '0.9rem', color: '#666' }}><p>No evidence found.</p></div>;
  }

  const renderItems = (items, type, color) => {
    if (items.length === 0) return null;
    return (
      <div className={`evidence-group evidence-${type}`} style={{ marginTop: '0.5rem' }}>
        <h5 style={{ color: color, marginBottom: '0.25rem', fontSize: '0.85rem', textTransform: 'uppercase' }}>{type} Evidence</h5>
        <ul style={{ paddingLeft: '1rem', margin: 0, fontSize: '0.85rem' }}>
          {items.map((item, idx) => (
            <li key={idx} style={{ marginBottom: '0.25rem' }}>
              <a href={item.url} target="_blank" rel="noreferrer" style={{ fontWeight: 600, color: '#3b82f6', textDecoration: 'none' }}>
                {item.source_name}
              </a>
              <span style={{ color: '#888', fontSize: '0.8rem', marginLeft: '0.25rem' }}>(Score: {item.credibility_score})</span>
              <p style={{ margin: '0.1rem 0 0 0', color: '#444' }}>{item.title}</p>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="evidence-list" style={{ marginTop: '1rem', padding: '0.75rem', backgroundColor: '#f8fafc', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
      {reasoning && <div className="evidence-reasoning" style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#334155' }}><strong>AI Reasoning:</strong> {reasoning}</div>}
      <div className="evidence-groups">
        {renderItems(supporting_evidence, 'supporting', '#10b981')}
        {renderItems(contradicting_evidence, 'contradicting', '#ef4444')}
        {renderItems(unclear_evidence, 'unclear', '#f59e0b')}
      </div>
    </div>
  );
}
