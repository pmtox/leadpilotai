import React, { useState, useEffect } from 'react';
import { checkBackendHealth } from './services/api';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verifyConnection() {
      try {
        const data = await checkBackendHealth();
        setBackendStatus(data);
      } catch (err) {
        setBackendStatus({ status: 'offline', error: err.message });
      } finally {
        setLoading(false);
      }
    }
    verifyConnection();
  }, []);

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', maxWidth: '800px', margin: '40px auto', padding: '24px', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}>
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '16px', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, color: '#0f172a', fontSize: '28px' }}>🚀 LeadPilot AI</h1>
        <p style={{ margin: '6px 0 0 0', color: '#64748b' }}>Autonomous Multilingual AI Sales Agent</p>
      </header>

      <section style={{ backgroundColor: '#f8fafc', padding: '16px', borderRadius: '8px', marginBottom: '24px' }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#1e293b' }}>Sprint Status: Checkpoint CP-01 (Project Foundation)</h3>
        <ul style={{ margin: 0, paddingLeft: '20px', color: '#334155', lineHeight: '1.8' }}>
          <li>✅ Git repository initialized with protected <code>.gitignore</code></li>
          <li>✅ FastAPI backend operational with SQLite persistence</li>
          <li>✅ React + Vite frontend scaffolded & configured</li>
          <li>✅ Multilingual data models & schemas initialized (English, Hindi, Telugu)</li>
        </ul>
      </section>

      <section style={{ padding: '16px', border: '1px solid #cbd5e1', borderRadius: '8px' }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#334155' }}>Backend Connectivity Status:</h4>
        {loading ? (
          <p style={{ color: '#64748b' }}>Checking backend health...</p>
        ) : backendStatus?.status === 'healthy' ? (
          <div style={{ color: '#166534', backgroundColor: '#dcfce7', padding: '10px 14px', borderRadius: '6px', fontWeight: '500' }}>
            🟢 Backend Connected: {backendStatus.database} (SQLite Ready)
          </div>
        ) : (
          <div style={{ color: '#991b1b', backgroundColor: '#fee2e2', padding: '10px 14px', borderRadius: '6px' }}>
            🔴 Backend Offline: Run backend uvicorn server on port 8000
          </div>
        )}
      </section>
    </div>
  );
}

export default App;
