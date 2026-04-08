import { useState, useEffect, useCallback } from 'react';
import { getDashboard, getHealth } from '../api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [dashData, healthData] = await Promise.all([
        getDashboard(),
        getHealth(),
      ]);
      setStats(dashData);
      setHealth(healthData);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError('Failed to load dashboard. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading && !stats) {
    return (
      <div className="dashboard">
        <h2 className="analyzer-title" style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          📊 Dashboard
        </h2>
        <div className="stats-grid">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="stat-card">
              <div className="loading-skeleton" style={{ height: 60, marginBottom: 8 }}></div>
              <div className="loading-skeleton" style={{ height: 16, width: '60%', margin: '0 auto' }}></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="dashboard">
        <h2 className="analyzer-title" style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '1.5rem' }}>
          📊 Dashboard
        </h2>
        <div className="error-banner">⚠️ {error}</div>
        <button className="analyze-btn" onClick={fetchData} style={{ maxWidth: 250, margin: '1rem auto', display: 'block' }}>
          🔄 Retry Connection
        </button>
      </div>
    );
  }

  const total = stats?.total_analyzed || 0;
  const fakeCount = stats?.fake_count || 0;
  const realCount = stats?.real_count || 0;
  const avgCred = stats?.average_credibility || 0;
  const fakePercent = total > 0 ? Math.round((fakeCount / total) * 100) : 0;
  const realPercent = total > 0 ? Math.round((realCount / total) * 100) : 0;

  return (
    <div className="dashboard">
      <h2 className="analyzer-title" style={{ fontSize: '1.8rem', textAlign: 'center', marginBottom: '1.5rem' }}>
        📊 Dashboard
      </h2>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📰</div>
          <div className="stat-value">{total}</div>
          <div className="stat-label">Total Analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🚨</div>
          <div className="stat-value" style={{ background: 'linear-gradient(135deg, #ef4444, #dc2626)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            {fakeCount}
          </div>
          <div className="stat-label">Fake Detected</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-value" style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            {realCount}
          </div>
          <div className="stat-label">Real Verified</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{avgCred}</div>
          <div className="stat-label">Avg Credibility</div>
        </div>
      </div>

      {/* Distribution Chart (CSS Donut) */}
      {total > 0 && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-title" style={{ marginBottom: '1.5rem' }}>
            📊 Fake vs Real Distribution
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '3rem', flexWrap: 'wrap' }}>
            {/* CSS Donut Chart */}
            <div style={{
              width: 180, height: 180, borderRadius: '50%',
              background: `conic-gradient(#ef4444 0% ${fakePercent}%, #22c55e ${fakePercent}% 100%)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              position: 'relative',
            }}>
              <div style={{
                width: 110, height: 110, borderRadius: '50%',
                background: 'var(--bg-card)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexDirection: 'column',
              }}>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                  {total}
                </div>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Total
                </div>
              </div>
            </div>
            
            {/* Legend */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ width: 16, height: 16, borderRadius: 4, background: '#ef4444' }}></div>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Fake News</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {fakeCount} articles ({fakePercent}%)
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ width: 16, height: 16, borderRadius: 4, background: '#22c55e' }}></div>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Real News</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    {realCount} articles ({realPercent}%)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Credibility Distribution Bar */}
      {total > 0 && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-title" style={{ marginBottom: '1rem' }}>
            🎯 Credibility Overview
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end', height: 60 }}>
            <div style={{ flex: fakeCount || 1, background: 'linear-gradient(180deg, #ef4444, #dc2626)', borderRadius: '6px 6px 0 0', minHeight: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.25rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'white' }}>{fakePercent}% Fake</span>
            </div>
            <div style={{ flex: realCount || 1, background: 'linear-gradient(180deg, #22c55e, #16a34a)', borderRadius: '6px 6px 0 0', minHeight: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0.25rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'white' }}>{realPercent}% Real</span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            <span>Average Credibility Score: <strong style={{ color: avgCred >= 60 ? '#22c55e' : avgCred >= 40 ? '#f59e0b' : '#ef4444' }}>{avgCred}/100</strong></span>
          </div>
        </div>
      )}

      {/* System Health */}
      {health && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>⚙️ System Status</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem' }}>{health.status === 'healthy' ? '🟢' : '🔴'}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {health.status === 'healthy' ? 'Online' : 'Offline'}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem' }}>{health.model_loaded ? '🧠' : '❌'}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                {health.model_loaded ? 'ML Model Loaded' : 'Model Missing'}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.9rem', fontFamily: 'var(--font-mono)', color: 'var(--accent-secondary)', fontWeight: 600 }}>
                v{health.version}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                API Version
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Analyses */}
      {stats?.recent_analyses && stats.recent_analyses.length > 0 && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>🕐 Recent Analyses</div>
          <div className="history-list">
            {stats.recent_analyses.map((item, idx) => (
              <div key={idx} className="history-item">
                <span className="history-text">{item.text_preview || 'No preview available'}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                  <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: item.credibility_score >= 50 ? '#22c55e' : '#ef4444' }}>
                    {item.credibility_score}/100
                  </span>
                  <span className={`history-badge ${item.prediction === 'FAKE' ? 'fake' : 'real'}`}>
                    {item.prediction}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {total === 0 && (
        <div className="empty-state" style={{ marginTop: '2rem' }}>
          <div className="empty-state-icon">📊</div>
          <p className="empty-state-text">
            No analyses yet. Go to the <strong>Analyzer</strong> page to start checking news articles!
          </p>
        </div>
      )}
    </div>
  );
}
