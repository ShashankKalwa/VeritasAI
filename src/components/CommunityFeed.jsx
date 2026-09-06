/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
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

const VERDICT_COLORS = {
  'Credible': '#22c55e',
  'Likely True': '#86efac',
  'Mixed / Misleading': '#eab308',
  'Likely False': '#f97316',
  'False': '#ef4444',
  'Insufficient Evidence': '#94a3b8',
  'Opinion / Not Fact-Checkable': '#6366f1',
  // Old labels (backward compat)
  'CREDIBLE': '#22c55e',
  'MOSTLY_TRUE': '#86efac',
  'MIXED': '#eab308',
  'MOSTLY_FALSE': '#f97316',
  'FALSE': '#ef4444',
};

function mapVerdict(verdict) {
  const mapping = {
    'CREDIBLE': 'Credible',
    'MOSTLY_TRUE': 'Likely True',
    'MIXED': 'Mixed',
    'MOSTLY_FALSE': 'Likely False',
    'FALSE': 'False',
    'REAL': 'Credible',
    'FAKE': 'False',
  };
  return mapping[verdict] || verdict;
}

export default function CommunityFeed() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);

  async function fetchRecent() {
    try {
      const { data } = await supabase
        .from('analyzed_news')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(20); // fetch more to ensure we have enough after deduplication

      if (data) {
        const uniqueData = [];
        const seen = new Set();
        for (const item of data) {
          const text = (item.headline || item.input_text || '').trim().substring(0, 50).toLowerCase();
          if (!seen.has(text)) {
            seen.add(text);
            uniqueData.push(item);
            if (uniqueData.length === 10) break;
          }
        }
        setAnalyses(uniqueData);
      } else {
        setAnalyses([]);
      }
    } catch (err) {
      console.error('Feed error:', err);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    // Initial fetch
    fetchRecent();

    const getNormalizedText = (item) => {
      return (item.headline || item.input_text || '').trim().substring(0, 50).toLowerCase();
    };

    // Realtime subscription
    const channel = supabase
      .channel('public-analyzed-news')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'analyzed_news' },
        (payload) => {
          setAnalyses(prev => {
            if (prev.some(item => item.id === payload.new.id)) return prev;
            const newText = getNormalizedText(payload.new);
            if (prev.some(item => getNormalizedText(item) === newText)) return prev;
            return [payload.new, ...prev].slice(0, 10);
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);


  const getVerdict = (item) => {
    const v = item.overall_verdict || item.verdict || 'Insufficient Evidence';
    return mapVerdict(v);
  };

  const getColor = (item) => {
    const v = item.overall_verdict || item.verdict || '';
    return VERDICT_COLORS[v] || '#94a3b8';
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
            <div key={item.id} className="feed-item" onClick={() => setSelectedItem(item)}>
              <div className="feed-item-top">
                <span className="mini-badge" style={{
                  background: getColor(item) + '20',
                  color: getColor(item),
                  borderColor: getColor(item) + '40',
                }}>
                  {getVerdict(item)}
                </span>
                <span className="feed-confidence">
                  {item.overall_confidence || item.confidence || 0}%
                </span>
              </div>
              <p className="feed-text">
                {(item.headline || item.input_text || '').length > 80
                  ? (item.headline || item.input_text).substring(0, 80) + '...'
                  : (item.headline || item.input_text)}
              </p>
              <div className="feed-meta">
                <span className="feed-time">{timeAgo(item.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Feed Detail Modal */}
      {selectedItem && createPortal(
        <div className="feed-modal-overlay" onClick={() => setSelectedItem(null)}>
          <div className="feed-modal-content" onClick={e => e.stopPropagation()}>
            <button className="feed-modal-close" onClick={() => setSelectedItem(null)}>×</button>
            
            <div className="feed-modal-header">
              <span className="mini-badge" style={{
                background: getColor(selectedItem) + '20',
                color: getColor(selectedItem),
                borderColor: getColor(selectedItem) + '40',
              }}>
                {getVerdict(selectedItem)}
              </span>
              <span className="feed-confidence">
                {selectedItem.overall_confidence || selectedItem.confidence || 0}% Confidence
              </span>
            </div>
            
            <h3 className="feed-modal-title">
              {selectedItem.headline || selectedItem.input_text}
            </h3>
            
            {(selectedItem.summary || (selectedItem.explainability && selectedItem.explainability.primary_signal) || selectedItem.analysis) && (
              <div className="feed-modal-section">
                <h4>Analysis Summary</h4>
                <p>{selectedItem.summary || (selectedItem.explainability && selectedItem.explainability.primary_signal) || selectedItem.analysis}</p>
              </div>
            )}

            {selectedItem.top_sources && selectedItem.top_sources.length > 0 && (
              <div className="feed-modal-section">
                <h4>Sources</h4>
                <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-secondary)' }}>
                  {selectedItem.top_sources.map((src, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {typeof src === 'string' ? src : `${src.source_name} - ${src.stance}`}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {selectedItem.source_url && (
              <div className="feed-modal-section" style={{ background: 'transparent', border: 'none', padding: '0', marginBottom: '0' }}>
                <a href={selectedItem.source_url} target="_blank" rel="noreferrer" className="feed-modal-link">
                  View Original Source ↗
                </a>
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
