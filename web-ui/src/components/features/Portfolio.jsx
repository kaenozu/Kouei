import React, { useState, useEffect } from 'react';
import { Briefcase, TrendingUp, AlertTriangle, RefreshCw } from 'lucide-react';

export const Portfolio = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [optimizing, setOptimizing] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState('');

  useEffect(() => {
    fetchStrategies();
  }, []);

  const fetchStrategies = async () => {
    try {
      const resp = await fetch('/api/betting/strategies');
      const data = await resp.json();
      setStrategies(data.strategies || []);
    } catch (e) {
      console.error('Failed to fetch strategies', e);
    }
  };

  const optimizePortfolio = async () => {
    setOptimizing(true);
    try {
      const resp = await fetch('/api/betting/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget: 10000,
          strategy: selectedStrategy || 'kelly'
        })
      });
      const data = await resp.json();
      setPortfolio(data);
    } catch (e) {
      console.error('Failed to optimize', e);
    }
    setOptimizing(false);
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>
        <Briefcase style={{ display: 'inline', marginRight: '0.5rem' }} /> ポートフォリオ管理
      </h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>資金配分とリスク管理を最適化</p>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>ベッティング戦略</h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
          {strategies.map(s => (
            <button
              key={s.id}
              onClick={() => setSelectedStrategy(s.id)}
              style={{
                padding: '0.75rem 1.5rem',
                background: selectedStrategy === s.id ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                color: selectedStrategy === s.id ? '#000' : '#fff',
                border: '1px solid var(--glass-border)',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {s.name}
            </button>
          ))}
        </div>

        <button
          className="btn-primary"
          onClick={optimizePortfolio}
          disabled={optimizing}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={18} className={optimizing ? 'spin' : ''} />
          {optimizing ? '最適化中...' : 'ポートフォリオを最適化'}
        </button>
      </div>

      {portfolio && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>最適化結果</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>期待収益率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--success)' }}>
                {portfolio.expected_return ? (portfolio.expected_return * 100).toFixed(1) : 0}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>リスク</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--warning)' }}>
                {portfolio.risk ? (portfolio.risk * 100).toFixed(1) : 0}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>シャープレシオ</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                {portfolio.sharpe_ratio?.toFixed(2) || 'N/A'}
              </div>
            </div>
          </div>

          {portfolio.allocations && portfolio.allocations.length > 0 && (
            <div>
              <h4 style={{ marginBottom: '0.75rem', fontWeight: '600' }}>推奨資金配分</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {portfolio.allocations.slice(0, 10).map((alloc, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px'
                  }}>
                    <span>{alloc.race || alloc.bet}</span>
                    <span style={{ fontWeight: '700', color: 'var(--primary)' }}>
                      ¥{alloc.amount?.toLocaleString() || 0}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {portfolio.warnings && portfolio.warnings.length > 0 && (
            <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,159,67,0.1)', borderRadius: '8px', border: '1px solid rgba(255,159,67,0.3)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--warning)' }}>
                <AlertTriangle size={18} />
                <span>注意事項</span>
              </div>
              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem', color: 'var(--text-dim)' }}>
                {portfolio.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Portfolio;
