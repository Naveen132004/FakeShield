import { useState } from 'react';
import { predictText, predictURL } from '../api';

export default function Analyzer() {
  const [activeTab, setActiveTab] = useState('text');
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    setError('');
    setResult(null);

    if (activeTab === 'text' && text.trim().length < 10) {
      setError('Please enter at least 10 characters of text to analyze.');
      return;
    }
    if (activeTab === 'url' && !url.trim()) {
      setError('Please enter a valid URL.');
      return;
    }

    setLoading(true);
    try {
      let data;
      if (activeTab === 'text') {
        data = await predictText(text);
      } else {
        data = await predictURL(url);
      }
      setResult(data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Analysis failed. Make sure backend is running.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const getGaugeColor = (score) => {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#84cc16';
    if (score >= 40) return '#f59e0b';
    if (score >= 20) return '#ef4444';
    return '#dc2626';
  };

  const getGaugeLabel = (score) => {
    if (score >= 80) return 'Highly Credible';
    if (score >= 60) return 'Likely Credible';
    if (score >= 40) return 'Uncertain';
    if (score >= 20) return 'Likely Fake';
    return 'Highly Suspicious';
  };

  return (
    <div className="analyzer">
      <div className="analyzer-header">
        <h1 className="analyzer-title">Fake News Detector</h1>
        <p className="analyzer-description">
          Paste any news article or URL to instantly analyze its credibility using AI
        </p>
      </div>

      <div className="card">
        {/* Tab Switcher */}
        <div className="tab-switcher">
          <button
            className={`tab-btn ${activeTab === 'text' ? 'active' : ''}`}
            onClick={() => { setActiveTab('text'); setError(''); setResult(null); }}
          >
            📝 Analyze Text
          </button>
          <button
            className={`tab-btn ${activeTab === 'url' ? 'active' : ''}`}
            onClick={() => { setActiveTab('url'); setError(''); setResult(null); }}
          >
            🔗 Analyze URL
          </button>
        </div>

        {/* Input */}
        {activeTab === 'text' ? (
          <div className="input-group">
            <label className="input-label">News Article Text</label>
            <textarea
              className="text-input"
              placeholder="Paste the news article text here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={6}
            />
            <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              {text.length} characters
            </div>
          </div>
        ) : (
          <div className="input-group">
            <label className="input-label">Article URL</label>
            <input
              className="url-input"
              type="url"
              placeholder="https://example.com/news/article"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {/* Analyze Button */}
        <button
          className={`analyze-btn ${loading ? 'loading' : ''}`}
          onClick={handleAnalyze}
          disabled={loading}
        >
          {loading ? (
            <><span className="spinner"></span> Analyzing...</>
          ) : (
            '🔍 Analyze Now'
          )}
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="results">
          {/* Verdict */}
          <div className={`result-verdict ${result.prediction === 'FAKE' ? 'fake' : 'real'}`}>
            <div className="verdict-icon">
              {result.prediction === 'FAKE' ? '🚨' : '✅'}
            </div>
            <div className={`verdict-label ${result.prediction === 'FAKE' ? 'fake' : 'real'}`}>
              {result.prediction === 'FAKE' ? 'LIKELY FAKE NEWS' : 'LIKELY REAL NEWS'}
            </div>
            <div className="verdict-confidence">
              {result.confidence}% confidence
            </div>
          </div>

          {/* Credibility Score - Big Visual */}
          <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '0.5rem' }}>
              Credibility Score
            </div>
            <div style={{
              width: 140, height: 140, margin: '0 auto',
              borderRadius: '50%',
              background: `conic-gradient(${getGaugeColor(result.credibility_score)} ${result.credibility_score}%, var(--bg-secondary) ${result.credibility_score}%)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: `0 0 30px ${getGaugeColor(result.credibility_score)}33`,
            }}>
              <div style={{
                width: 100, height: 100, borderRadius: '50%',
                background: 'var(--bg-card)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexDirection: 'column',
              }}>
                <div style={{
                  fontSize: '2rem', fontWeight: 800,
                  fontFamily: 'var(--font-mono)',
                  color: getGaugeColor(result.credibility_score),
                }}>
                  {result.credibility_score}
                </div>
                <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)' }}>/ 100</div>
              </div>
            </div>
            <div style={{ marginTop: '0.75rem', fontWeight: 600, color: getGaugeColor(result.credibility_score), fontSize: '1.1rem' }}>
              {result.credibility_level || getGaugeLabel(result.credibility_score)}
            </div>
          </div>

          {/* Probability Bars */}
          <div className="card" style={{ marginTop: '1rem' }}>
            <div className="card-title" style={{ marginBottom: '1rem' }}>📊 Probability Breakdown</div>
            
            {/* Fake Probability */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>🔴 Fake Probability</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#ef4444', fontFamily: 'var(--font-mono)' }}>
                  {result.fake_probability}%
                </span>
              </div>
              <div style={{ height: 8, background: 'var(--bg-secondary)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 4,
                  width: `${result.fake_probability}%`,
                  background: 'linear-gradient(90deg, #ef4444, #dc2626)',
                  transition: 'width 1s ease',
                }}></div>
              </div>
            </div>

            {/* Real Probability */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>🟢 Real Probability</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#22c55e', fontFamily: 'var(--font-mono)' }}>
                  {result.real_probability}%
                </span>
              </div>
              <div style={{ height: 8, background: 'var(--bg-secondary)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 4,
                  width: `${result.real_probability}%`,
                  background: 'linear-gradient(90deg, #22c55e, #16a34a)',
                  transition: 'width 1s ease',
                }}></div>
              </div>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="metrics-grid" style={{ marginTop: '1rem' }}>
            <div className="metric-card">
              <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>
                {result.text_length}
              </div>
              <div className="metric-label">Characters</div>
            </div>
            <div className="metric-card">
              <div className="metric-value" style={{ color: result.prediction === 'FAKE' ? '#ef4444' : '#22c55e' }}>
                {result.confidence}%
              </div>
              <div className="metric-label">Confidence</div>
            </div>
            <div className="metric-card">
              <div className="metric-value" style={{ color: getGaugeColor(result.credibility_score) }}>
                {result.credibility_score}/100
              </div>
              <div className="metric-label">Credibility</div>
            </div>
          </div>

          {/* Suspicious Words */}
          {result.suspicious_words && result.suspicious_words.length > 0 && (
            <div className="card" style={{ marginTop: '1rem' }}>
              <div className="card-title">🔑 Key Words Influencing Decision</div>
              <div className="word-list">
                {result.suspicious_words.map((word, idx) => (
                  <span
                    key={idx}
                    className={`word-tag ${word.direction}`}
                    title={`Importance: ${word.importance}, TF-IDF: ${word.tfidf_score}`}
                  >
                    {word.direction === 'fake' ? '🔴' : '🟢'} {word.word}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* URL-specific Info */}
          {result.extracted_title && (
            <div className="card" style={{ marginTop: '1rem' }}>
              <div className="card-title">📰 Extracted Article</div>
              <p style={{ color: 'var(--text-primary)', marginTop: '0.5rem', fontWeight: 600 }}>
                {result.extracted_title}
              </p>
              <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem', fontSize: '0.85rem' }}>
                Domain: <strong>{result.source_domain}</strong> | 
                Extracted: <strong>{result.extracted_text_length}</strong> characters
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
