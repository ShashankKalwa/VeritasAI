import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ onLoginClick }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { user, signOut } = useAuth();

  const links = [
    { to: '/', label: 'Detect' },
    { to: '/dataset', label: 'Engines' },
    { to: '/dashboard', label: 'Dashboard' },
  ];

  const initials = user?.email ? user.email.substring(0, 2).toUpperCase() : '';

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo" style={{ color: '#fafafa' }}>
          Veritas<span style={{ color: '#f87171' }}>AI</span>
        </Link>

        <div className="navbar-live">
          <span className="live-dot"></span>
          <span className="live-text">LIVE</span>
        </div>

        <div className={`navbar-links ${mobileOpen ? 'open' : ''}`}>
          {links.map(link => (
            <Link
              key={link.to}
              to={link.to}
              className={`nav-link ${location.pathname === link.to ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="nav-auth-mobile">
            {user ? (
              <button className="btn-auth" onClick={signOut}>Sign Out</button>
            ) : (
              <button className="btn-auth" onClick={() => { onLoginClick(); setMobileOpen(false); }}>Login</button>
            )}
          </div>
        </div>

        <div className="navbar-right">
          {user ? (
            <div className="user-menu">
              <div className="user-avatar">{initials}</div>
              <button className="btn-auth btn-signout" onClick={signOut}>Sign Out</button>
            </div>
          ) : (
            <button className="btn-auth" onClick={onLoginClick}>Login</button>
          )}
        </div>

        <button
          className="hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </nav>
  );
}
