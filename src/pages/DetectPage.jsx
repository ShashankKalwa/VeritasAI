import { useState } from 'react';
import ArticleInput from '../components/ArticleInput';
import ResultCard from '../components/ResultCard';
import CommunityFeed from '../components/CommunityFeed';
import { analyzeArticle } from '../lib/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function DetectPage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (text, file) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      let data;

      if (file) {
        // File upload mode
        const formData = new FormData();
        formData.append('file', file);

        const resp = await fetch(`${API_URL}/api/analyze/file`, {
          method: 'POST',
          body: formData,
        });

        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.detail || 'File analysis failed');
        }
        data = await resp.json();
      } else {
        // Text mode
        data = await analyzeArticle(text);
      }

      setResult(data);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="detect-page">
      <div className="detect-main">
        <ArticleInput onAnalyze={handleAnalyze} loading={loading} />
        {error && <div className="error-banner">⚠️ {error}</div>}
        <ResultCard result={result} />
      </div>
      <CommunityFeed />
    </div>
  );
}
