import React, { useState, useEffect } from 'react';

const API_BASE = '';

export default function PlaceBets() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);
  const [minProb, setMinProb] = useState(0.5);

  useEffect(() => {
    fetchPredictions();
  }, [minProb]);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const res = await fetch(`${API_BASE}/api/place?date=${date}&min_prob=${minProb}`);
      const data = await res.json();
      setPredictions(data.predictions || []);
    } catch (err) {
      console.error('Error:', err);
    }
    setLoading(false);
  };

  const runBacktest = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/place/backtest?min_prob=${minProb}`);
      const data = await res.json();
      setBacktestResult(data);
    } catch (err) {
      console.error('Backtest error:', err);
    }
  };

  const getConfidenceStyle = (conf) => {
    switch (conf) {
      case 'S': return { background: '#eab308', color: '#000' };
      case 'A': return { background: '#8b5cf6', color: '#fff' };
      case 'B': return { background: '#3b82f6', color: '#fff' };
      default: return { background: '#4b5563', color: '#fff' };
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ background: 'rgba(17, 24, 39, 0.8)', borderRadius: '12px', padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff', margin: 0 }}>🎯 複勝予測</h2>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <select
              value={minProb}
              onChange={(e) => setMinProb(parseFloat(e.target.value))}
              style={{ background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '6px', border: 'none' }}
            >
              <option value={0.4}>確率40%+</option>
              <option value={0.5}>確率50%+</option>
              <option value={0.6}>確率60%+</option>
              <option value={0.7}>確率70%+</option>
            </select>
            <button
              onClick={runBacktest}
              style={{ padding: '0.5rem 1rem', background: '#7c3aed', color: '#fff', borderRadius: '6px', border: 'none', cursor: 'pointer' }}
            >
              バックテスト
            </button>
          </div>
        </div>

        {backtestResult && (
          <div style={{ background: '#1f2937', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem' }}>
            <h3 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '0.75rem' }}>📊 バックテスト結果</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', textAlign: 'center' }}>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>総賭け数</div>
                <div style={{ color: '#fff', fontWeight: 'bold', fontSize: '1.25rem' }}>{backtestResult.summary?.total_bets}</div>
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>的中数</div>
                <div style={{ color: '#10b981', fontWeight: 'bold', fontSize: '1.25rem' }}>{backtestResult.summary?.total_wins}</div>
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>的中率</div>
                <div style={{ color: '#06b6d4', fontWeight: 'bold', fontSize: '1.25rem' }}>{backtestResult.summary?.hit_rate}%</div>
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>ROI</div>
                <div style={{ color: backtestResult.summary?.roi >= 0 ? '#10b981' : '#ef4444', fontWeight: 'bold', fontSize: '1.25rem' }}>
                  {backtestResult.summary?.roi}%
                </div>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#9ca3af' }}>読み込み中...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
            {predictions.map((pred, idx) => (
              <div key={idx} style={{ background: '#1f2937', borderRadius: '10px', padding: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <div>
                    <span style={{ color: '#9ca3af', fontSize: '0.875rem' }}>{pred.jyo_name}</span>
                    <span style={{ color: '#fff', fontWeight: 'bold', marginLeft: '0.5rem' }}>{pred.race_no}R</span>
                  </div>
                  <span style={{ ...getConfidenceStyle(pred.confidence), padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                    {pred.confidence}
                  </span>
                </div>
                
                <div style={{ textAlign: 'center', margin: '0.75rem 0' }}>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#06b6d4' }}>{pred.boat_no}号艇</div>
                  {pred.racer_name && (
                    <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>{pred.racer_name}</div>
                  )}
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem', textAlign: 'center' }}>
                  <div>
                    <span style={{ color: '#6b7280' }}>3着内率</span>
                    <div style={{ color: '#10b981', fontWeight: 'bold' }}>{(pred.probability * 100).toFixed(0)}%</div>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>期待値</span>
                    <div style={{ color: pred.ev >= 1.0 ? '#10b981' : '#ef4444', fontWeight: 'bold' }}>
                      {pred.ev?.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
