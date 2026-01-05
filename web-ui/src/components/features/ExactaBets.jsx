import React, { useState, useEffect } from 'react';
import { Zap, TrendingUp, RefreshCw, Target } from 'lucide-react';

export const ExactaBets = () => {
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [minProb, setMinProb] = useState(0.35);
  const [minEv, setMinEv] = useState(2.5);

  useEffect(() => {
    fetchPredictions();
  }, [minProb, minEv]);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/exacta?min_prob=${minProb}&min_ev=${minEv}&max_results=20`);
      const data = await resp.json();
      setPredictions(data);
    } catch (e) {
      console.error('Failed to fetch exacta predictions', e);
    }
    setLoading(false);
  };

  const confidenceColors = {
    'S': 'var(--success)',
    'A': '#00d4ff',
    'B': 'var(--warning)',
    'C': 'var(--text-muted)'
  };

  const boatColors = {
    1: '#fff', 2: '#000', 3: '#f00', 4: '#00f', 5: '#ff0', 6: '#0f0'
  };
  const boatBg = {
    1: '#fff', 2: '#000', 3: '#f00', 4: '#00f', 5: '#ff0', 6: '#0f0'
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Target color="var(--primary)" /> 2連単予測
          </h1>
          <p style={{ color: 'var(--text-dim)' }}>期待値ベースの2連単推奨（回収率重視）</p>
        </div>
        <button
          onClick={fetchPredictions}
          disabled={loading}
          style={{
            padding: '0.75rem 1.5rem',
            background: 'var(--primary)',
            color: '#000',
            border: 'none',
            borderRadius: '12px',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshCw size={18} className={loading ? 'spin' : ''} /> 更新
        </button>
      </div>

      {/* Strategy info */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem', background: 'linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.1))' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <TrendingUp size={20} /> 推奨戦略
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>バックテスト的中率</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>~30%</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>推定回収率</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--success)' }}>+97%</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>推奨条件</div>
            <div style={{ fontSize: '1rem', fontWeight: '600' }}>確率35%+ EV2.5+</div>
          </div>
        </div>
      </div>

      {/* Settings */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>フィルター設定</h3>
        <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>最小確率</div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[0.25, 0.30, 0.35, 0.40].map(p => (
                <button
                  key={p}
                  onClick={() => setMinProb(p)}
                  style={{
                    padding: '0.5rem 1rem',
                    background: minProb === p ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                    color: minProb === p ? '#000' : '#fff',
                    border: '1px solid',
                    borderColor: minProb === p ? 'var(--primary)' : 'var(--glass-border)',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  {p * 100}%
                </button>
              ))}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>最小EV</div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[1.5, 2.0, 2.5, 3.0].map(e => (
                <button
                  key={e}
                  onClick={() => setMinEv(e)}
                  style={{
                    padding: '0.5rem 1rem',
                    background: minEv === e ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                    color: minEv === e ? '#000' : '#fff',
                    border: '1px solid',
                    borderColor: minEv === e ? 'var(--primary)' : 'var(--glass-border)',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  {e.toFixed(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Predictions */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>
          本日の2連単推奨
          {predictions && <span style={{ marginLeft: '0.5rem', fontSize: '0.875rem', color: 'var(--text-dim)' }}>({predictions.total_predictions}件)</span>}
        </h3>
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>読み込み中...</div>
        ) : predictions && predictions.predictions && predictions.predictions.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {predictions.predictions.map((pred, i) => (
              <div
                key={i}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '80px 140px 120px 1fr 100px',
                  gap: '1rem',
                  alignItems: 'center',
                  padding: '1rem',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '12px',
                  border: '1px solid var(--glass-border)'
                }}
              >
                <div style={{
                  background: confidenceColors[pred.confidence],
                  color: '#000',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '6px',
                  fontWeight: '800',
                  textAlign: 'center',
                  fontSize: '0.75rem'
                }}>
                  {pred.confidence}ランク
                </div>
                <div>
                  <div style={{ fontWeight: '700' }}>{pred.jyo_name} {pred.race_no}R</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    {pred.start_time || '--:--'}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: boatBg[pred.first],
                    color: pred.first === 1 ? '#000' : pred.first === 2 ? '#fff' : '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    border: pred.first === 1 ? '2px solid #000' : 'none'
                  }}>
                    {pred.first}
                  </div>
                  <span style={{ fontSize: '1.5rem', color: 'var(--text-dim)' }}>→</span>
                  <div style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '50%',
                    background: boatBg[pred.second],
                    color: pred.second === 1 ? '#000' : pred.second === 2 ? '#fff' : '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800',
                    border: pred.second === 1 ? '2px solid #000' : 'none'
                  }}>
                    {pred.second}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.9rem' }}>
                    予測配当: <span style={{ fontWeight: '700', color: 'var(--warning)' }}>{pred.expected_odds.toFixed(1)}倍</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    EV: {pred.ev.toFixed(2)}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--success)' }}>
                    {(pred.probability * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>
            条件に合う2連単がありません
          </div>
        )}
      </div>
    </div>
  );
};

export default ExactaBets;
