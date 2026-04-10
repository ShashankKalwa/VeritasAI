import { useState } from 'react';
import ArticleInput from '../components/ArticleInput';
import ResultCard from '../components/ResultCard';
import CommunityFeed from '../components/CommunityFeed';
import { analyzeArticle } from '../lib/api';

export default function DetectPage() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (text) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const analysisResult = await analyzeArticle(text);
      setResult({ ...analysisResult, input_text: text });
    } catch (err) {
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="detect-page">
      <div className="detect-main">
        <ArticleInput onAnalyze={handleAnalyze} isLoading={loading} />

        {error && (
          <div className="error-banner">
            <span>⚠</span> {error}
          </div>
        )}

        <ResultCard result={result} />
      </div>

      <aside className="detect-sidebar">
        <CommunityFeed />
      </aside>
    </div>
  );
}
