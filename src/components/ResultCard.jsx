import { useState, useEffect } from 'react';

export default function ResultCard({ result }) {
  const [visible, setVisible] = useState(false);
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    if (result) {
      setTimeout(() => setVisible(true), 50);
      setTimeout(() => setBarWidth(result.confidence), 200);
    }
  }, [result]);

  if (!result) return null;

  const isFake = result.verdict === 'FAKE';

  const handleShare = () => {
    const shareText = `VeritasAI Analysis: ${result.verdict} (${result.confidence}% confidence)\n\n"${result.input_text || ''}"\n\n${result.analysis}`;
    navigator.clipboard.writeText(shareText).then(() => {
      alert('Result copied to clipboard!');
    });
  };

  return (
    <div className={`result-card ${visible ? 'visible' : ''} ${isFake ? 'result-fake' : 'result-real'}`}>
      <div className="result-header">
        <div className={`verdict-badge ${isFake ? 'badge-fake' : 'badge-real'}`}>
          {isFake ? '⚠' : '✓'} {result.verdict}
        </div>
        <span className="result-category">{result.category}</span>
      </div>

      <div className="confidence-section">
        <div className="confidence-label">
          <span>Confidence Level</span>
          <span className="confidence-value">{result.confidence}%</span>
        </div>
        <div className="confidence-bar-bg">
          <div
            className={`confidence-bar-fill ${isFake ? 'bar-fake' : 'bar-real'}`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
      </div>

      <div className="result-analysis">
        <h4>Analysis</h4>
        <p>{result.analysis}</p>
      </div>

      <div className="result-indicators">
        <h4>Key Indicators</h4>
        <div className="indicator-pills">
          {result.indicators.map((indicator, i) => (
            <span key={i} className={`indicator-pill ${isFake ? 'indicator-fake' : 'indicator-real'}`}>
              {indicator}
            </span>
          ))}
        </div>
      </div>

      <div className="result-footer">
        <button className="btn-share" onClick={handleShare}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
            <polyline points="16 6 12 2 8 6"/>
            <line x1="12" y1="2" x2="12" y2="15"/>
          </svg>
          Share Result
        </button>
        <span className="result-score">Heuristic Score: {result.heuristic_score}</span>
      </div>
    </div>
  );
}
