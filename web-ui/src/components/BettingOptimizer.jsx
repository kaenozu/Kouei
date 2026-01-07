/**
 * Betting Optimizer Component
 * 買い目最適化パネル
 */
import React, { useState } from 'react';
import { Zap, Calculator, DollarSign } from 'lucide-react';
import api from '../utils/api';

const BET_TYPES = [
  { value: 'tansho', label: '単勝' },
  { value: 'nirentan', label: '2連単' },
  { value: 'nirenufuku', label: '2連複' },
  { value: 'sanrentan', label: '3連単' },
  { value: 'sanrenfuku', label: '3連複' },
];

const FORMATION_TYPES = [
  { value: 'box', label: 'ボックス' },
  { value: 'formation', label: 'フォーメーション' },
  { value: 'flow', label: '流し' },
];

export default function BettingOptimizer({ date, jyo, race }) {
  const [mode, setMode] = useState('kelly'); // kelly or formation
  const [budget, setBudget] = useState(10000);
  const [betType, setBetType] = useState('sanrentan');
  const [formationType, setFormationType] = useState('box');
  const [kellyFraction, setKellyFraction] = useState(0.5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const optimize = async () => {
    setLoading(true);
    try {
      if (mode === 'kelly') {
        const res = await api.optimizeBetting({
          date,
          jyo,
          race,
          budget,
          bet_type: betType,
          kelly_fraction: kellyFraction,
        });
        setResult(res);
      } else {
        const res = await api.optimizeFormation(date, jyo, race, budget, formationType);
        setResult(res);
      }
    } catch (err) {
      console.error('Optimization failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Calculator size={20} /> 買い目最適化
      </h3>

      {/* Mode Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setMode('kelly')}
          style={{
            flex: 1,
            padding: '0.75rem',
            borderRadius: '8px',
            border: 'none',
            background: mode === 'kelly' ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
            color: '#fff',
            cursor: 'pointer',
            fontWeight: mode === 'kelly' ? '700' : '400',
          }}
        >
          Kelly基準
        </button>
        <button
          onClick={() => setMode('formation')}
          style={{
            flex: 1,
            padding: '0.75rem',
            borderRadius: '8px',
            border: 'none',
            background: mode === 'formation' ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
            color: '#fff',
            cursor: 'pointer',
            fontWeight: mode === 'formation' ? '700' : '400',
          }}
        >
          フォーメーション
        </button>
      </div>

      {/* Settings */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            資金 (円)
          </label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value))}
            min={100}
            step={100}
            style={{
              width: '100%',
              padding: '0.75rem',
              borderRadius: '8px',
              border: '1px solid var(--glass-border)',
              background: 'rgba(255,255,255,0.05)',
              color: '#fff',
            }}
          />
        </div>

        {mode === 'kelly' ? (
          <>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                貭式
              </label>
              <select
                value={betType}
                onChange={(e) => setBetType(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  border: '1px solid var(--glass-border)',
                  background: 'rgba(255,255,255,0.05)',
                  color: '#fff',
                }}
              >
                {BET_TYPES.map((bt) => (
                  <option key={bt.value} value={bt.value}>
                    {bt.label}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Kelly係数: {kellyFraction}
              </label>
              <input
                type="range"
                value={kellyFraction}
                onChange={(e) => setKellyFraction(Number(e.target.value))}
                min={0.1}
                max={1.0}
                step={0.1}
                style={{ width: '100%' }}
              />
            </div>
          </>
        ) : (
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              フォーメーションタイプ
            </label>
            <select
              value={formationType}
              onChange={(e) => setFormationType(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                borderRadius: '8px',
                border: '1px solid var(--glass-border)',
                background: 'rgba(255,255,255,0.05)',
                color: '#fff',
              }}
            >
              {FORMATION_TYPES.map((ft) => (
                <option key={ft.value} value={ft.value}>
                  {ft.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Optimize Button */}
      <button
        onClick={optimize}
        disabled={loading}
        style={{
          width: '100%',
          padding: '1rem',
          borderRadius: '8px',
          border: 'none',
          background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
          color: '#fff',
          fontWeight: '700',
          cursor: loading ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
        }}
      >
        <Zap size={20} />
        {loading ? '計算中...' : '最適化実行'}
      </button>

      {/* Results */}
      {result && result.status === 'success' && (
        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ marginBottom: '1rem', color: 'var(--success)' }}>✅ 最適化結果</h4>

          {mode === 'kelly' && result.recommendations && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>総貭け金</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>¥{result.total_bet?.toLocaleString()}</div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>期待リターン</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900', color: 'var(--success)' }}>
                    ¥{result.expected_return?.toLocaleString()}
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>組数</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>{result.recommendations?.length}</div>
                </div>
              </div>

              <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                {result.recommendations?.map((rec, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem',
                      borderBottom: '1px solid var(--glass-border)',
                    }}
                  >
                    <span style={{ fontWeight: '700', fontSize: '1.1rem' }}>{rec.combo}</span>
                    <span style={{ color: 'var(--text-muted)' }}>オッズ: {rec.odds?.toFixed(1)}</span>
                    <span style={{ color: rec.ev > 1 ? 'var(--success)' : 'var(--text-muted)' }}>
                      EV: {rec.ev?.toFixed(2)}
                    </span>
                    <span style={{ fontWeight: '700', color: 'var(--primary)' }}>
                      ¥{rec.amount?.toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}

          {mode === 'formation' && result.combos && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>軸艇</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>{result.top_boats?.join('-')}</div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>点数</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>{result.total_combos}点</div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>各点金額</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: '900' }}>¥{result.amount_per_combo?.toLocaleString()}</div>
                </div>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {result.combos?.map((combo, i) => (
                  <span
                    key={i}
                    style={{
                      padding: '0.5rem 1rem',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.1)',
                      fontWeight: '600',
                    }}
                  >
                    {combo}
                  </span>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
