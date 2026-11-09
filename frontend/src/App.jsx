import React, { useState, useEffect, useRef } from 'react';
import {
  checkBackendHealth,
  createCustomer,
  startConversation,
  sendMessage,
  endConversation
} from './services/api';
import './App.css';

function App() {
  const [backendStatus, setBackendStatus] = useState(null);
  const [customerName, setCustomerName] = useState('Priya Sharma');
  const [customerPhone, setCustomerPhone] = useState('+919876543210');
  const [language, setLanguage] = useState('English');
  const [conversation, setConversation] = useState(null);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [healthLoading, setHealthLoading] = useState(true);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    async function verifyConnection() {
      try {
        const data = await checkBackendHealth();
        setBackendStatus(data);
      } catch (err) {
        setBackendStatus({ status: 'offline', error: err.message });
      } finally {
        setHealthLoading(false);
      }
    }
    verifyConnection();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages]);

  async function handleStartConversation(e) {
    e.preventDefault();
    setLoading(true);
    try {
      // 1. Create or register customer
      const cust = await createCustomer({
        name: customerName,
        phone: customerPhone,
        preferred_language: language,
      });

      // 2. Start conversation
      const conv = await startConversation(cust.id, language);
      setConversation(conv);
    } catch (err) {
      alert(`Error starting conversation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleSendMessage(e) {
    e.preventDefault();
    if (!inputText.trim() || !conversation) return;

    const text = inputText.trim();
    setInputText('');
    setLoading(true);

    try {
      const updatedConv = await sendMessage(conversation.id, text, language);
      setConversation(updatedConv);
    } catch (err) {
      alert(`Error sending message: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function handleEndConversation() {
    if (!conversation) return;
    setLoading(true);
    try {
      const ended = await endConversation(conversation.id);
      setConversation(ended);
    } catch (err) {
      alert(`Error ending conversation: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', maxWidth: '850px', margin: '30px auto', padding: '24px', backgroundColor: '#ffffff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '16px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0f172a', fontSize: '26px' }}>🚀 LeadPilot AI</h1>
          <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>Autonomous Multilingual AI Sales Agent</p>
        </div>
        <div>
          {healthLoading ? (
            <span style={{ fontSize: '13px', color: '#64748b' }}>Checking backend...</span>
          ) : backendStatus?.status === 'healthy' ? (
            <span style={{ backgroundColor: '#dcfce7', color: '#166534', padding: '6px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: '600' }}>
              ● Backend Ready
            </span>
          ) : (
            <span style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '6px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: '600' }}>
              ○ Backend Offline
            </span>
          )}
        </div>
      </header>

      {/* Checkpoint Banner */}
      <div style={{ backgroundColor: '#f1f5f9', borderLeft: '4px solid #2563eb', padding: '12px 16px', borderRadius: '4px', marginBottom: '20px', fontSize: '14px', color: '#334155' }}>
        <strong>Checkpoint CP-02: LLM Conversation Engine</strong> — Multilingual dialogue active in English, Hindi (हिंदी), and Telugu (తెలుగు).
      </div>

      {/* Customer Setup Form (if no active conversation) */}
      {!conversation ? (
        <form onSubmit={handleStartConversation} style={{ backgroundColor: '#fafafa', padding: '20px', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '17px', color: '#1e293b' }}>Initiate Customer Interaction</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#475569' }}>Customer Name</label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#475569' }}>Phone Number</label>
              <input
                type="text"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                required
                style={{ width: '100%', padding: '8px 12px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: '600', color: '#475569' }}>Preferred Language</label>
            <div style={{ display: 'flex', gap: '12px' }}>
              {['English', 'Hindi', 'Telugu'].map((lang) => (
                <button
                  type="button"
                  key={lang}
                  onClick={() => setLanguage(lang)}
                  style={{
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: language === lang ? '2px solid #2563eb' : '1px solid #cbd5e1',
                    backgroundColor: language === lang ? '#eff6ff' : '#ffffff',
                    color: language === lang ? '#1d4ed8' : '#334155',
                    fontWeight: language === lang ? '600' : '400',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  {lang === 'English' ? 'English' : lang === 'Hindi' ? 'हिंदी (Hindi)' : 'తెలుగు (Telugu)'}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              backgroundColor: '#2563eb',
              color: '#ffffff',
              padding: '10px 20px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: '600',
              fontSize: '14px',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {loading ? 'Starting...' : 'Start AI Sales Conversation →'}
          </button>
        </form>
      ) : (
        /* Conversation Interface */
        <div style={{ display: 'flex', flexDirection: 'column', height: '520px', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
          {/* Chat Topbar */}
          <div style={{ backgroundColor: '#f8fafc', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontWeight: '600', color: '#1e293b' }}>{customerName}</span>
              <span style={{ marginLeft: '8px', color: '#64748b', fontSize: '13px' }}>({language})</span>
              <span style={{ marginLeft: '12px', fontSize: '12px', padding: '2px 8px', borderRadius: '10px', backgroundColor: conversation.status === 'active' ? '#dcfce7' : '#f1f5f9', color: conversation.status === 'active' ? '#166534' : '#64748b' }}>
                {conversation.status.toUpperCase()}
              </span>
            </div>
            {conversation.status === 'active' && (
              <button
                onClick={handleEndConversation}
                disabled={loading}
                style={{ padding: '6px 12px', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
              >
                End Conversation
              </button>
            )}
          </div>

          {/* Messages Scroll Area */}
          <div style={{ flex: 1, padding: '16px', overflowY: 'auto', backgroundColor: '#fbfcfd' }}>
            {conversation.messages?.map((msg) => {
              const isAgent = msg.speaker === 'agent';
              return (
                <div
                  key={msg.id}
                  style={{
                    display: 'flex',
                    justifyContent: isAgent ? 'flex-start' : 'flex-end',
                    marginBottom: '12px',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '75%',
                      padding: '10px 14px',
                      borderRadius: isAgent ? '12px 12px 12px 2px' : '12px 12px 2px 12px',
                      backgroundColor: isAgent ? '#ffffff' : '#2563eb',
                      color: isAgent ? '#1e293b' : '#ffffff',
                      border: isAgent ? '1px solid #e2e8f0' : 'none',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                      fontSize: '14px',
                      lineHeight: '1.5'
                    }}
                  >
                    <div style={{ fontSize: '11px', marginBottom: '4px', opacity: 0.7, fontWeight: '600' }}>
                      {isAgent ? '🤖 LeadPilot AI' : `👤 ${customerName}`}
                    </div>
                    {msg.content}
                  </div>
                </div>
              );
            })}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '12px' }}>
                <div style={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '8px 12px', fontSize: '13px', color: '#64748b' }}>
                  LeadPilot AI is thinking...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Turn Bar */}
          {conversation.status === 'active' ? (
            <form onSubmit={handleSendMessage} style={{ display: 'flex', padding: '12px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0', gap: '8px' }}>
              <input
                type="text"
                placeholder={language === 'Hindi' ? "अपना संदेश यहाँ लिखें..." : language === 'Telugu' ? "మీ సందేశాన్ని ఇక్కడ టైప్ చేయండి..." : "Type your response as the customer..."}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={loading}
                style={{ flex: 1, padding: '10px 14px', borderRadius: '6px', border: '1px solid #cbd5e1', fontSize: '14px' }}
              />
              <button
                type="submit"
                disabled={loading || !inputText.trim()}
                style={{
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  padding: '10px 18px',
                  borderRadius: '6px',
                  border: 'none',
                  fontWeight: '600',
                  fontSize: '14px',
                  cursor: loading || !inputText.trim() ? 'not-allowed' : 'pointer',
                  opacity: loading || !inputText.trim() ? 0.6 : 1
                }}
              >
                Send
              </button>
            </form>
          ) : (
            <div style={{ padding: '14px', textAlign: 'center', backgroundColor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
              <p style={{ margin: '0 0 10px 0', fontSize: '14px', color: '#64748b' }}>Conversation ended. Summary: {conversation.summary}</p>
              <button
                onClick={() => setConversation(null)}
                style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
              >
                Start New Interaction
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
