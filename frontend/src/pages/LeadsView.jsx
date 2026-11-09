import React, { useState, useEffect } from 'react';
import { fetchLeads } from '../services/api';

export default function LeadsView() {
  const [leads, setLeads] = useState([]);
  const [filter, setFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchLeads();
        setLeads(data);
      } catch (err) {
        console.error('Error fetching leads:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = leads.filter(l => {
    if (filter === 'ALL') return true;
    return l.classification === filter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>🎯 Lead Intelligence & CRM</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Structured requirements, qualification scores, and AI reasoning.</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'HOT', 'WARM', 'COLD'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '6px 14px',
                borderRadius: '6px',
                border: filter === f ? '2px solid #2563eb' : '1px solid #cbd5e1',
                backgroundColor: filter === f ? '#eff6ff' : '#ffffff',
                color: filter === f ? '#1d4ed8' : '#475569',
                fontWeight: filter === f ? '700' : '500',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              {f === 'ALL' ? 'All Leads' : f === 'HOT' ? '🔥 HOT' : f === 'WARM' ? '☀️ WARM' : '❄️ COLD'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        {filtered.length === 0 ? (
          <div style={{ padding: '36px', textAlign: 'center', color: '#94a3b8' }}>
            No leads matching '{filter}' filter.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {filtered.map((l) => (
              <div key={l.id} style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: '700',
                      backgroundColor: l.classification === 'HOT' ? '#dcfce7' : l.classification === 'WARM' ? '#fef3c7' : '#f1f5f9',
                      color: l.classification === 'HOT' ? '#15803d' : l.classification === 'WARM' ? '#b45309' : '#475569'
                    }}>
                      {l.classification}
                    </span>
                    <strong style={{ fontSize: '16px', color: '#0f172a' }}>{l.business_type || 'General Store'}</strong>
                    <span style={{ fontSize: '13px', color: '#64748b' }}>(Lead #{l.id})</span>
                  </div>
                  <div style={{ fontSize: '15px', fontWeight: '800', color: '#2563eb' }}>
                    Score: {l.score}/100
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '13px', color: '#334155', backgroundColor: '#f8fafc', padding: '10px 14px', borderRadius: '6px' }}>
                  <div><strong>Budget:</strong> {l.budget ? `₹${l.budget.toLocaleString('en-IN')}` : 'Not specified'}</div>
                  <div><strong>Catalog Size:</strong> {l.product_count ? `${l.product_count} items` : 'Not specified'}</div>
                  <div><strong>Timeline:</strong> {l.timeline || 'Not specified'}</div>
                  <div><strong>Buying Intent:</strong> {l.buying_intent}</div>
                </div>

                {l.features && l.features.length > 0 && (
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center', marginTop: '2px' }}>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>Features:</span>
                    {l.features.map((f, i) => (
                      <span key={i} style={{ backgroundColor: '#eff6ff', color: '#1d4ed8', fontSize: '11px', padding: '2px 8px', borderRadius: '10px' }}>
                        ✓ {f}
                      </span>
                    ))}
                  </div>
                )}

                {l.qualification_reason && (
                  <div style={{ fontSize: '12px', color: '#475569', fontStyle: 'italic', marginTop: '2px' }}>
                    💡 {l.qualification_reason}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
