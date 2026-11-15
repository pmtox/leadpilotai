import React, { useEffect, useState } from 'react';
import { fetchCustomers, fetchConversations } from '../services/api';

export default function CustomersView() {
  const [customers, setCustomers] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    Promise.all([fetchCustomers(), fetchConversations()])
      .then(([customerList, conversationList]) => {
        if (!active) return;
        setCustomers(customerList);
        setConversations(conversationList);
      })
      .catch((loadError) => {
        if (active) setError(loadError.message || 'Could not load customer records.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const conversationCounts = conversations.reduce((counts, conversation) => {
    counts[conversation.customer_id] = (counts[conversation.customer_id] || 0) + 1;
    return counts;
  }, {});
  const leadsByCustomer = conversations.reduce((leads, conversation) => {
    if (conversation.lead) leads[conversation.customer_id] = conversation.lead;
    return leads;
  }, {});

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ADMIN WORKSPACE</p>
          <h1>Customers</h1>
          <p>Customer accounts, conversations, and lead status.</p>
        </div>
        <span className="record-count">{customers.length} {customers.length === 1 ? 'customer' : 'customers'}</span>
      </div>

      {error && <p className="notice notice-error" role="alert">{error}</p>}

      <div className="surface table-card">
        {loading ? (
          <p className="table-state">Loading customer records…</p>
        ) : customers.length === 0 ? (
          <p className="table-state">No customer accounts yet.</p>
        ) : (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Contact</th>
                  <th>Language</th>
                  <th>Lead status</th>
                  <th>Conversations</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => {
                  const lead = leadsByCustomer[customer.id];
                  const classification = lead?.classification?.toLowerCase();
                  return (
                    <tr key={customer.id}>
                      <td>
                        <strong className="table-primary">{customer.name}</strong>
                        <span className="table-secondary">Customer #{customer.id}</span>
                      </td>
                      <td>
                        <span className="table-primary">{customer.email || '—'}</span>
                        <span className="table-secondary">{customer.phone || 'No phone number'}</span>
                      </td>
                      <td><span className="language-tag">{customer.preferred_language || 'English'}</span></td>
                      <td>
                        {lead ? (
                          <span className={`lead-tag lead-tag-${classification || 'cold'}`}>
                            {lead.classification || 'New'} · {lead.score || 0}/100
                          </span>
                        ) : <span className="table-secondary">Not qualified</span>}
                      </td>
                      <td className="session-count">{conversationCounts[customer.id] || 0}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
