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
      const cust = await createCustomer({
        name: customerName,
        phone: customerPhone,
        preferred_language: language,
      });

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

  const lead = conversation?.lead;

  // Lead qualification styling
  const getBadgeStyle = (classification) => {
    switch (classification) {
      case 'HOT':
        return { bg: '#dcfce7', text: '#15803d', border: '#86efac', label: '🔥 HOT LEAD' };
      case 'WARM':
        return { bg: '#fef3c7', text: '#b45309', border: '#fcd34d', label: '☀️ WARM LEAD' };
      default:
        return { bg: '#f1f5f9', text: '#475569', border: '#cbd5e1', label: '❄️ COLD LEAD' };
    }
  };

  const badge = getBadgeStyle(lead?.classification);

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', maxWidth: '1080px', margin: '20px auto', padding: '24px', backgroundColor: '#ffffff', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
      {/* Header */}
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '16px', marginBottom: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, color: '#0f172a', fontSize: '26px' }}>🚀 LeadPilot AI</h1>
          <p style={{ margin: '4px 0 0 0', color: '#64748b', fontSize: '14px' }}>Autonomous Multilingual AI Sales Agent</p>
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
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
      <div style={{ backgroundColor: '#f1f5f9', borderLeft: '4px solid #f59e0b', padding: '12px 16px', borderRadius: '4px', marginBottom: '20px', fontSize: '14px', color: '#334155' }}>
        <strong>Checkpoint CP-04: Lead Qualification Engine</strong> — Live scoring (0–100), HOT/WARM/COLD status, and personalized follow-up generation active.
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
            }}
          >
            {loading ? 'Starting...' : 'Start AI Sales Conversation →'}
          </button>
        </form>
      ) : (
        /* 2-Column Layout: Chat on Left, Structured Lead Intelligence on Right */
        <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '20px' }}>
          {/* Chat Column */}
          <div style={{ display: 'flex', flexDirection: 'column', height: '620px', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ backgroundColor: '#f8fafc', padding: '12px 16px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontWeight: '600', color: '#1e293b' }}>{customerName}</span>
                <span style={{ marginLeft: '8px', color: '#64748b', fontSize: '13px' }}>({language})</span>
                <span style={{ marginLeft: '10px', fontSize: '11px', padding: '2px 8px', borderRadius: '10px', backgroundColor: conversation.status === 'active' ? '#dcfce7' : '#f1f5f9', color: conversation.status === 'active' ? '#166534' : '#64748b' }}>
                  {conversation.status.toUpperCase()}
                </span>
              </div>
              {conversation.status === 'active' && (
                <button
                  onClick={handleEndConversation}
                  disabled={loading}
                  style={{ padding: '6px 10px', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: '600', cursor: 'pointer' }}
                >
                  End Chat
                </button>
              )}
            </div>

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
                        maxWidth: '82%',
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
                    LeadPilot AI is thinking & qualifying lead...
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {conversation.status === 'active' ? (
              <form onSubmit={handleSendMessage} style={{ display: 'flex', padding: '12px', backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0', gap: '8px' }}>
                <input
                  type="text"
                  placeholder={language === 'Hindi' ? "उदा: 100 उत्पाद हैं और ₹70,000 बजट है..." : language === 'Telugu' ? "ఉదా: 100 ఉత్పత్తులు, ₹70,000 బడ్జెట్..." : "e.g. Online clothing store with 200 items, ₹80,000 budget..."}
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
                  }}
                >
                  Send
                </button>
              </form>
            ) : (
              <div style={{ padding: '12px', textAlign: 'center', backgroundColor: '#f8fafc', borderTop: '1px solid #e2e8f0' }}>
                <button
                  onClick={() => setConversation(null)}
                  style={{ padding: '8px 16px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
                >
                  Start New Interaction
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Structured Lead Intelligence & Qualification Card */}
          <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', maxHeight: '620px' }}>
            {/* Qualification Status Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: badge.bg, border: `1px solid ${badge.border}`, padding: '10px 14px', borderRadius: '8px' }}>
              <div>
                <div style={{ fontSize: '11px', color: badge.text, fontWeight: '700', textTransform: 'uppercase' }}>LEAD QUALIFICATION</div>
                <div style={{ fontSize: '18px', fontWeight: '800', color: badge.text }}>
                  {badge.label}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '11px', color: badge.text, fontWeight: '600' }}>SCORE</div>
                <div style={{ fontSize: '20px', fontWeight: '800', color: badge.text }}>
                  {lead?.score || 0}<span style={{ fontSize: '12px', opacity: 0.8 }}>/100</span>
                </div>
              </div>
            </div>

            {/* Score Progress Bar */}
            <div style={{ backgroundColor: '#e2e8f0', borderRadius: '6px', height: '8px', overflow: 'hidden' }}>
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, Math.max(0, lead?.score || 0))}%`,
                  backgroundColor: lead?.score >= 70 ? '#16a34a' : lead?.score >= 40 ? '#d97706' : '#64748b',
                  transition: 'width 0.4s ease'
                }}
              />
            </div>

            {/* Qualification Explanation */}
            {lead?.qualification_reason && (
              <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '12px', color: '#334155', lineHeight: '1.4' }}>
                <strong>Qualification Details:</strong> {lead.qualification_reason}
              </div>
            )}

            {/* Extracted Details Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '10px' }}>
              <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>BUSINESS TYPE</div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: lead?.business_type ? '#0f172a' : '#94a3b8', marginTop: '2px' }}>
                  {lead?.business_type || 'Unknown yet'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>PRODUCT COUNT</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: lead?.product_count ? '#0f172a' : '#94a3b8', marginTop: '2px' }}>
                    {lead?.product_count ? `${lead.product_count} items` : 'Unknown'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>BUDGET</div>
                  <div style={{ fontSize: '14px', fontWeight: '600', color: lead?.budget ? '#166534' : '#94a3b8', marginTop: '2px' }}>
                    {lead?.budget ? `₹${lead.budget.toLocaleString('en-IN')}` : 'Unknown'}
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>TIMELINE</div>
                  <div style={{ fontSize: '13px', fontWeight: '500', color: lead?.timeline ? '#0f172a' : '#94a3b8', marginTop: '2px' }}>
                    {lead?.timeline || 'Unknown'}
                  </div>
                </div>

                <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>INTENT</div>
                  <div style={{ fontSize: '13px', fontWeight: '700', marginTop: '2px', color: lead?.buying_intent === 'HIGH' ? '#166534' : lead?.buying_intent === 'MEDIUM' ? '#d97706' : '#64748b' }}>
                    {lead?.buying_intent || 'UNKNOWN'}
                  </div>
                </div>
              </div>

              <div style={{ backgroundColor: '#ffffff', padding: '10px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                <div style={{ fontSize: '11px', color: '#64748b', fontWeight: '600', marginBottom: '4px' }}>FEATURES</div>
                {lead?.features && lead.features.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {lead.features.map((f, i) => (
                      <span key={i} style={{ backgroundColor: '#eff6ff', color: '#1d4ed8', fontSize: '11px', padding: '2px 7px', borderRadius: '10px', border: '1px solid #bfdbfe' }}>
                        ✓ {f}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span style={{ fontSize: '12px', color: '#94a3b8' }}>None identified</span>
                )}
              </div>
            </div>

            {/* Prepared Follow-up Message Draft */}
            {lead?.followup_draft && (
              <div style={{ backgroundColor: '#f0fdf4', padding: '12px', borderRadius: '6px', border: '1px solid #bbf7d0', marginTop: '4px' }}>
                <div style={{ fontSize: '11px', color: '#166534', fontWeight: '700', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span>💬</span> PREPARED FOLLOW-UP DRAFT (WHATSAPP)
                </div>
                <div style={{ fontSize: '12px', color: '#14532d', lineHeight: '1.4' }}>
                  {lead.followup_draft}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
