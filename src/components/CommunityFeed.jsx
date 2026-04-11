import { useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';

function timeAgo(dateStr) {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function CommunityFeed() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial fetch
    fetchRecent();

    // Realtime subscription
    const channel = supabase
      .channel('public-analyses')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'analyses' },
        (payload) => {
          setAnalyses(prev => [payload.new, ...prev].slice(0, 10));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const fetchRecent = async () => {
    try {
      const { data } = await supabase
        .from('analyses')
        .select('*')
        .eq('is_public', true)
        .order('created_at', { ascending: false })
        .limit(10);
      setAnalyses(data || []);
    } catch (err) {
      console.error('Feed error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="community-feed">
      <div className="feed-header">
        <h3>
          <span className="live-dot"></span>
          Live Detection Feed
        </h3>
      </div>

      {loading ? (
        <div className="feed-skeleton">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton-item">
              <div className="skeleton-badge"></div>
              <div className="skeleton-text"></div>
              <div className="skeleton-text short"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="feed-list">
          {analyses.map((item) => (
            <div key={item.id} className="feed-item">
              <div className="feed-item-top">
                <span className={`mini-badge ${
                  item.verdict === 'FAKE' ? 'badge-fake' :
                  item.verdict === 'MISLEADING' ? 'badge-misleading' :
                  item.verdict === 'PARTIALLY_TRUE' ? 'badge-partial' :
                  item.verdict === 'UNCERTAIN' ? 'badge-uncertain' :
                  'badge-real'
                }`}>
                  {item.verdict === 'PARTIALLY_TRUE' ? 'PARTIAL' : item.verdict}
                </span>
                <span className="feed-confidence">{item.confidence}%</span>
              </div>
              <p className="feed-text">
                {item.input_text.length > 80
                  ? item.input_text.substring(0, 80) + '...'
                  : item.input_text}
              </p>
              <span className="feed-time">{timeAgo(item.created_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
