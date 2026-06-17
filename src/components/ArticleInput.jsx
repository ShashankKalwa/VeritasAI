import { useState, useRef } from 'react';

const SAMPLES = {
  credible: "Lenovo unveiled a transparent laptop at MWC 2024, featuring a see-through display powered by micro-LED technology according to Reuters",
  misleading: "Scientists discover miracle cure suppressed by pharmaceutical companies for decades, whistleblower reveals shocking truth mainstream media refuses to cover",
  opinion: "I think the government should invest more in renewable energy sources. In my view, solar power is the future.",
  social: "@tech_news The new iPhone 17 is going to be absolutely INSANE 🔥🔥 #Apple #iPhone17 #tech",
};

const INPUT_TYPES = [
  { value: 'text', label: '✍️ Article Text', icon: '✍️' },
  { value: 'url', label: '🔗 URL', icon: '🔗' },
  { value: 'headline', label: '📰 Headline', icon: '📰' },
  { value: 'social_post', label: '📱 Social Post', icon: '📱' },
];

const CONTENT_TYPES = [
  { value: 'auto', label: 'Auto-detect' },
  { value: 'news_report', label: 'News Report' },
  { value: 'opinion_satire', label: 'Opinion / Satire' },
  { value: 'social_media_post', label: 'Social Media Post' },
];

export default function ArticleInput({ onAnalyze, loading }) {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('text'); // 'text' or 'file'
  const [inputType, setInputType] = useState('text');
  const [contentType, setContentType] = useState('auto');
  const [fileName, setFileName] = useState('');
  const [fileObj, setFileObj] = useState(null);
  const fileRef = useRef(null);

  const handleSubmit = () => {
    if (mode === 'file' && fileObj) {
      onAnalyze(null, fileObj, inputType, contentType);
    } else if (text.trim().length >= 10) {
      onAnalyze(text, null, inputType, contentType);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();
    const allowed = ['pdf', 'docx', 'doc', 'txt', 'text', 'md'];
    if (!allowed.includes(ext)) {
      alert('Unsupported file. Please upload PDF, DOCX, or TXT files.');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('File too large. Maximum 5MB.');
      return;
    }

    setFileObj(file);
    setFileName(file.name);
  };

  const clearFile = () => {
    setFileObj(null);
    setFileName('');
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleSample = (key) => {
    setText(SAMPLES[key]);
    setMode('text');
    clearFile();
    // Auto-set input type based on sample
    if (key === 'social') setInputType('social_post');
    else if (key === 'opinion') setInputType('text');
    else setInputType('text');
  };

  const canSubmit = mode === 'file' ? !!fileObj : text.trim().length >= 10;

  return (
    <div className="article-input-container">
      <h1 className="hero-title">
        Veritas<span style={{ WebkitTextFillColor: '#f87171', color: '#f87171' }}>AI</span>
      </h1>
      <p className="hero-subtitle">
        Retrieval-augmented misinformation verification. Extract claims, retrieve evidence, and get explainable verdicts.
      </p>

      {/* Mode Toggle: Text vs File */}
      <div className="mode-toggle">
        <button
          className={`mode-btn ${mode === 'text' ? 'active' : ''}`}
          onClick={() => { setMode('text'); clearFile(); }}
        >
          ✍️ Text / URL
        </button>
        <button
          className={`mode-btn ${mode === 'file' ? 'active' : ''}`}
          onClick={() => setMode('file')}
        >
          📁 Upload File
        </button>
      </div>

      {mode === 'text' ? (
        <>
          {/* Input Type Selector */}
          <div className="input-type-selector">
            {INPUT_TYPES.map(t => (
              <button
                key={t.value}
                className={`input-type-btn ${inputType === t.value ? 'active' : ''}`}
                onClick={() => setInputType(t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Content Type Dropdown */}
          <div className="content-type-row">
            <label className="content-type-label">Content Type:</label>
            <select
              className="content-type-select"
              value={contentType}
              onChange={e => setContentType(e.target.value)}
            >
              {CONTENT_TYPES.map(ct => (
                <option key={ct.value} value={ct.value}>{ct.label}</option>
              ))}
            </select>
          </div>

          <div className="input-wrapper">
            <textarea
              className="article-textarea"
              placeholder={
                inputType === 'url'
                  ? 'Paste a news article URL to analyze (e.g., https://reuters.com/...)'
                  : inputType === 'headline'
                    ? 'Enter a news headline to fact-check...'
                    : inputType === 'social_post'
                      ? 'Paste a social media post to verify...'
                      : 'Paste a news article, headline, or claim to analyze...'
              }
              value={text}
              onChange={e => setText(e.target.value)}
              rows={inputType === 'headline' ? 2 : 5}
            />
            <div className="input-footer">
              <span className="char-count">{text.length} / 10000</span>
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={loading || !canSubmit}
              >
                {loading && <span className="spinner"></span>}
                {loading ? 'Analyzing...' : '🔍 Verify Claims'}
              </button>
            </div>
          </div>

          <div className="sample-row">
            <span className="sample-label">Try samples:</span>
            <button className="sample-pill real" onClick={() => handleSample('credible')}>Credible News</button>
            <button className="sample-pill fake" onClick={() => handleSample('misleading')}>Misleading</button>
            <button className="sample-pill neutral" onClick={() => handleSample('opinion')}>Opinion</button>
            <button className="sample-pill neutral" onClick={() => handleSample('social')}>Social Post</button>
          </div>
        </>
      ) : (
        <div className="file-upload-area">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.docx,.doc,.txt,.text,.md"
            onChange={handleFileChange}
            className="file-input-hidden"
            id="file-upload"
          />

          {!fileObj ? (
            <label htmlFor="file-upload" className="file-drop-zone">
              <div className="file-drop-icon">📄</div>
              <p className="file-drop-title">Click to upload a file</p>
              <p className="file-drop-subtitle">Supports PDF, DOCX, TXT — Max 5MB</p>
            </label>
          ) : (
            <div className="file-selected">
              <div className="file-info">
                <span className="file-icon">
                  {fileName.endsWith('.pdf') ? '📕' : fileName.endsWith('.docx') ? '📘' : '📄'}
                </span>
                <div>
                  <p className="file-name">{fileName}</p>
                  <p className="file-size">{(fileObj.size / 1024).toFixed(1)} KB</p>
                </div>
                <button className="file-remove" onClick={clearFile}>✕</button>
              </div>
              <button
                className="btn-primary btn-full"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading && <span className="spinner"></span>}
                {loading ? 'Analyzing File...' : '🔍 Verify Document'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
