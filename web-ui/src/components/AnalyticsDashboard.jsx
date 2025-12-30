import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Target, Award, MapPin } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const API_BASE = 'http://localhost:8001';

const StatCard = ({ title, value, subtitle, trend, icon: Icon }) => (
  <div className="stat-card" style={{
    background: 'rgba(255,255,255,0.05)',
    borderRadius: '12px',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: '#888', fontSize: '0.875rem' }}>{title}</span>
      {Icon && <Icon size={20} style={{ color: '#00f2ff' }} />}
    </div>
    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#fff' }}>{value}</div>
    {subtitle && (
      <div style={{ 
        fontSize: '0.875rem', 
        color: trend === 'up' ? '#4ade80' : trend === 'down' ? '#f87171' : '#888' 
      }}>
        {trend === 'up' && '↑ '}
        {trend === 'down' && '↓ '}
        {subtitle}
      </div>
    )}
  </div>
);

const AnalyticsDashboard = () => {
  const [accuracy, setAccuracy] = useState(null);
  const [roi, setRoi] = useState(null);
  const [venues, setVenues] = useState(null);
  const [leaderboard, setLeaderboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    fetchData();
  }, [days]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [accRes, roiRes, venueRes, leaderRes] = await Promise.all([
        fetch(`${API_BASE}/api/analytics/accuracy?days=${days}`),
        fetch(`${API_BASE}/api/analytics/roi?days=${days}&bet_amount=100`),
        fetch(`${API_BASE}/api/analytics/venue-stats`),
        fetch(`${API_BASE}/api/analytics/leaderboard?limit=10`)
      ]);
      
      setAccuracy(await accRes.json());
      setRoi(await roiRes.json());
      setVenues(await venueRes.json());
      setLeaderboard(await leaderRes.json());
    } catch (e) {
      console.error('Failed to fetch analytics', e);
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>
        読み込み中...
      </div>
    );
  }

  const venueNames = {
    1: '桐生', 2: '戸田', 3: '江戸川', 4: '平和島', 5: '多摩川', 6: '浜名湖',
    7: '蒲郡', 8: '常滑', 9: '津', 10: '三国', 11: 'びわこ', 12: '住之江',
    13: '尼崎', 14: '鳴門', 15: '丸亀', 16: '児島', 17: '宮島', 18: '徳山',
    19: '下関', 20: '若松', 21: '芦屋', 22: '福岡', 23: '唐津', 24: '大村'
  };

  return (
    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Period Selector */}
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <span style={{ color: '#888' }}>期間:</span>
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
              cursor: 'pointer',
              fontWeight: days === d ? 'bold' : 'normal'
            }}
          >
            {d}日
          </button>
        ))}
      </div>

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <StatCard 
          title="的中率" 
          value={`${accuracy?.overall_hit_rate || 0}%`}
          subtitle={`${accuracy?.total_races || 0}レース`}
          trend={accuracy?.overall_hit_rate > 50 ? 'up' : 'down'}
          icon={Target}
        />
        <StatCard 
          title="ROI" 
          value={`${roi?.roi || 0}%`}
          subtitle={`純利益: ¥${roi?.net_profit?.toLocaleString() || 0}`}
          trend={roi?.roi > 0 ? 'up' : 'down'}
          icon={roi?.roi > 0 ? TrendingUp : TrendingDown}
        />
        <StatCard 
          title="勝敗" 
          value={`${roi?.wins || 0}-${roi?.losses || 0}`}
          subtitle={`勝率 ${roi?.win_rate || 0}%`}
          icon={Award}
        />
      </div>

      {/* Daily Chart */}
      {accuracy?.daily_stats?.length > 0 && (
        <div style={{ 
          background: 'rgba(255,255,255,0.05)', 
          borderRadius: '12px', 
          padding: '1.5rem' 
        }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff' }}>日別的中率</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={accuracy.daily_stats}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" domain={[0, 100]} />
              <Tooltip 
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333' }}
                labelStyle={{ color: '#fff' }}
              />
              <Line 
                type="monotone" 
                dataKey="hit_rate" 
                stroke="#00f2ff" 
                strokeWidth={2}
                dot={{ fill: '#00f2ff' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Two Column Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {/* Venue Stats */}
        <div style={{ 
          background: 'rgba(255,255,255,0.05)', 
          borderRadius: '12px', 
          padding: '1.5rem' 
        }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <MapPin size={18} /> 会場別的中率
          </h3>
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {venues?.venue_stats?.slice(0, 10).map((v, i) => (
              <div key={v.venue_code} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 0',
                borderBottom: '1px solid rgba(255,255,255,0.1)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ 
                    width: '24px', 
                    height: '24px', 
                    borderRadius: '50%', 
                    background: i < 3 ? '#fbbf24' : 'rgba(255,255,255,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    color: i < 3 ? '#000' : '#888'
                  }}>
                    {i + 1}
                  </span>
                  <span style={{ color: '#fff' }}>{venueNames[v.venue_code] || v.venue_code}</span>
                </div>
                <span style={{ 
                  color: v.hit_rate >= 50 ? '#4ade80' : '#f87171',
                  fontWeight: 'bold'
                }}>
                  {v.hit_rate}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Leaderboard */}
        <div style={{ 
          background: 'rgba(255,255,255,0.05)', 
          borderRadius: '12px', 
          padding: '1.5rem' 
        }}>
          <h3 style={{ margin: '0 0 1rem 0', color: '#fff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Award size={18} /> トップレーサー
          </h3>
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {leaderboard?.leaderboard?.map((r, i) => (
              <div key={r.racer_id} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.75rem 0',
                borderBottom: '1px solid rgba(255,255,255,0.1)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <span style={{ 
                    width: '24px', 
                    height: '24px', 
                    borderRadius: '50%', 
                    background: i === 0 ? '#fbbf24' : i === 1 ? '#9ca3af' : i === 2 ? '#cd7f32' : 'rgba(255,255,255,0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.75rem',
                    color: i < 3 ? '#000' : '#888'
                  }}>
                    {r.rank}
                  </span>
                  <div>
                    <div style={{ color: '#fff', fontSize: '0.875rem' }}>#{r.racer_id}</div>
                    <div style={{ color: '#888', fontSize: '0.75rem' }}>
                      勝率 {r.win_rate}% / {r.races}R
                    </div>
                  </div>
                </div>
                <span style={{ 
                  color: '#4ade80',
                  fontWeight: 'bold'
                }}>
                  {r.actual_hit_rate}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
