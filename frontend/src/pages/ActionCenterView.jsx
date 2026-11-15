import React, { useState, useEffect } from 'react';
import { fetchActions, executeAction } from '../services/api';

export default function ActionCenterView() {
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [drafts, setDrafts] = useState({});
  const [error, setError] = useState('');

  async function loadActions() {
    try {
      const data = await fetchActions();
      setActions(data);
      setError('');
    } catch (loadError) {
      setError(loadError.message || 'Could not load action center records.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    fetchActions()
      .then((data) => {
        if (active) {
          setActions(data);
          setError('');
        }
      })
      .catch((loadError) => {
        if (active) setError(loadError.message || 'Could not load action center records.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
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
    <section className="page-section">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ADMIN WORKSPACE</p>
          <h1>Action Center</h1>
          <p>Review call-summary delivery and follow-up actions.</p>
        </div>
      </div>

      {error && <p className="notice notice-error" role="alert">{error}</p>}

      <div className="surface action-card">
        <div className="action-card-title">
          SCHEDULED & DRAFT WORKFLOWS
        </div>

        {loading ? (
          <p className="table-state">Loading workflows…</p>
        ) : actions.length === 0 ? (
          <p className="table-state">
            No action events yet. Follow-up proposals appear here as conversations are completed.
          </p>
        ) : (
          <div className="action-list">
            {actions.map((act) => (
              <article className="action-row" key={act.id}>
                <div className="action-content">
                  <div className="action-heading">
                    <strong className="action-type">
                      {act.action_type === 'whatsapp_followup'
                        ? '💬 WhatsApp Follow-Up'
                        : act.action_type === 'email_followup'
                          ? '✉️ Call Summary Email'
                          : '📞 Scheduled Callback'}
                    </strong>
                    <span className={`action-status action-status-${act.status}`}>
                      {act.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="action-payload">
                    {act.action_type === 'email_followup' && (
                      <div className="action-destination">
                        <strong>To:</strong> {act.payload?.recipient || 'Email not provided'}
                        <br />
                        <strong>Subject:</strong> {act.payload?.subject || 'Project discussion summary'}
                      </div>
                    )}
                    <div className="action-message">
                      {drafts[act.id] || act.payload?.followup_draft || act.payload?.message || JSON.stringify(act.payload)}
                    </div>
                    {act.payload?.delivery_message && (
                      <div className={`action-delivery ${act.status === 'failed' ? 'action-delivery-failed' : ''}`} role="status">
                        {act.payload.delivery_message}
                      </div>
                    )}
                  </div>
                </div>

                <div className="action-cta">
                  {!['sent', 'delivered', 'executed', 'cancelled'].includes(act.status) ? (
                    <button
                      className="button button-primary action-button"
                      onClick={() => handleExecute(act.id)}
                      type="button"
                    >
                      {act.action_type === 'email_followup' ? 'Approve & Send Email →' : 'Confirm Consent & Send →'}
                    </button>
                  ) : (
                    <span className="action-done">
                      {['sent', 'delivered'].includes(act.status) ? '✓ Sent' : act.status === 'cancelled' ? 'Cancelled' : '✓ Recorded'}
                    </span>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
