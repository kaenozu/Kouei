import React, { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, TrendingDown, RefreshCw, AlertTriangle } from 'lucide-react';

export const OddsAnalysis = ({ jyo, race, date }) => {
  const [odds, setOdds] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    if (jyo && race && date) {
      fetchOdds();
    }
  }, [jyo, race, date]);

  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchOdds, 30000); // 30秒ごとに更新
    }
    return () => clearInterval(interval);
  }, [autoRefresh, jyo, race, date]);

  const fetchOdds = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/odds/analysis?date=${date}&jyo=${jyo}&race=${race}`);
      const data = await resp.json();
      setOdds(data);
    } catch (e) {
      console.error('Failed to fetch odds', e);
    }
    setLoading(false);
  };

  const calculateEV = (probability, currentOdds) => {
    return probability * currentOdds;
  };

  if (!odds) {
    return (
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <DollarSign size={20} />
          <h3 style={{ fontWeight: '700' }}>オッズ分析</h3>
        </div>
        <p style={{ color: 'var(--text-dim)' }}>レースを選択するとオッズ情報が表示されます</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <DollarSign size={20} />
          <h3 style={{ fontWeight: '700' }}>オッズ分析</h3>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{
              padding: '0.5rem 1rem',
              background: autoRefresh ? 'var(--success)' : 'rgba(255,255,255,0.05)',
              color: autoRefresh ? '#000' : '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.75rem'
            }}
          >
            {autoRefresh ? '自動更新ON' : '自動更新OFF'}
          </button>
          <button
            onClick={fetchOdds}
            disabled={loading}
            style={{
              padding: '0.5rem',
              background: 'rgba(255,255,255,0.05)',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {odds.updated_at && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1rem' }}>
          最終更新: {odds.updated_at}
        </p>
      )}

      {/* 単勝オッズ */}
      {odds.tansho && (
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ marginBottom: '0.75rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>単勝オッズ</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
            {odds.tansho.map((o, i) => {
              const ev = o.probability ? calculateEV(o.probability, o.odds) : null;
              const isValue = ev && ev > 1.2;
              return (
                <div key={i} style={{
                  padding: '0.75rem',
                  background: isValue ? 'rgba(0,255,136,0.1)' : 'rgba(255,255,255,0.03)',
                  border: isValue ? '1px solid var(--success)' : '1px solid var(--glass-border)',
                  borderRadius: '8px',
                  textAlign: 'center'
                }}>
                  <div className={`boat-badge boat-${i + 1}`} style={{ margin: '0 auto 0.5rem', width: '24px', height: '24px', fontSize: '0.75rem' }}>
                    {i + 1}
                  </div>
                  <div style={{ fontSize: '1.25rem', fontWeight: '800' }}>{o.odds?.toFixed(1) || '-'}</div>
                  {ev && (
                    <div style={{ fontSize: '0.7rem', color: isValue ? 'var(--success)' : 'var(--text-dim)', marginTop: '0.25rem' }}>
                      EV: {ev.toFixed(2)}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 期待値が高い買い目 */}
      {odds.value_bets && odds.value_bets.length > 0 && (
        <div style={{ padding: '1rem', background: 'rgba(0,255,136,0.05)', borderRadius: '8px', border: '1px solid rgba(0,255,136,0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
            <TrendingUp size={18} color="var(--success)" />
            <span style={{ fontWeight: '700', color: 'var(--success)' }}>期待値プラスの買い目</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {odds.value_bets.slice(0, 5).map((bet, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>{bet.type}: {bet.combination}</span>
                <span style={{ fontWeight: '700' }}>
                  <span style={{ color: 'var(--text-dim)', marginRight: '0.5rem' }}>×{bet.odds?.toFixed(1)}</span>
                  <span style={{ color: 'var(--success)' }}>EV {bet.ev?.toFixed(2)}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* オッズ変動警告 */}
      {odds.alerts && odds.alerts.length > 0 && (
        <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,159,67,0.1)', borderRadius: '8px', border: '1px solid rgba(255,159,67,0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <AlertTriangle size={18} color="var(--warning)" />
            <span style={{ fontWeight: '700', color: 'var(--warning)' }}>オッズ変動アラート</span>
          </div>
          {odds.alerts.map((alert, i) => (
            <p key={i} style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{alert}</p>
          ))}
        </div>
      )}
    </div>
  );
};

export default OddsAnalysis;
