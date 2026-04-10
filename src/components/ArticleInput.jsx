import { useState } from 'react';

const SAMPLE_FAKE_1 = "Scientists discover miracle cure suppressed by pharmaceutical companies for decades, whistleblower reveals shocking truth mainstream media refuses to cover";
const SAMPLE_FAKE_2 = "Government secretly adding mind control chemicals to tap water since 1975, leaked documents from anonymous insider finally surface";
const SAMPLE_REAL_1 = "FDA approves new Alzheimer's drug after successful phase 3 clinical trial, marking significant milestone in neurodegenerative disease treatment";
const SAMPLE_REAL_2 = "Federal Reserve holds interest rates steady for third consecutive meeting, citing ongoing inflation monitoring and labor market stability";

export default function ArticleInput({ onAnalyze, isLoading }) {
  const [text, setText] = useState('');
  const maxChars = 5000;

  const handleSubmit = () => {
    if (text.trim().length >= 10 && !isLoading) {
      onAnalyze(text);
    }
  };

  const loadSample = (sample) => {
    setText(sample);
  };

  return (
    <div className="article-input-container">
      <h1 className="hero-title">See Through the Noise</h1>
      <p className="hero-subtitle">
        Paste any news article or headline below — our AI-powered heuristic engine
        will analyze it for misinformation patterns in real-time.
      </p>

      <div className="input-wrapper">
        <textarea
          id="article-textarea"
          className="article-textarea"
          value={text}
          onChange={e => setText(e.target.value.slice(0, maxChars))}
          placeholder="Paste a news article, headline, or social media post here..."
          rows={6}
        />
        <div className="input-footer">
          <span className="char-count">
            {text.length} / {maxChars}
          </span>
          <button
            id="analyze-button"
            className="btn-primary btn-analyze"
            onClick={handleSubmit}
            disabled={text.trim().length < 10 || isLoading}
          >
            {isLoading ? (
              <span className="spinner"></span>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
                Analyze Article
              </>
            )}
          </button>
        </div>
      </div>

      <div className="sample-row">
        <span className="sample-label">Try a sample:</span>
        <button className="sample-pill fake" onClick={() => loadSample(SAMPLE_FAKE_1)}>Fake #1</button>
        <button className="sample-pill fake" onClick={() => loadSample(SAMPLE_FAKE_2)}>Fake #2</button>
        <button className="sample-pill real" onClick={() => loadSample(SAMPLE_REAL_1)}>Real #1</button>
        <button className="sample-pill real" onClick={() => loadSample(SAMPLE_REAL_2)}>Real #2</button>
      </div>
    </div>
  );
}
