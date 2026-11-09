import React, { useState, useEffect } from 'react';
import { fetchActions, executeAction } from '../services/api';

export default function ActionCenterView() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drafts, setDrafts] = useState({});

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
    const action = actions.find((item) => item.id === actionId);
    const isEmail = action?.action_type === 'email_followup';
    const confirmation = isEmail
      ? `Send this call summary to ${action.payload?.recipient || 'the saved customer email'}?`
      : 'Confirm that this customer explicitly opted in to WhatsApp messages. If not confirmed, the message will remain a draft.';
    if (!window.confirm(confirmation)) {
      return;
    }

    try {
      const result = await executeAction(actionId, true);
      if (result.draft_text) {
        setDrafts((current) => ({ ...current, [actionId]: result.draft_text }));
      }
      alert(result.message || 'Action processed.');
      loadActions();
    } catch (err) {
      alert(`Action execution failed: ${err.message}`);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>⚡ Action Center</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Call-summary emails send automatically when a conversation ends and SMTP is configured. Drafts and delivery results appear here with WhatsApp follow-ups.</p>
      </div>

      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc', fontSize: '13px', fontWeight: '700', color: '#475569' }}>
          SCHEDULED & DRAFT WORKFLOWS
        </div>

        {loading ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#64748b' }}>
            Loading workflows...
          </div>
        ) : actions.length === 0 ? (
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
                      {act.action_type === 'whatsapp_followup'
                        ? '💬 WhatsApp Follow-Up'
                        : act.action_type === 'email_followup'
                          ? '✉️ Call Summary Email'
                          : '📞 Scheduled Callback'}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      fontWeight: '700',
                      backgroundColor: ['sent', 'delivered', 'executed'].includes(act.status) ? '#dcfce7' : ['draft', 'queued'].includes(act.status) ? '#fef3c7' : act.status === 'failed' ? '#fee2e2' : '#f1f5f9',
                      color: ['sent', 'delivered', 'executed'].includes(act.status) ? '#15803d' : ['draft', 'queued'].includes(act.status) ? '#b45309' : act.status === 'failed' ? '#b91c1c' : '#475569'
                    }}>
                      {act.status.toUpperCase()}
                    </span>
                  </div>

                  <div style={{ backgroundColor: '#f8fafc', padding: '10px 14px', borderRadius: '6px', fontSize: '13px', color: '#1e293b', border: '1px solid #e2e8f0' }}>
                    {act.action_type === 'email_followup' && (
                      <div style={{ marginBottom: '8px', color: '#475569' }}>
                        <strong>To:</strong> {act.payload?.recipient || 'Email not provided'}
                        <br />
                        <strong>Subject:</strong> {act.payload?.subject || 'Project discussion summary'}
                      </div>
                    )}
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {drafts[act.id] || act.payload?.followup_draft || act.payload?.message || JSON.stringify(act.payload)}
                    </div>
                    {act.payload?.delivery_message && (
                      <div role="status" style={{ marginTop: '8px', color: act.status === 'failed' ? '#b91c1c' : '#64748b' }}>
                        {act.payload.delivery_message}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ flexShrink: 0 }}>
                  {!['sent', 'delivered', 'executed', 'cancelled'].includes(act.status) ? (
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
                      {act.action_type === 'email_followup' ? 'Approve & Send Email →' : 'Confirm Consent & Send →'}
                    </button>
                  ) : (
                    <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: '600' }}>
                      {['sent', 'delivered'].includes(act.status) ? '✓ Sent' : act.status === 'cancelled' ? 'Cancelled' : '✓ Recorded'}
                    </span>
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
