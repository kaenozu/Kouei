import React, { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Target, DollarSign, RefreshCw } from 'lucide-react';

const API_BASE = '';

const BacktestResults = ({ threshold = 0.7 }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays] = useState(7);

  const fetchBacktest = async () => {
    setLoading(true);
    try {
      const resp = await fetch(
        `${API_BASE}/api/analytics/backtest/high-prob?threshold=${threshold}&days=${days}`
      );
      const data = await resp.json();
      setResults(data);
    } catch (e) {
      console.error('Failed to fetch backtest', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchBacktest();
  }, [threshold, days]);

  if (!results) return null;

  const roiColor = results.roi > 0 ? '#00ff88' : '#ff6b6b';

  return (
    <div style={{
      background: 'rgba(0, 255, 136, 0.05)',
      border: '1px solid rgba(0, 255, 136, 0.2)',
      borderRadius: '16px',
      padding: '1.5rem',
      marginTop: '2rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
        <TrendingUp size={24} color="#00ff88" />
        <h3 style={{ margin: 0, color: '#fff' }}>
          バックテスト結果（{(threshold * 100).toFixed(0)}%以上戦略）
        </h3>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          {[3, 7, 14, 30].map(d => (
            <button
              key={d}
              onClick={() => setDays(d)}
              style={{
                padding: '0.3rem 0.8rem',
                borderRadius: '6px',
                border: days === d ? '1px solid #00ff88' : '1px solid #333',
                background: days === d ? 'rgba(0, 255, 136, 0.2)' : 'transparent',
                color: days === d ? '#00ff88' : '#888',
                cursor: 'pointer',
                fontSize: '0.8rem'
              }}
            >
              {d}日
            </button>
          ))}
        </div>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(4, 1fr)', 
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: '1rem', 
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#888', fontSize: '0.8rem', marginBottom: '0.3rem' }}>対象レース</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#fff' }}>
            {results.total_races}
          </div>
        </div>

        <div style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: '1rem', 
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#888', fontSize: '0.8rem', marginBottom: '0.3rem' }}>的中率</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: '#00ff88' }}>
            {results.hit_rate}%
          </div>
        </div>

        <div style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: '1rem', 
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#888', fontSize: '0.8rem', marginBottom: '0.3rem' }}>ROI</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: roiColor }}>
            {results.roi > 0 ? '+' : ''}{results.roi}%
          </div>
        </div>

        <div style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: '1rem', 
          borderRadius: '12px',
          textAlign: 'center'
        }}>
          <div style={{ color: '#888', fontSize: '0.8rem', marginBottom: '0.3rem' }}>純利益</div>
          <div style={{ fontSize: '1.8rem', fontWeight: '900', color: roiColor }}>
            ¥{results.profit?.toLocaleString()}
          </div>
        </div>
      </div>

      {/* 日別推移 */}
      {results.daily_stats && results.daily_stats.length > 0 && (
        <div>
          <h4 style={{ color: '#888', marginBottom: '0.5rem', fontSize: '0.9rem' }}>日別成績</h4>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', 
            gap: '0.5rem' 
          }}>
            {results.daily_stats.map((day, idx) => (
              <div 
                key={idx}
                style={{
                  background: 'rgba(0,0,0,0.2)',
                  padding: '0.8rem',
                  borderRadius: '8px',
                  textAlign: 'center'
                }}
              >
                <div style={{ color: '#666', fontSize: '0.7rem' }}>
                  {day.date.slice(4, 6)}/{day.date.slice(6, 8)}
                </div>
                <div style={{ color: '#00ff88', fontWeight: '700' }}>
                  {day.hits}/{day.races}
                </div>
                <div style={{ color: day.profit > 0 ? '#00ff88' : '#ff6b6b', fontSize: '0.8rem' }}>
                  ¥{day.profit > 0 ? '+' : ''}{day.profit.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BacktestResults;
