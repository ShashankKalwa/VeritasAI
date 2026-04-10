import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import AuthModal from './components/AuthModal';
import DetectPage from './pages/DetectPage';
import DatasetPage from './pages/DatasetPage';
import DashboardPage from './pages/DashboardPage';

function App() {
  const [showAuth, setShowAuth] = useState(false);

  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Navbar onLoginClick={() => setShowAuth(true)} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<DetectPage />} />
              <Route path="/dataset" element={<DatasetPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
            </Routes>
          </main>
          <AuthModal isOpen={showAuth} onClose={() => setShowAuth(false)} />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
