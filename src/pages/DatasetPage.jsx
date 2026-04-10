import { useState, useEffect } from 'react';
import { getDataset, getDatasetStats } from '../lib/api';

export default function DatasetPage() {
  const [data, setData] = useState([]);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({ label: 'all', category: 'All', search: '' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const categories = ['All', 'Health', 'Politics', 'Science', 'Business', 'Environment', 'History'];

  useEffect(() => {
    fetchStats();
  }, []);

  useEffect(() => {
    fetchData();
  }, [filters, page]);

  const fetchStats = async () => {
    try {
      const s = await getDatasetStats();
      setStats(s);
    } catch (err) {
      console.error('Dataset stats error:', err);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await getDataset({ ...filters, page, pageSize: 20 });
      setData(result.data);
      setTotalPages(result.totalPages);
      setTotal(result.count);
    } catch (err) {
      console.error('Dataset error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Training Dataset</h1>
        <p className="page-subtitle">Explore 500 labeled headlines used for detection training</p>
      </div>

      {stats && (
        <div className="dataset-stats-bar">
          <span className="ds-stat">
            <strong>{stats.total}</strong> Total Headlines
          </span>
          <span className="ds-stat fake-stat">
            <strong>{stats.fakeCount}</strong> Fake
          </span>
          <span className="ds-stat real-stat">
            <strong>{stats.realCount}</strong> Real
          </span>
          <span className="ds-stat">
            <strong>{stats.categories.length}</strong> Categories
          </span>
        </div>
      )}

      <div className="dataset-filters">
        <div className="filter-group">
          <div className="filter-pills">
            {['all', 'fake', 'real'].map(label => (
              <button
                key={label}
                className={`filter-pill ${filters.label === label ? (label === 'fake' ? 'active-fake' : label === 'real' ? 'active-real' : 'active') : ''}`}
                onClick={() => handleFilterChange('label', label)}
              >
                {label.charAt(0).toUpperCase() + label.slice(1)}
              </button>
            ))}
          </div>

          <div className="filter-pills category-pills">
            {categories.map(cat => (
              <button
                key={cat}
                className={`filter-pill ${filters.category === cat ? 'active' : ''}`}
                onClick={() => handleFilterChange('category', cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <div className="search-input-wrapper">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2">
            <circle cx="11" cy="11" r="8"/>
            <path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder="Search headlines..."
            value={filters.search}
            onChange={e => handleFilterChange('search', e.target.value)}
          />
        </div>
      </div>

      <div className="dataset-table-wrapper">
        {loading ? (
          <div className="loading-state">
            <div className="spinner large"></div>
          </div>
        ) : (
          <>
            <table className="dataset-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Headline</th>
                  <th>Category</th>
                  <th>Label</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {data.map(row => (
                  <tr key={row.id}>
                    <td className="cell-id">{row.id}</td>
                    <td className="cell-headline">{row.headline}</td>
                    <td><span className="category-badge">{row.category}</span></td>
                    <td>
                      <span className={`label-pill ${row.label === 'fake' ? 'label-fake' : 'label-real'}`}>
                        {row.label.toUpperCase()}
                      </span>
                    </td>
                    <td className="cell-source">{row.source || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="pagination">
              <button
                className="btn-page"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ← Prev
              </button>
              <span className="page-info">
                Page {page} of {totalPages} ({total} results)
              </span>
              <button
                className="btn-page"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                Next →
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
