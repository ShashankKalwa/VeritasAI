import { useState } from 'react';
import ArticleInput from '../components/ArticleInput';
import ResultCard from '../components/ResultCard';
import CommunityFeed from '../components/CommunityFeed';
import { analyzeArticle, analyzeFile } from '../lib/api';

export default function DetectPage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (text, file, inputType = 'text', contentType = 'auto') => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      let data;

      if (file) {
        // File upload mode
        data = await analyzeFile(file);
      } else {
        // Text/URL mode
        data = await analyzeArticle(text, inputType, contentType);
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
