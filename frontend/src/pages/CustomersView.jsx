import React, { useState, useEffect } from 'react';
import { fetchCustomers, fetchConversations } from '../services/api';

export default function CustomersView() {
  const [customers, setCustomers] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cList, convList] = await Promise.all([
          fetchCustomers().catch(() => []),
          fetchConversations().catch(() => [])
        ]);
        setCustomers(cList);
        setConversations(convList);
      } catch (err) {
        console.error('Failed to load customers:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>👥 Customer Directory & History</h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Registered customer contacts, language preferences, and interaction sessions.</p>
      </div>

      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {customers.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
            No customers registered yet.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '12px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 16px' }}>ID</th>
                <th style={{ padding: '12px 16px' }}>Name</th>
                <th style={{ padding: '12px 16px' }}>Phone</th>
                <th style={{ padding: '12px 16px' }}>Preferred Language</th>
                <th style={{ padding: '12px 16px' }}>Calls / Sessions</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => {
                const count = conversations.filter(conv => conv.customer_id === c.id).length;
                return (
                  <tr key={c.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px', fontWeight: '600', color: '#64748b' }}>#{c.id}</td>
                    <td style={{ padding: '12px 16px', fontWeight: '600', color: '#0f172a' }}>{c.name}</td>
                    <td style={{ padding: '12px 16px', color: '#334155' }}>{c.phone}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ backgroundColor: '#eff6ff', color: '#1d4ed8', padding: '2px 8px', borderRadius: '10px', fontSize: '12px' }}>
                        {c.preferred_language || 'English'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontWeight: '600', color: '#2563eb' }}>
                      {count} {count === 1 ? 'interaction' : 'interactions'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
