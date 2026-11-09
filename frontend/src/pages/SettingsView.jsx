import React from 'react';

export default function SettingsView({ backendStatus }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>⚙️ System Settings & Security</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Provider connections, model configuration, and confidential environment variables.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '20px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#0f172a' }}>FastAPI Backend Status</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: '#334155' }}>
            <div><strong>Status:</strong> {backendStatus?.status === 'healthy' ? '🟢 Online & Healthy' : '🔴 Offline'}</div>
            <div><strong>Database Engine:</strong> SQLite (leadpilot.db)</div>
            <div><strong>Host / Port:</strong> 0.0.0.0:8000</div>
            <div><strong>Active Sprint:</strong> CP-06 — Interactive Dashboard</div>
          </div>
        </div>

        <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', padding: '20px' }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#0f172a' }}>AI & Speech Engine</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: '#334155' }}>
            <div><strong>LLM Providers:</strong> Google Gemini API & Groq LLaMA</div>
            <div><strong>Speech Recognition (STT):</strong> Web Speech API & Groq Whisper-Large-v3</div>
            <div><strong>Speech Generation (TTS):</strong> Web SpeechSynthesis Engine</div>
            <div><strong>Supported Languages:</strong> English, Hindi (हिंदी), Telugu (తెలుగు)</div>
          </div>
        </div>
      </div>

      <div style={{ backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '16px', fontSize: '13px', color: '#166534', lineHeight: '1.6' }}>
        <strong>🔒 Confidentiality & Security Standard:</strong>
        <ul style={{ margin: '6px 0 0 0', paddingLeft: '20px' }}>
          <li>API keys are stored exclusively in <code>backend/.env</code> and never exposed to client-side bundles.</li>
          <li>All secret tokens, local SQLite databases, customer audio files, and transcripts are ignored by <code>.gitignore</code>.</li>
        </ul>
      </div>
    </div>
  );
}

