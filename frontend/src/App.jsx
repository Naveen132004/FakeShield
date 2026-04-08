import { useState } from 'react';
import Navbar from './components/Navbar';
import Analyzer from './components/Analyzer';
import Dashboard from './components/Dashboard';
import History from './components/History';
import Monitor from './components/Monitor';
import './index.css';

function App() {
  const [activePage, setActivePage] = useState('analyzer');

  const renderPage = () => {
    switch (activePage) {
      case 'analyzer':
        return <Analyzer />;
      case 'dashboard':
        return <Dashboard />;
      case 'history':
        return <History />;
      case 'monitor':
        return <Monitor />;
      default:
        return <Analyzer />;
    }
  };

  return (
    <div className="app">
      <Navbar activePage={activePage} onNavigate={setActivePage} />
      <main className="app-content">
        {renderPage()}
      </main>
    </div>
  );
}

export default App;
