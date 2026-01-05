import React, { useState, useEffect } from 'react';

const API_BASE = '';

export default function ValueBets() {
  const [valueBets, setValueBets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [minEV, setMinEV] = useState(1.05);
  const [minProb, setMinProb] = useState(0.15);
  const [betTypes, setBetTypes] = useState('win,exacta');

  useEffect(() => {
    fetchValueBets();
  }, []);

  const fetchValueBets = async () => {
    setLoading(true);
    try {
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const res = await fetch(
        `${API_BASE}/api/odds/value-bets?date=${date}&min_ev=${minEV}&min_prob=${minProb}&bet_types=${betTypes}`
      );
      const data = await res.json();
      setValueBets(data.value_bets || []);
      setSummary(data.summary || null);
    } catch (err) {
      console.error('Error:', err);
    }
    setLoading(false);
  };

  const getConfidenceColor = (conf) => {
    const colors = {
      'S': '#eab308',
      'A': '#a855f7', 
      'B': '#3b82f6',
      'C': '#6b7280'
    };
    return colors[conf] || colors['C'];
  };

  const getEVColor = (ev) => {
    if (ev >= 1.5) return '#facc15';
    if (ev >= 1.3) return '#4ade80';
    if (ev >= 1.1) return '#22d3ee';
    return '#9ca3af';
  };

  return (
    <div>
      {/* Header & Controls */}
      <div style={{ background: 'rgba(17, 24, 39, 0.9)', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff', margin: 0 }}>💰 バリューベット発見</h2>
          <button
            onClick={fetchValueBets}
            disabled={loading}
            style={{ 
              padding: '0.5rem 1rem', 
              background: loading ? '#4b5563' : '#06b6d4', 
              color: '#fff', 
              borderRadius: '8px', 
              border: 'none', 
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {loading ? '分析中...' : '🔍 分析実行'}
          </button>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
          <div>
            <label style={{ color: '#9ca3af', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>最小期待値</label>
            <select 
              value={minEV} 
              onChange={(e) => setMinEV(parseFloat(e.target.value))}
              style={{ width: '100%', background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '8px', border: 'none' }}
            >
              <option value="1.0">1.0 (全て)</option>
              <option value="1.05">1.05 (+5%)</option>
              <option value="1.1">1.1 (+10%)</option>
              <option value="1.2">1.2 (+20%)</option>
              <option value="1.3">1.3 (+30%)</option>
            </select>
          </div>
          <div>
            <label style={{ color: '#9ca3af', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>最小確率</label>
            <select 
              value={minProb} 
              onChange={(e) => setMinProb(parseFloat(e.target.value))}
              style={{ width: '100%', background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '8px', border: 'none' }}
            >
              <option value="0.1">10%以上</option>
              <option value="0.15">15%以上</option>
              <option value="0.2">20%以上</option>
              <option value="0.3">30%以上</option>
            </select>
          </div>
          <div>
            <label style={{ color: '#9ca3af', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>ベットタイプ</label>
            <select 
              value={betTypes} 
              onChange={(e) => setBetTypes(e.target.value)}
              style={{ width: '100%', background: '#1f2937', color: '#fff', padding: '0.5rem', borderRadius: '8px', border: 'none' }}
            >
              <option value="win">単勝のみ</option>
              <option value="exacta">2連単のみ</option>
              <option value="win,exacta">単勝 + 2連単</option>
            </select>
          </div>
        </div>

        {/* Summary */}
        {summary && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', background: '#1f2937', borderRadius: '8px', padding: '1rem' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>分析レース</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>{summary.races_analyzed}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>バリューベット</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#22d3ee' }}>{summary.total_value_bets}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>平均EV</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: getEVColor(summary.avg_ev) }}>
                {summary.avg_ev > 0 ? `+${((summary.avg_ev - 1) * 100).toFixed(0)}%` : '-'}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#9ca3af', fontSize: '0.75rem' }}>平均エッジ</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#4ade80' }}>
                {summary.avg_edge > 0 ? `+${summary.avg_edge.toFixed(1)}%` : '-'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Value Bets List */}
      <div style={{ background: 'rgba(17, 24, 39, 0.9)', borderRadius: '12px', padding: '1.5rem', marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', color: '#fff', marginBottom: '1rem' }}>🎯 推奨ベット（期待値順）</h3>
        
        {loading ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: '2rem' }}>分析中...</div>
        ) : valueBets.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: '2rem' }}>
            条件に合うバリューベットが見つかりませんでした
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
            {valueBets.slice(0, 20).map((bet, idx) => (
              <div 
                key={idx} 
                style={{ 
                  background: '#1f2937', 
                  borderRadius: '8px', 
                  padding: '1rem',
                  border: bet.confidence === 'S' ? '1px solid #eab308' : 'none'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ 
                      padding: '2px 8px', 
                      borderRadius: '4px', 
                      fontSize: '0.75rem', 
                      fontWeight: 'bold',
                      background: getConfidenceColor(bet.confidence),
                      color: bet.confidence === 'S' ? '#000' : '#fff'
                    }}>
                      {bet.confidence}
                    </span>
                    <span style={{ color: '#fff', fontWeight: 'bold' }}>
                      {bet.venue_name} {bet.race_no}R
                    </span>
                  </div>
                  <span style={{ 
                    color: getEVColor(bet.expected_value), 
                    fontWeight: 'bold',
                    fontSize: '1.125rem'
                  }}>
                    +{((bet.expected_value - 1) * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', fontSize: '0.875rem' }}>
                  <div>
                    <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>タイプ</div>
                    <div style={{ color: '#fff' }}>{bet.bet_type === 'win' ? '単勝' : '2連単'}</div>
                  </div>
                  <div>
                    <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>選択</div>
                    <div style={{ color: '#22d3ee', fontWeight: 'bold' }}>{bet.selection}</div>
                  </div>
                  <div>
                    <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>AI確率</div>
                    <div style={{ color: '#fff' }}>{(bet.ai_probability * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div style={{ color: '#6b7280', fontSize: '0.75rem' }}>オッズ</div>
                    <div style={{ color: '#fff' }}>{bet.market_odds}倍</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Explanation */}
      <div style={{ background: 'rgba(17, 24, 39, 0.9)', borderRadius: '12px', padding: '1.5rem' }}>
        <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', color: '#fff', marginBottom: '1rem' }}>📖 バリューベットとは</h3>
        <div style={{ color: '#9ca3af', lineHeight: '1.75' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong style={{ color: '#22d3ee' }}>期待値（EV）</strong> = AI予測確率 × オッズ
          </p>
          <p style={{ marginBottom: '0.5rem' }}>
            EV &gt; 1.0 の場合、長期的に利益が期待できる「バリューベット」です。
          </p>
          <p style={{ marginBottom: '0.5rem' }}>
            例: 確率30%で5倍のオッズ → EV = 0.3 × 5 = 1.5 (+50%)
          </p>
          <p style={{ color: '#facc15' }}>
            ⚠️ オッズは推定値です。実際のオッズは変動します。
          </p>
        </div>
      </div>
    </div>
  );
}
