import React, { useState, useEffect } from 'react';
import { fetchCustomers, fetchConversations, fetchLeads, fetchActions } from '../services/api';

export default function DashboardView({ onNavigateToCallCenter }) {
  const [stats, setStats] = useState({
    customers: 0,
    conversations: 0,
    hotLeads: 0,
    warmLeads: 0,
    coldLeads: 0,
    pendingActions: 0
  });
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [custs, convs, leads, actions] = await Promise.all([
          fetchCustomers().catch(() => []),
          fetchConversations().catch(() => []),
          fetchLeads().catch(() => []),
          fetchActions().catch(() => [])
        ]);

        const hot = leads.filter(l => l.classification === 'HOT').length;
        const warm = leads.filter(l => l.classification === 'WARM').length;
        const cold = leads.filter(l => l.classification === 'COLD').length;
        const pending = actions.filter(a => a.status === 'draft' || a.status === 'pending').length;

        setStats({
          customers: custs.length,
          conversations: convs.length,
          hotLeads: hot,
          warmLeads: warm,
          coldLeads: cold,
          pendingActions: pending
        });
        setRecentLeads(leads.slice(0, 5));
      } catch (err) {
        console.error('Failed to load dashboard metrics:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f8fafc', padding: '18px 24px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
        <div>
          <h2 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#0f172a' }}>Sales Intelligence Overview</h2>
          <p style={{ margin: 0, fontSize: '14px', color: '#64748b' }}>Real-time qualification metrics across multilingual customer conversations.</p>
        </div>
        <button
          onClick={onNavigateToCallCenter}
          style={{
            backgroundColor: '#2563eb',
            color: '#ffffff',
            padding: '10px 18px',
            borderRadius: '6px',
            border: 'none',
            fontSize: '14px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span>🎙️</span> Launch Live Call Center
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b' }}>TOTAL CONVERSATIONS</div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#0f172a', marginTop: '6px' }}>{stats.conversations}</div>
          <div style={{ fontSize: '12px', color: '#16a34a', marginTop: '4px' }}>Across EN, HI, TE</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #86efac', backgroundColor: '#f0fdf4', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#166534' }}>HOT LEADS (70-100)</div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#15803d', marginTop: '6px' }}>🔥 {stats.hotLeads}</div>
          <div style={{ fontSize: '12px', color: '#166534', marginTop: '4px' }}>Ready for follow-up</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #fcd34d', backgroundColor: '#fffbeb', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#b45309' }}>WARM LEADS (40-69)</div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#b45309', marginTop: '6px' }}>☀️ {stats.warmLeads}</div>
          <div style={{ fontSize: '12px', color: '#b45309', marginTop: '4px' }}>Needs nurturing</div>
        </div>

        <div style={{ backgroundColor: '#ffffff', padding: '18px', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ fontSize: '12px', fontWeight: '700', color: '#64748b' }}>PENDING ACTIONS</div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: '#2563eb', marginTop: '6px' }}>💬 {stats.pendingActions}</div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Draft proposals ready</div>
        </div>
      </div>

      {/* Recent Qualified Leads Table */}
      <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>Recent Qualified Leads</h3>
          <span style={{ fontSize: '12px', color: '#64748b' }}>Automated Qualification Engine</span>
        </div>

        {recentLeads.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>
            No leads recorded yet. Start a conversation in the Live Call Center!
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b', fontSize: '12px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 16px' }}>ID</th>
                <th style={{ padding: '12px 16px' }}>Category</th>
                <th style={{ padding: '12px 16px' }}>Budget</th>
                <th style={{ padding: '12px 16px' }}>Catalog</th>
                <th style={{ padding: '12px 16px' }}>Timeline</th>
                <th style={{ padding: '12px 16px' }}>Score</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentLeads.map((l) => (
                <tr key={l.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '12px 16px', fontWeight: '600', color: '#64748b' }}>#{l.id}</td>
                  <td style={{ padding: '12px 16px', fontWeight: '600', color: '#0f172a' }}>{l.business_type || 'General'}</td>
                  <td style={{ padding: '12px 16px', color: '#166534', fontWeight: '600' }}>
                    {l.budget ? `₹${l.budget.toLocaleString('en-IN')}` : '—'}
                  </td>
                  <td style={{ padding: '12px 16px', color: '#334155' }}>{l.product_count ? `${l.product_count} items` : '—'}</td>
                  <td style={{ padding: '12px 16px', color: '#334155' }}>{l.timeline || '—'}</td>
                  <td style={{ padding: '12px 16px', fontWeight: '700' }}>{l.score}/100</td>
                  <td style={{ padding: '12px 16px' }}>
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
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
