import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Activity, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API_BASE = '';

const BacktestDashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    fetchBacktestData();
  }, [days]);

  const fetchBacktestData = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/backtest/history?days=${days}`);
      const result = await resp.json();
      setData(result);
    } catch (e) {
      console.error('Failed to fetch backtest data', e);
    }
    setLoading(false);
  };

  const runBacktest = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/backtest/run`, { method: 'POST' });
      const result = await resp.json();
      alert(result.error || `バックテスト完了: AUC=${result.auc}`);
      fetchBacktestData();
    } catch (e) {
      alert('バックテスト失敗');
    }
  };

  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>読み込み中...</div>;
  }

  const summary = data?.summary || {};
  const history = data?.history || [];

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, color: '#fff' }}>📊 バックテスト履歴</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[7, 14, 30].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              style={{
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                border: 'none',
                background: days === d ? '#00f2ff' : 'rgba(255,255,255,0.1)',
                color: days === d ? '#000' : '#fff',
                cursor: 'pointer'
              }}
            >
              {d}日
            </button>
          ))}
          <button
            onClick={runBacktest}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              border: 'none',
              background: '#4ade80',
              color: '#000',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            実行
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '1.5rem' }}>
          <div style={{ color: '#888', fontSize: '0.875rem' }}>平均AUC</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#00f2ff' }}>
            {summary.avg_auc?.toFixed(4) || 'N/A'}
          </div>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '1.5rem' }}>
          <div style={{ color: '#888', fontSize: '0.875rem' }}>平均的中率</div>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4ade80' }}>
            {summary.avg_top1_accuracy ? `${(summary.avg_top1_accuracy * 100).toFixed(1)}%` : 'N/A'}
          </div>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '1.5rem' }}>
          <div style={{ color: '#888', fontSize: '0.875rem' }}>平均ROI</div>
          <div style={{ 
            fontSize: '2rem', 
            fontWeight: 'bold', 
            color: (summary.avg_roi || 0) >= 0 ? '#4ade80' : '#f87171' 
          }}>
            {summary.avg_roi != null ? `${summary.avg_roi.toFixed(1)}%` : 'N/A'}
          </div>
        </div>
      </div>

      {/* Chart */}
      {history.length > 0 && (
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>AUC推移</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" domain={[0.7, 0.9]} />
              <Tooltip 
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line type="monotone" dataKey="auc" stroke="#00f2ff" strokeWidth={2} dot={{ fill: '#00f2ff' }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* History Table */}
      {history.length > 0 && (
        <div style={{ background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '1.5rem' }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>詳細履歴</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #333' }}>
                  <th style={{ padding: '0.75rem', textAlign: 'left', color: '#888' }}>日付</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: '#888' }}>AUC</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: '#888' }}>的中率</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: '#888' }}>ROI</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right', color: '#888' }}>レース数</th>
                </tr>
              </thead>
              <tbody>
                {history.slice().reverse().map((row, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                    <td style={{ padding: '0.75rem', color: '#fff' }}>{row.date}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: '#00f2ff' }}>
                      {row.auc?.toFixed(4)}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: '#4ade80' }}>
                      {row.top1_accuracy ? `${(row.top1_accuracy * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td style={{ 
                      padding: '0.75rem', 
                      textAlign: 'right',
                      color: (row.sim_roi || 0) >= 0 ? '#4ade80' : '#f87171'
                    }}>
                      {row.sim_roi != null ? `${row.sim_roi.toFixed(1)}%` : '-'}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', color: '#888' }}>
                      {row.total_races || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestDashboard;
