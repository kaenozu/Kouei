import React, { useState, useEffect } from 'react';
import { Clock, ChevronRight, Zap, RefreshCw } from 'lucide-react';

export const UpcomingBets = ({ onSelectRace }) => {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBets();
    // Refresh every 60 seconds
    const interval = setInterval(fetchBets, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchBets = async () => {
    try {
      const resp = await fetch('/api/smart-bets?threshold=0.7&max_bets=5');
      const data = await resp.json();
      setBets(data.bets || []);
    } catch (e) {
      console.error('Failed to fetch upcoming bets', e);
    }
    setLoading(false);
  };

  const formatTimeUntil = (minutes) => {
    if (minutes === null || minutes === undefined) return null;
    if (minutes <= 0) return 'まもなく';
    if (minutes < 60) return `${minutes}分後`;
    return `${Math.floor(minutes/60)}時間${minutes%60}分`;
  };

  const confidenceColors = {
    'S': 'var(--success)',
    'A': '#00d4ff',
    'B': 'var(--warning)',
    'C': 'var(--text-muted)'
  };

  if (loading) {
    return (
      <div className="card" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Zap size={20} color="var(--warning)" />
          <h3 style={{ margin: 0, fontWeight: '800' }}>直近の推奨レース</h3>
        </div>
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)' }}>
          <RefreshCw className="spin" size={24} />
        </div>
      </div>
    );
  }

  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Zap size={20} color="var(--warning)" />
          <h3 style={{ margin: 0, fontWeight: '800' }}>直近の推奨レース</h3>
        </div>
        <button
          onClick={fetchBets}
          style={{
            background: 'transparent',
            border: '1px solid var(--glass-border)',
            borderRadius: '8px',
            padding: '0.4rem 0.8rem',
            color: 'var(--text-dim)',
            cursor: 'pointer',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem'
          }}
        >
          <RefreshCw size={12} /> 更新
        </button>
      </div>

      {bets.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-dim)' }}>
          現在、推奨レースがありません
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {bets.map((bet, i) => {
            const isHot = bet.minutes_until !== null && bet.minutes_until <= 5;
            const isUpcoming = bet.minutes_until !== null && bet.minutes_until <= 15;
            
            return (
              <div
                key={i}
                onClick={() => onSelectRace && onSelectRace(bet.jyo_cd, bet.race_no)}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '60px 1fr 80px',
                  gap: '0.75rem',
                  alignItems: 'center',
                  padding: '0.75rem',
                  background: isHot 
                    ? 'linear-gradient(135deg, rgba(255,50,50,0.1), rgba(255,100,0,0.05))'
                    : isUpcoming
                      ? 'rgba(255,200,0,0.05)'
                      : 'rgba(255,255,255,0.02)',
                  borderRadius: '10px',
                  border: isHot 
                    ? '1px solid rgba(255,100,100,0.3)'
                    : '1px solid var(--glass-border)',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{
                  background: confidenceColors[bet.confidence],
                  color: '#000',
                  padding: '0.2rem 0.4rem',
                  borderRadius: '4px',
                  fontWeight: '800',
                  textAlign: 'center',
                  fontSize: '0.65rem'
                }}>
                  {bet.confidence}ランク
                </div>
                
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>{bet.jyo_name}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--primary)' }}>{bet.race_no}R</span>
                    {isHot && <span style={{ background: 'var(--error)', color: '#fff', padding: '0.1rem 0.3rem', borderRadius: '3px', fontSize: '0.6rem' }}>🔥 HOT</span>}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: isHot ? 'var(--error)' : 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Clock size={10} />
                    {bet.start_time}
                    {bet.minutes_until !== null && <span>({formatTimeUntil(bet.minutes_until)})</span>}
                  </div>
                </div>
                
                <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: '800', color: 'var(--success)' }}>
                    {(bet.probability * 100).toFixed(0)}%
                  </span>
                  <ChevronRight size={14} color="var(--text-dim)" />
                </div>
              </div>
            );
          })}
        </div>
      )}
      
      <div style={{ marginTop: '1rem', textAlign: 'center' }}>
        <a 
          href="#" 
          onClick={(e) => { e.preventDefault(); window.location.hash = 'highvalue'; }}
          style={{ fontSize: '0.75rem', color: 'var(--primary)', textDecoration: 'none' }}
        >
          すべての推奨レースを見る →
        </a>
      </div>
    </div>
  );
};

export default UpcomingBets;
