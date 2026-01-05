import React, { useState } from 'react';

const API_BASE = '';
const STRATEGIES = ['win', 'exacta', 'trifecta', 'wide', 'place'];
const STRATEGY_NAMES = {
  win: '単勝',
  exacta: '2連単',
  trifecta: '3連単',
  wide: 'ワイド',
  place: '複勝'
};

export default function EnhancedBacktest() {
  const [loading, setLoading] = useState(false);
  const [compareResult, setCompareResult] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState('win');
  const [detailedResult, setDetailedResult] = useState(null);
  const [minConfidence, setMinConfidence] = useState('C');

  const runCompare = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/backtest/compare`);
      const data = await res.json();
      setCompareResult(data);
    } catch (err) {
      console.error('Compare error:', err);
    }
    setLoading(false);
  };

  const runDetailedBacktest = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/backtest/comprehensive?strategy=${selectedStrategy}&min_confidence=${minConfidence}`
      );
      const data = await res.json();
      setDetailedResult(data);
    } catch (err) {
      console.error('Backtest error:', err);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ background: 'rgba(17, 24, 39, 0.8)', borderRadius: '12px', padding: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff', marginBottom: '1.5rem' }}>🔬 高度バックテスト</h2>
        
        {/* Controls */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
          <button
            onClick={runCompare}
            disabled={loading}
            style={{ padding: '0.5rem 1rem', background: '#06b6d4', color: '#fff', borderRadius: '6px', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.5 : 1 }}
          >
            {loading ? '分析中...' : '📊 全戦略比較'}
          </button>
          
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              style={{ background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '6px', border: 'none' }}
            >
              {STRATEGIES.map(s => (
                <option key={s} value={s}>{STRATEGY_NAMES[s]}</option>
              ))}
            </select>
            
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(e.target.value)}
              style={{ background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '6px', border: 'none' }}
            >
              <option value="S">Sランク以上</option>
              <option value="A">Aランク以上</option>
              <option value="B">Bランク以上</option>
              <option value="C">全て</option>
            </select>
            
            <button
              onClick={runDetailedBacktest}
              disabled={loading}
              style={{ padding: '0.5rem 1rem', background: '#7c3aed', color: '#fff', borderRadius: '6px', border: 'none', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.5 : 1 }}
            >
              詳細分析
            </button>
          </div>
        </div>

        {/* Strategy Comparison */}
        {compareResult?.strategies && (
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '1rem' }}>📊 戦略比較結果</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem' }}>
              {compareResult.strategies.map((s, idx) => (
                <div 
                  key={s.strategy}
                  style={{ 
                    background: '#1f2937', 
                    borderRadius: '10px', 
                    padding: '1rem', 
                    textAlign: 'center',
                    border: s.strategy === compareResult.best_strategy ? '2px solid #eab308' : '2px solid transparent'
                  }}
                >
                  {s.strategy === compareResult.best_strategy && (
                    <div style={{ color: '#eab308', fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>👑 Best</div>
                  )}
                  <div style={{ color: '#9ca3af', fontSize: '0.875rem' }}>{STRATEGY_NAMES[s.strategy]}</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: (s.summary?.roi || 0) >= 0 ? '#10b981' : '#ef4444', margin: '0.5rem 0' }}>
                    {s.summary?.roi || 0}%
                  </div>
                  <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>
                    {s.summary?.total_bets || 0}件 / {s.summary?.hit_rate || 0}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Result */}
        {detailedResult && (
          <div>
            <h3 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '1rem' }}>
              📈 {STRATEGY_NAMES[selectedStrategy]} 詳細結果
            </h3>
            
            {/* Summary */}
            <div style={{ background: '#1f2937', borderRadius: '10px', padding: '1.5rem', marginBottom: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', textAlign: 'center' }}>
                <div>
                  <div style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '0.5rem' }}>総賭け数</div>
                  <div style={{ color: '#fff', fontSize: '1.5rem', fontWeight: 'bold' }}>{detailedResult.summary?.total_bets}</div>
                </div>
                <div>
                  <div style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '0.5rem' }}>的中数</div>
                  <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 'bold' }}>{detailedResult.summary?.total_wins}</div>
                </div>
                <div>
                  <div style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '0.5rem' }}>的中率</div>
                  <div style={{ color: '#06b6d4', fontSize: '1.5rem', fontWeight: 'bold' }}>{detailedResult.summary?.hit_rate}%</div>
                </div>
                <div>
                  <div style={{ color: '#9ca3af', fontSize: '0.875rem', marginBottom: '0.5rem' }}>ROI</div>
                  <div style={{ color: (detailedResult.summary?.roi || 0) >= 0 ? '#10b981' : '#ef4444', fontSize: '1.5rem', fontWeight: 'bold' }}>
                    {detailedResult.summary?.roi}%
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #374151', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.875rem' }}>
                <div style={{ color: '#9ca3af' }}>
                  投資額: <span style={{ color: '#fff' }}>{detailedResult.summary?.total_invested?.toLocaleString()}円</span>
                </div>
                <div style={{ color: '#9ca3af' }}>
                  回収額: <span style={{ color: (detailedResult.summary?.profit || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                    {detailedResult.summary?.total_return?.toLocaleString()}円 
                    ({(detailedResult.summary?.profit || 0) >= 0 ? '+' : ''}{detailedResult.summary?.profit?.toLocaleString()}円)
                  </span>
                </div>
              </div>
            </div>

            {/* Confidence Breakdown */}
            {detailedResult.confidence_breakdown && (
              <div style={{ background: '#1f2937', borderRadius: '10px', padding: '1.5rem', marginBottom: '1.5rem' }}>
                <h4 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '1rem' }}>🎖️ 信頼度別成績</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
                  {['S', 'A', 'B', 'C'].map(conf => {
                    const data = detailedResult.confidence_breakdown[conf] || {};
                    const confColors = { S: '#eab308', A: '#8b5cf6', B: '#3b82f6', C: '#6b7280' };
                    return (
                      <div key={conf} style={{ textAlign: 'center', background: 'rgba(55, 65, 81, 0.5)', borderRadius: '8px', padding: '1rem' }}>
                        <div style={{ color: confColors[conf], fontSize: '1.25rem', fontWeight: 'bold' }}>{conf}ランク</div>
                        <div style={{ color: '#9ca3af', fontSize: '0.75rem', margin: '0.25rem 0' }}>{data.bets || 0}件</div>
                        <div style={{ color: '#fff', fontWeight: 'bold' }}>{data.hit_rate || 0}%</div>
                        <div style={{ color: (data.roi || 0) >= 0 ? '#10b981' : '#ef4444', fontSize: '0.875rem' }}>
                          ROI: {data.roi || 0}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Venue Results */}
            {detailedResult.venue_results && Object.keys(detailedResult.venue_results).length > 0 && (
              <div style={{ background: '#1f2937', borderRadius: '10px', padding: '1.5rem' }}>
                <h4 style={{ color: '#fff', fontWeight: 'bold', marginBottom: '1rem' }}>🏟️ 会場別成績 (Top 12)</h4>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.5rem' }}>
                  {Object.entries(detailedResult.venue_results)
                    .sort((a, b) => (b[1].roi || 0) - (a[1].roi || 0))
                    .slice(0, 12)
                    .map(([venue, data]) => (
                      <div key={venue} style={{ textAlign: 'center', background: 'rgba(55, 65, 81, 0.5)', borderRadius: '6px', padding: '0.5rem', fontSize: '0.75rem' }}>
                        <div style={{ color: '#fff', fontWeight: 'bold' }}>{venue}</div>
                        <div style={{ color: '#9ca3af' }}>{data.bets}件</div>
                        <div style={{ color: (data.roi || 0) >= 0 ? '#10b981' : '#ef4444', fontWeight: 'bold' }}>
                          {data.roi}%
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#9ca3af' }}>
            <div style={{ marginBottom: '1rem' }}>分析中...</div>
            <div style={{ fontSize: '0.875rem' }}>大量のデータを処理しています。しばらくお待ちください。</div>
          </div>
        )}
      </div>
    </div>
  );
}
