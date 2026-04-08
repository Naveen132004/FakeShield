import { useState, useEffect } from 'react';
import { getHistory } from '../api';

export default function History() {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getHistory();
      setHistory(data);
    } catch (err) {
      console.error('History error:', err);
      setError('Failed to load history. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#84cc16';
    if (score >= 40) return '#f59e0b';
    if (score >= 20) return '#ef4444';
    return '#dc2626';
  };

  const items = history?.items || [];
  const total = history?.total || 0;

  return (
    <div>
      <h2 className="analyzer-title" style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '1.5rem' }}>
        📋 Analysis History
      </h2>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {loading && !history ? (
        <div className="history-list">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="history-item">
              <div className="loading-skeleton" style={{ height: 20, flex: 1 }}></div>
              <div className="loading-skeleton" style={{ height: 24, width: 80, marginLeft: 16 }}></div>
            </div>
          ))}
        </div>
      ) : items.length > 0 ? (
        <>
          <div className="card" style={{ marginBottom: '1rem', textAlign: 'center' }}>
            <span style={{ color: 'var(--text-secondary)' }}>
              Total Records: <strong style={{ color: 'var(--accent-secondary)', fontFamily: 'var(--font-mono)' }}>{total}</strong>
            </span>
          </div>
          <div className="history-list">
            {items.map((item, idx) => (
              <div key={idx} className="history-item">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="history-text">{item.text_preview || 'No preview available'}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {item.analyzed_at ? new Date(item.analyzed_at).toLocaleString() : '—'}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                  <span style={{
                    fontSize: '0.85rem', fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: getScoreColor(item.credibility_score),
                  }}>
                    {item.credibility_score}/100
                  </span>
                  <span className={`history-badge ${item.prediction === 'FAKE' ? 'fake' : 'real'}`}>
                    {item.prediction}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p className="empty-state-text">
            No analysis history yet. Go to the <strong>Analyzer</strong> to start checking news!
          </p>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
          <button className="analyze-btn" onClick={fetchHistory} disabled={loading} style={{ maxWidth: 250 }}>
            {loading ? <><span className="spinner"></span> Refreshing...</> : '🔄 Refresh'}
          </button>
        </div>
      )}
    </div>
  );
}
