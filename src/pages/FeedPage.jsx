import React, { useState, useEffect } from 'react';
import { getTrendingClaims } from '../lib/api';
import TrendingClaimCard from '../components/TrendingClaimCard';

export default function FeedPage() {
  // Trending State
  const [trendingItems, setTrendingItems] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(true);

  // Fetch initial data
  async function fetchTrending() {
    setTrendingLoading(true);
    try {
      const data = await getTrendingClaims(20);
      setTrendingItems(data || []);
    } catch (err) {
      console.error('Failed to load trending:', err);
    } finally {
      setTrendingLoading(false);
    }
  }

  useEffect(() => {
    fetchTrending();
  }, []);

  return (
    <div className="feed-page">
      <div className="page-header">
        <h1 className="page-title">Trending Claims</h1>
        <p className="page-subtitle">Top factual claims being verified across multiple sources and narratives</p>
      </div>

      <div className="trending-view">
        {trendingLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <span>Analyzing global narratives...</span>
          </div>
        ) : trendingItems.length === 0 ? (
          <div className="empty-state">No trending claims found yet.</div>
        ) : (
          <div className="trending-grid">
            {trendingItems.map(claim => (
              <TrendingClaimCard key={claim.id} claim={claim} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
