import { useState, useEffect } from 'react';
import { getMonitorData } from '../api';

export default function Monitor() {
  const [monitorData, setMonitorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchMonitorData();
    const interval = setInterval(fetchMonitorData, 120000);
    return () => clearInterval(interval);
  }, []);

  const fetchMonitorData = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getMonitorData();
      setMonitorData(data);
    } catch (err) {
      console.error('Monitor error:', err);
      setError('Failed to load news. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (!score && score !== 0) return 'var(--text-muted)';
    if (score >= 70) return '#22c55e';
    if (score >= 50) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div>
      <h2 className="analyzer-title" style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '0.5rem' }}>
        📡 Real-Time News Monitor
      </h2>
      <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
        Live analysis of trending news articles
      </p>

      {error && <div className="error-banner">⚠️ {error}</div>}

      {/* Summary Bar */}
      {monitorData && (
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '1.5rem' }}>
          <div className="stat-card">
            <div className="stat-value">{monitorData.analyzed_count || 0}</div>
            <div className="stat-label">Articles Scanned</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              {monitorData.fake_count || 0}
            </div>
            <div className="stat-label">Flagged Fake</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              {monitorData.real_count || 0}
            </div>
            <div className="stat-label">Verified Real</div>
          </div>
        </div>
      )}

      {/* News Cards */}
      {loading && !monitorData ? (
        <div className="monitor-grid">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="news-card">
              <div className="loading-skeleton" style={{ height: 16, width: '40%', marginBottom: 12 }}></div>
              <div className="loading-skeleton" style={{ height: 20, marginBottom: 8 }}></div>
              <div className="loading-skeleton" style={{ height: 14, marginBottom: 4 }}></div>
              <div className="loading-skeleton" style={{ height: 14, width: '80%' }}></div>
            </div>
          ))}
        </div>
      ) : monitorData && monitorData.articles && monitorData.articles.length > 0 ? (
        <div className="monitor-grid">
          {monitorData.articles.map((article, idx) => (
            <div key={idx} className="news-card">
              <div className="news-card-header">
                <span className="news-source">{article.source || 'Unknown'}</span>
                {article.prediction && (
                  <span className={`history-badge ${article.prediction === 'FAKE' ? 'fake' : 'real'}`}>
                    {article.prediction}
                  </span>
                )}
              </div>
              <h3 className="news-title">{article.title || 'Untitled'}</h3>
              {article.description && (
                <p className="news-description">{article.description}</p>
              )}
              <div className="news-footer">
                <span style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  fontFamily: 'var(--font-mono)',
                  color: getScoreColor(article.credibility_score),
                }}>
                  {article.credibility_score != null ? `${article.credibility_score}/100` : 'N/A'}
                </span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {article.confidence ? `${article.confidence.toFixed(1)}% confident` : ''}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : !loading && (
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <p className="empty-state-text">No news articles to monitor right now.</p>
        </div>
      )}

      {/* Refresh Button */}
      <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
        <button className="analyze-btn" onClick={fetchMonitorData} disabled={loading} style={{ maxWidth: 250 }}>
          {loading ? <><span className="spinner"></span> Refreshing...</> : '🔄 Refresh Feed'}
        </button>
      </div>
    </div>
  );
}
