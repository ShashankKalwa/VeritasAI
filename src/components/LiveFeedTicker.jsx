import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

const VERDICT_COLORS = {
  'Credible': '#22c55e',
  'Likely True': '#86efac',
  'Mixed / Misleading': '#eab308',
  'Likely False': '#f97316',
  'False': '#ef4444',
  'Insufficient Evidence': '#94a3b8',
  'Opinion / Not Fact-Checkable': '#6366f1'
};

export default function LiveFeedTicker() {
  const [headlines, setHeadlines] = useState([]);

  useEffect(() => {
    // Initial fetch
    const fetchRecent = async () => {
      try {
        const { data } = await supabase
          .from('analyzed_news')
          .select('id, headline, overall_verdict')
          .order('created_at', { ascending: false })
          .limit(10);
        if (data) setHeadlines(data);
      } catch (err) {
        console.error('Ticker fetch error:', err);
      }
    };
    fetchRecent();

    // Subscribe to new items
    const channel = supabase
      .channel('ticker-updates')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'analyzed_news' },
        (payload) => {
          setHeadlines(prev => [payload.new, ...prev].slice(0, 10));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  if (headlines.length === 0) return null;

  return (
    <div className="ticker-container">
      <div className="ticker-label">
        <span className="live-dot"></span> LIVE
      </div>
      <div className="ticker-wrap">
        <div className="ticker-scroll">
          {/* Duplicate the list to create a seamless infinite loop */}
          {[...headlines, ...headlines].map((item, idx) => {
            const verdict = item.overall_verdict || 'Insufficient Evidence';
            const color = VERDICT_COLORS[verdict] || '#94a3b8';
            return (
              <div key={`${item.id}-${idx}`} className="ticker-item">
                <span className="ticker-badge" style={{ color: color, borderColor: `${color}40` }}>
                  {verdict}
                </span>
                <span className="ticker-text">{item.headline}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
