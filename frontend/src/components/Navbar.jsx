export default function Navbar({ activePage, onNavigate }) {
  const pages = [
    { id: 'analyzer', label: 'Analyze', icon: '🔍' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'history', label: 'History', icon: '📋' },
    { id: 'monitor', label: 'Monitor', icon: '📡' },
  ];

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <div className="navbar-brand" onClick={() => onNavigate('analyzer')} style={{ cursor: 'pointer' }}>
          <div className="navbar-logo">🛡️</div>
          <div>
            <div className="navbar-title">FakeShield</div>
            <div className="navbar-subtitle">AI-Powered News Verification</div>
          </div>
        </div>
        <div className="navbar-nav">
          {pages.map((page) => (
            <button
              key={page.id}
              className={`nav-link ${activePage === page.id ? 'active' : ''}`}
              onClick={() => onNavigate(page.id)}
            >
              {page.icon} {page.label}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
