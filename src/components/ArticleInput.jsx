import { useState, useRef } from 'react';

const SAMPLES = {
  fake1: "Scientists discover miracle cure suppressed by pharmaceutical companies for decades, whistleblower reveals shocking truth mainstream media refuses to cover",
  fake2: "BREAKING: Government secretly installing 5G towers that cause mind control, leaked documents expose massive cover-up",
  real1: "Federal Reserve holds interest rates steady at 5.25% for third consecutive meeting, citing ongoing inflation data according to Reuters",
  real2: "Study published in Nature confirms new mRNA vaccine shows 94.1% efficacy in Phase 3 clinical trials across 30,000 participants",
};

export default function ArticleInput({ onAnalyze, loading }) {
  const [text, setText] = useState('');
  const [mode, setMode] = useState('text'); // 'text' or 'file'
  const [fileName, setFileName] = useState('');
  const [fileObj, setFileObj] = useState(null);
  const fileRef = useRef(null);

  const handleSubmit = () => {
    if (mode === 'file' && fileObj) {
      onAnalyze(null, fileObj);
    } else if (text.trim().length >= 10) {
      onAnalyze(text, null);
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

  const canSubmit = mode === 'file' ? !!fileObj : text.trim().length >= 10;

  return (
    <div className="article-input-container">
      <h1 className="hero-title">VeritasAI</h1>
      <p className="hero-subtitle">
        Multi-engine AI fake news detection. Paste text or upload a document for instant analysis.
      </p>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          className={`mode-btn ${mode === 'text' ? 'active' : ''}`}
          onClick={() => { setMode('text'); clearFile(); }}
        >
          ✍️ Paste Text
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
          <div className="input-wrapper">
            <textarea
              className="article-textarea"
              placeholder="Paste a news article, headline, or any text to analyze for fake news..."
              value={text}
              onChange={e => setText(e.target.value)}
              rows={5}
            />
            <div className="input-footer">
              <span className="char-count">{text.length} / 5000</span>
              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={loading || !canSubmit}
              >
                {loading && <span className="spinner"></span>}
                {loading ? 'Analyzing...' : '🔍 Analyze Article'}
              </button>
            </div>
          </div>

          <div className="sample-row">
            <span className="sample-label">Try samples:</span>
            <button className="sample-pill fake" onClick={() => setText(SAMPLES.fake1)}>Fake #1</button>
            <button className="sample-pill fake" onClick={() => setText(SAMPLES.fake2)}>Fake #2</button>
            <button className="sample-pill real" onClick={() => setText(SAMPLES.real1)}>Real #1</button>
            <button className="sample-pill real" onClick={() => setText(SAMPLES.real2)}>Real #2</button>
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
                {loading ? 'Analyzing File...' : '🔍 Analyze Document'}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
