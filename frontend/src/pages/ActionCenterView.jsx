import React, { useState, useEffect } from 'react';
import { fetchActions, executeAction } from '../services/api';

export default function ActionCenterView() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadActions() {
    try {
      const data = await fetchActions();
      setActions(data);
    } catch (err) {
      console.error('Error fetching actions:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadActions();
  }, []);

  async function handleExecute(actionId) {
    try {
      await executeAction(actionId);
      alert('Action successfully executed and recorded!');
      loadActions();
    } catch (err) {
      alert(`Action execution failed: ${err.message}`);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>⚡ Action Center</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Post-conversation workflows, personalized WhatsApp follow-ups, and callbacks.</p>
      </div>

      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc', fontSize: '13px', fontWeight: '700', color: '#475569' }}>
          SCHEDULED & DRAFT WORKFLOWS
        </div>

        {actions.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
            No action events recorded yet. Qualified leads in the Call Center automatically generate follow-up proposals here.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {actions.map((act) => (
              <div key={act.id} style={{ padding: '16px 20px', borderBottom: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: '700', color: '#0f172a' }}>
                      {act.action_type === 'whatsapp_followup' ? '💬 WhatsApp Follow-Up' : '📞 Scheduled Callback'}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontWeight: '700',
                      backgroundColor: act.status === 'executed' ? '#dcfce7' : act.status === 'draft' ? '#fef3c7' : '#f1f5f9',
                      color: act.status === 'executed' ? '#15803d' : act.status === 'draft' ? '#b45309' : '#475569'
                    }}>
                      {act.status.toUpperCase()}
                    </span>
                  </div>

                  <div style={{ backgroundColor: '#f8fafc', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', color: '#1e293b', border: '1px solid #e2e8f0' }}>
                    {act.payload?.message || JSON.stringify(act.payload)}
                  </div>
                </div>

                <div style={{ flexShrink: 0 }}>
                  {act.status !== 'executed' ? (
                    <button
                      onClick={() => handleExecute(act.id)}
                      style={{
                        backgroundColor: '#16a34a',
                        color: '#ffffff',
                        padding: '8px 14px',
                        borderRadius: '6px',
                        border: 'none',
                        fontWeight: '600',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                      Authorize & Send →
                    </button>
                  ) : (
                    <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: '600' }}>✓ Sent / Recorded</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
