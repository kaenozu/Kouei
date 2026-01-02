import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, Calendar, RefreshCw } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export const PredictionAccuracy = () => {
  const [accuracyData, setAccuracyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState('7');

  useEffect(() => {
    fetchAccuracyData();
  }, [dateRange]);

  const fetchAccuracyData = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/accuracy?days=${dateRange}`);
      const data = await resp.json();
      setAccuracyData(data);
    } catch (e) {
      console.error('Failed to fetch accuracy data', e);
      // モックデータ
      setAccuracyData({
        overall: {
          win_rate: 0.32,
          top2_rate: 0.58,
          top3_rate: 0.75,
          roi: 0.92
        },
        daily: [
          { date: '12/26', accuracy: 0.35, roi: 0.95 },
          { date: '12/27', accuracy: 0.28, roi: 0.82 },
          { date: '12/28', accuracy: 0.42, roi: 1.15 },
          { date: '12/29', accuracy: 0.31, roi: 0.88 },
          { date: '12/30', accuracy: 0.38, roi: 1.05 },
          { date: '12/31', accuracy: 0.29, roi: 0.78 },
          { date: '01/01', accuracy: 0.33, roi: 0.98 }
        ],
        by_confidence: [
          { level: 'A', count: 45, hit_rate: 0.52 },
          { level: 'B', count: 120, hit_rate: 0.35 },
          { level: 'C', count: 280, hit_rate: 0.22 }
        ],
        by_course: [
          { course: 1, predictions: 156, wins: 78, rate: 0.50 },
          { course: 2, predictions: 156, wins: 28, rate: 0.18 },
          { course: 3, predictions: 156, wins: 22, rate: 0.14 },
          { course: 4, predictions: 156, wins: 18, rate: 0.12 },
          { course: 5, predictions: 156, wins: 12, rate: 0.08 },
          { course: 6, predictions: 156, wins: 8, rate: 0.05 }
        ]
      });
    }
    setLoading(false);
  };

  if (!accuracyData) {
    return (
      <div style={{ padding: '1rem', textAlign: 'center' }}>
        <RefreshCw className="spin" size={32} />
        <p>読み込み中...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>
            <Target style={{ display: 'inline', marginRight: '0.5rem' }} /> 予測精度分析
          </h1>
          <p style={{ color: 'var(--text-dim)' }}>過去の予測結果と実際の結果を比較</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {['7', '14', '30'].map(d => (
            <button
              key={d}
              onClick={() => setDateRange(d)}
              style={{
                padding: '0.5rem 1rem',
                background: dateRange === d ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                color: dateRange === d ? '#000' : '#fff',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              {d}日間
            </button>
          ))}
        </div>
      </div>

      {/* 総合指標 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>1着的中率</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--success)' }}>
            {(accuracyData.overall.win_rate * 100).toFixed(1)}%
          </div>
        </div>
        <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>2連率</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '900', color: 'var(--primary)' }}>
            {(accuracyData.overall.top2_rate * 100).toFixed(1)}%
          </div>
        </div>
        <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>3連率</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '900' }}>
            {(accuracyData.overall.top3_rate * 100).toFixed(1)}%
          </div>
        </div>
        <div className="card" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>回収率 (ROI)</div>
          <div style={{ fontSize: '2.5rem', fontWeight: '900', color: accuracyData.overall.roi >= 1 ? 'var(--success)' : 'var(--danger)' }}>
            {(accuracyData.overall.roi * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* 日別推移 */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>日別的中率推移</h3>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={accuracyData.daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="#666" />
              <YAxis stroke="#666" tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)' }}
                formatter={(v) => [`${(v * 100).toFixed(1)}%`]}
              />
              <Line type="monotone" dataKey="accuracy" stroke="#00f2ff" strokeWidth={2} dot={{ fill: '#00f2ff' }} name="的中率" />
              <Line type="monotone" dataKey="roi" stroke="#00ff88" strokeWidth={2} dot={{ fill: '#00ff88' }} name="ROI" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* 信頼度別 */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>信頼度別的中率</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {accuracyData.by_confidence.map(item => (
              <div key={item.level} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  width: '40px', height: '40px', borderRadius: '8px',
                  background: item.level === 'A' ? 'var(--success)' : item.level === 'B' ? 'var(--primary)' : 'var(--text-dim)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: '800', color: '#000'
                }}>
                  {item.level}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span>{item.count}件</span>
                    <span style={{ fontWeight: '700' }}>{(item.hit_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      height: '100%', width: `${item.hit_rate * 100}%`,
                      background: item.level === 'A' ? 'var(--success)' : item.level === 'B' ? 'var(--primary)' : 'var(--text-muted)',
                      borderRadius: '4px'
                    }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* コース別 */}
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>コース別予測精度</h3>
          <div style={{ height: '200px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={accuracyData.by_course}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="course" stroke="#666" />
                <YAxis stroke="#666" tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                <Tooltip
                  contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)' }}
                  formatter={(v) => [`${(v * 100).toFixed(1)}%`]}
                />
                <Bar dataKey="rate" fill="#00f2ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionAccuracy;
