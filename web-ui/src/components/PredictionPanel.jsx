/**
 * Prediction Panel Component
 */
import React from 'react';
import { Trophy, Copy, TrendingUp } from 'lucide-react';

const BOAT_COLORS = {
  1: { bg: '#FFFFFF', text: '#000000' },
  2: { bg: '#000000', text: '#FFFFFF' },
  3: { bg: '#FF0000', text: '#FFFFFF' },
  4: { bg: '#0000FF', text: '#FFFFFF' },
  5: { bg: '#FFFF00', text: '#000000' },
  6: { bg: '#00FF00', text: '#000000' },
};

const CONFIDENCE_COLORS = {
  S: 'var(--success)',
  A: 'var(--primary)',
  B: 'var(--warning)',
  C: 'var(--text-muted)',
};

export default function PredictionPanel({ prediction, onCopy }) {
  if (!prediction || !prediction.predictions) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        レースを選択してください
      </div>
    );
  }

  const { predictions, tips, confidence, insights, race_name, 展開予測 } = prediction;

  const copyForTeleboat = () => {
    if (predictions.length < 3) return;
    const top3 = predictions.slice(0, 3).map(p => p.boat_no);
    const text = `3連単 ${top3[0]}-${top3[1]}-${top3[2]} 100円`;
    navigator.clipboard.writeText(text);
    onCopy?.(text);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '900' }}>
              {prediction.jyo_cd} {prediction.race_no}R
            </h2>
            {race_name && (
              <span style={{ color: 'var(--secondary)', fontSize: '0.9rem' }}>{race_name}</span>
            )}
          </div>
          <div
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              background: CONFIDENCE_COLORS[confidence],
              color: '#fff',
              fontWeight: '900',
              fontSize: '1.2rem',
            }}
          >
            {confidence}
          </div>
        </div>

        {/* Insights */}
        {insights && insights.length > 0 && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {insights.map((insight, i) => (
              <span
                key={i}
                style={{
                  padding: '4px 12px',
                  borderRadius: '20px',
                  background: 'rgba(255,255,255,0.1)',
                  fontSize: '0.85rem',
                }}
              >
                {insight}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Predictions */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Trophy size={20} /> AI予測順位
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {predictions.map((pred, idx) => (
            <div
              key={pred.boat_no}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                padding: '0.75rem',
                borderRadius: '8px',
                background: idx === 0 ? 'rgba(255,215,0,0.15)' : 'rgba(255,255,255,0.05)',
                border: idx === 0 ? '2px solid gold' : 'none',
              }}
            >
              {/* Rank */}
              <span style={{ fontWeight: '900', fontSize: '1.2rem', width: '2rem', textAlign: 'center' }}>
                {idx + 1}
              </span>

              {/* Boat Number */}
              <span
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: BOAT_COLORS[pred.boat_no].bg,
                  color: BOAT_COLORS[pred.boat_no].text,
                  fontWeight: '900',
                  border: pred.boat_no === 1 ? '2px solid #ccc' : 'none',
                }}
              >
                {pred.boat_no}
              </span>

              {/* Racer Name */}
              <span style={{ flex: 1, fontWeight: '600' }}>{pred.racer_name}</span>

              {/* Ranks */}
              <span
                style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  background: pred.motor_rank === 'A' ? 'var(--success)' : pred.motor_rank === 'B' ? 'var(--warning)' : 'var(--text-muted)',
                  color: '#fff',
                }}
              >
                機{pred.motor_rank}
              </span>
              <span
                style={{
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.75rem',
                  background: pred.racer_rank === 'A' ? 'var(--success)' : pred.racer_rank === 'B' ? 'var(--warning)' : 'var(--text-muted)',
                  color: '#fff',
                }}
              >
                選{pred.racer_rank}
              </span>

              {/* Probability */}
              <div style={{ width: '80px' }}>
                <div
                  style={{
                    height: '8px',
                    borderRadius: '4px',
                    background: 'rgba(255,255,255,0.1)',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${pred.probability * 100}%`,
                      height: '100%',
                      background: 'var(--primary)',
                    }}
                  />
                </div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {(pred.probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Betting Tips */}
      {tips && (tips.nirentan?.length > 0 || tips.sanrentan?.length > 0) && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <TrendingUp size={20} /> 推奨買い目
            </h3>
            <button
              onClick={copyForTeleboat}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                background: 'var(--primary)',
                color: '#fff',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              <Copy size={16} /> コピー
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            {/* 2連単 */}
            <div>
              <h4 style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>2連単</h4>
              {tips.nirentan?.map((tip, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '0.5rem',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    marginBottom: '0.25rem',
                  }}
                >
                  <span style={{ fontWeight: '700' }}>{tip.combo}</span>
                  <span style={{ color: tip.ev > 1 ? 'var(--success)' : 'var(--text-muted)' }}>
                    EV: {tip.ev.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            {/* 3連単 */}
            <div>
              <h4 style={{ color: 'var(--text-muted)', marginBottom: '0.5rem' }}>3連単</h4>
              {tips.sanrentan?.map((tip, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '0.5rem',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '4px',
                    marginBottom: '0.25rem',
                  }}
                >
                  <span style={{ fontWeight: '700' }}>{tip.combo}</span>
                  <span style={{ color: tip.ev > 1 ? 'var(--success)' : 'var(--text-muted)' }}>
                    EV: {tip.ev.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 展開予測 */}
      {展開予測 && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>🏎️ レース展開予測</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {Object.entries(展開予測).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ width: '80px', fontWeight: '600' }}>{key}</span>
                <div style={{ flex: 1, height: '20px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(value, 100)}%`,
                      height: '100%',
                      background: key === '逃げ' ? 'var(--primary)' : key === '差し' ? 'var(--secondary)' : 'var(--warning)',
                    }}
                  />
                </div>
                <span style={{ width: '50px', textAlign: 'right', fontSize: '0.9rem' }}>
                  {value.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
