import React, { useState, useEffect } from 'react';
import { Zap, TrendingUp, AlertCircle, RefreshCw, Clock, ChevronRight } from 'lucide-react';

export const SmartBets = () => {
  const [bets, setBets] = useState(null);
  const [threshold, setThreshold] = useState(0.8);
  const [loading, setLoading] = useState(false);
  const [backtest, setBacktest] = useState(null);

  useEffect(() => {
    fetchBets();
    fetchBacktest();
  }, [threshold]);

  const fetchBets = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`/api/smart-bets?threshold=${threshold}&max_bets=20`);
      const data = await resp.json();
      setBets(data);
    } catch (e) {
      console.error('Failed to fetch smart bets', e);
    }
    setLoading(false);
  };

  const fetchBacktest = async () => {
    try {
      const resp = await fetch(`/api/smart-bets/backtest?threshold=${threshold}&days=7`);
      const data = await resp.json();
      setBacktest(data);
    } catch (e) {
      console.error('Failed to fetch backtest', e);
    }
  };

  const confidenceColors = {
    'S': 'var(--success)',
    'A': '#00d4ff',
    'B': 'var(--warning)',
    'C': 'var(--text-muted)'
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap color="var(--warning)" /> スマートベット
          </h1>
          <p style={{ color: 'var(--text-dim)' }}>高確率レースのみに厳選した推奨買い目</p>
        </div>
        <button
          onClick={() => { fetchBets(); fetchBacktest(); }}
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

      {/* Threshold selector */}
      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>確率閾値設定</h3>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {[0.7, 0.8, 0.9].map(t => (
            <button
              key={t}
              onClick={() => setThreshold(t)}
              style={{
                padding: '0.75rem 1.5rem',
                background: threshold === t ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
                color: threshold === t ? '#000' : '#fff',
                border: '1px solid',
                borderColor: threshold === t ? 'var(--primary)' : 'var(--glass-border)',
                borderRadius: '10px',
                fontWeight: '700',
                cursor: 'pointer'
              }}
            >
              {t * 100}%以上
            </button>
          ))}
        </div>
      </div>

      {/* Backtest stats */}
      {backtest && backtest.summary && (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem', background: 'linear-gradient(135deg, rgba(0,255,136,0.1), rgba(0,212,255,0.1))' }}>
          <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingUp size={20} /> バックテスト結果（過去7日間）
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>総ベット数</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>{backtest.summary.total_bets}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>的中率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--success)' }}>{backtest.summary.hit_rate}%</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>勝利数</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>{backtest.summary.total_wins}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>ROI</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: backtest.summary.roi > 0 ? 'var(--success)' : 'var(--error)' }}>
                {backtest.summary.roi > 1000 ? `${(backtest.summary.roi / 100).toFixed(0)}x` : `${backtest.summary.roi}%`}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Today's smart bets */}
      <div className="card" style={{ padding: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>
          本日の推奨レース
          {bets && <span style={{ marginLeft: '0.5rem', fontSize: '0.875rem', color: 'var(--text-dim)' }}>({bets.total_bets}件)</span>}
        </h3>
        
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>読み込み中...</div>
        ) : bets && bets.bets && bets.bets.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {bets.bets.map((bet, i) => {
              // Format time until race from API
              const formatTimeUntil = (minutes) => {
                if (minutes === null || minutes === undefined) return null;
                if (minutes <= 0) return 'まもなく';
                if (minutes < 60) return `${minutes}分後`;
                return `${Math.floor(minutes/60)}時間${minutes%60}分後`;
              };
              const timeUntil = formatTimeUntil(bet.minutes_until);
              const isUpcoming = bet.status === 'upcoming' || (bet.minutes_until !== null && bet.minutes_until <= 15);
              const isHot = bet.minutes_until !== null && bet.minutes_until <= 5;
              
              return (
                <div
                  key={i}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '80px 140px 50px 1fr 120px',
                    gap: '1rem',
                    alignItems: 'center',
                    padding: '1rem',
                    background: isHot
                      ? 'linear-gradient(135deg, rgba(255,50,50,0.15), rgba(255,100,0,0.1))'
                      : isUpcoming 
                        ? 'linear-gradient(135deg, rgba(255,200,0,0.1), rgba(255,100,0,0.05))'
                        : 'rgba(255,255,255,0.03)',
                    borderRadius: '12px',
                    border: isHot
                      ? '2px solid rgba(255,100,100,0.5)'
                      : isUpcoming 
                        ? '1px solid rgba(255,200,0,0.3)'
                        : '1px solid var(--glass-border)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    animation: isHot ? 'pulse 2s infinite' : 'none'
                  }}
                  onClick={() => window.location.href = `/race?date=${bet.date}&jyo=${bet.jyo_cd}&race=${bet.race_no}`}
                >
                  <div style={{
                    background: confidenceColors[bet.confidence],
                    color: '#000',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '6px',
                    fontWeight: '800',
                    textAlign: 'center',
                    fontSize: '0.75rem'
                  }}>
                    {bet.confidence}ランク
                  </div>
                  <div>
                    <div style={{ fontWeight: '700', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {bet.jyo_name}
                      <span style={{ 
                        fontSize: '0.7rem', 
                        background: 'rgba(255,255,255,0.1)', 
                        padding: '0.1rem 0.4rem', 
                        borderRadius: '4px' 
                      }}>{bet.race_no}R</span>
                    </div>
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: isHot ? 'var(--error)' : isUpcoming ? 'var(--warning)' : 'var(--text-dim)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      marginTop: '0.25rem',
                      fontWeight: isHot ? '700' : '400'
                    }}>
                      <Clock size={12} />
                      {bet.start_time || '--:--'}
                      {timeUntil && <span style={{ marginLeft: '0.25rem' }}>({timeUntil})</span>}
                      {isHot && <span style={{ marginLeft: '0.5rem', background: 'var(--error)', color: '#fff', padding: '0.1rem 0.4rem', borderRadius: '4px', fontSize: '0.65rem' }}>🔥 HOT</span>}
                    </div>
                  </div>
                  <div className={`boat-badge boat-${bet.boat_no}`} style={{
                    width: '32px',
                    height: '32px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '800'
                  }}>
                    {bet.boat_no}
                  </div>
                  <div>
                    <div style={{ fontWeight: '600' }}>{bet.racer_name}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      単勝推奨
                      {bet.real_odds && (
                        <span style={{ color: 'var(--warning)' }}>
                          オッズ {bet.real_odds.toFixed(1)}倍
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div>
                      <div style={{ fontSize: '1.25rem', fontWeight: '800', color: 'var(--success)' }}>
                        {(bet.probability * 100).toFixed(1)}%
                      </div>
                      {bet.ev > 1.1 && (
                        <div style={{ fontSize: '0.7rem', color: 'var(--warning)' }}>
                          EV {bet.ev.toFixed(2)}
                        </div>
                      )}
                    </div>
                    <ChevronRight size={16} style={{ color: 'var(--text-dim)' }} />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>
            <AlertCircle size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
            <p>本日は{threshold * 100}%以上の高確率レースがありません</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SmartBets;
