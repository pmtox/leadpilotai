import React, { useEffect, useState } from 'react';
import {
  checkBackendHealth,
  fetchCurrentUser,
  logout,
  updateProfile,
} from './services/api';
import AIWorkspace from './pages/AIWorkspace';
import ActionCenterView from './pages/ActionCenterView';
import CustomersView from './pages/CustomersView';
import GoogleLoginView from './pages/GoogleLoginView';
import ProfileView from './pages/ProfileView';
import './App.css';

function App() {
  const [profile, setProfile] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authError, setAuthError] = useState('');
  const [backendStatus, setBackendStatus] = useState('checking');
  const [activeSection, setActiveSection] = useState('ai');

  useEffect(() => {
    fetchCurrentUser()
      .then(setProfile)
      .catch((error) => setAuthError(error.message || 'Could not load your account.'))
      .finally(() => setAuthLoading(false));
    checkBackendHealth().then((health) => setBackendStatus(health.status));
  }, []);

  async function handleProfileSave(changes) {
    const updatedProfile = await updateProfile(changes);
    setProfile(updatedProfile);
  }

  async function handleLogout() {
    try {
      await logout();
      setProfile(null);
      setActiveSection('ai');
    } catch (error) {
      setAuthError(error.message || 'Could not sign out.');
    }
  }

  if (authLoading) {
    return (
      <main className="loading-screen" aria-live="polite">
        <div className="brand-mark" aria-hidden="true">L</div>
        <p>Loading your workspace…</p>
      </main>
    );
  }

  if (!profile) {
    return <GoogleLoginView initialError={authError} />;
  }

  const isAdmin = profile.role === 'admin';
  const sections = [
    { id: 'ai', label: 'AI Assistant', icon: '✦' },
    ...(isAdmin ? [
      { id: 'customers', label: 'Customers', icon: '◉' },
      { id: 'actions', label: 'Action Center', icon: '↗' },
    ] : []),
    { id: 'profile', label: 'Profile', icon: '○' },
  ];

  return (
    <div className="app-shell">
      <header className="app-header">
        <a className="brand" href="/" aria-label="LeadPilot AI home">
          <span className="brand-mark" aria-hidden="true">L</span>
          <span>
            <strong>LeadPilot</strong>
            <small>AI workspace</small>
          </span>
        </a>

        <div className="header-account">
          <span className={`service-status ${backendStatus === 'healthy' ? 'service-online' : ''}`}>
            <span aria-hidden="true" />
            {backendStatus === 'healthy' ? 'All systems ready' : backendStatus === 'checking' ? 'Connecting…' : 'Service unavailable'}
          </span>
          <div className="account-summary">
            {profile.picture ? (
              <img className="avatar" src={profile.picture} alt="" referrerPolicy="no-referrer" />
            ) : (
              <span className="avatar avatar-fallback" aria-hidden="true">
                {profile.name?.slice(0, 1)?.toUpperCase() || 'U'}
              </span>
            )}
            <div className="account-name">
              <strong>{profile.name}</strong>
              {isAdmin && <span className="role-badge role-admin">Admin</span>}
            </div>
            <button className="signout-button" type="button" onClick={handleLogout}>Sign out</button>
          </div>
        </div>
      </header>

      <nav className="main-nav" aria-label="Main navigation">
        {sections.map((section) => (
          <button
            aria-current={activeSection === section.id ? 'page' : undefined}
            className={activeSection === section.id ? 'nav-item nav-item-active' : 'nav-item'}
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            type="button"
          >
            <span aria-hidden="true">{section.icon}</span>
            {section.label}
          </button>
        ))}
      </nav>

      <main className="main-content">
        <div className={activeSection === 'ai' ? '' : 'hidden-section'}>
          <AIWorkspace key={profile.preferred_language} profile={profile} adminMode={isAdmin} />
        </div>
        {isAdmin && activeSection === 'customers' && <CustomersView />}
        {isAdmin && activeSection === 'actions' && <ActionCenterView />}
        {activeSection === 'profile' && (
          <ProfileView profile={profile} onSave={handleProfileSave} />
        )}
      </main>
      <footer className="app-footer">
        <span>LeadPilot AI</span>
        <span>Your ideas, thoughtfully planned.</span>
      </footer>
    </div>
  );
}

export default App;
