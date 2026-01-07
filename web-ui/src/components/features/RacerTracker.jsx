import React, { useState } from 'react';
import { Trophy, Search, TrendingUp, TrendingDown } from 'lucide-react';

export const RacerTracker = () => {
  const [racerSearch, setRacerSearch] = useState('');
  const [racerStats, setRacerStats] = useState(null);
  const [racerLoading, setRacerLoading] = useState(false);

  const searchRacer = async () => {
    if (!racerSearch) return;
    setRacerLoading(true);
    try {
      const resp = await fetch(`/api/racer/${racerSearch}`);
      const data = await resp.json();
      setRacerStats(data);
    } catch (e) {
      console.error('Failed to search racer', e);
    }
    setRacerLoading(false);
  };

  return (
    <div style={{ padding: '1rem', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>
        <Trophy style={{ display: 'inline', marginRight: '0.5rem' }} /> 選手追跡
      </h1>
      <p style={{ color: 'var(--text-dim)', marginBottom: '2rem' }}>選手の成績と傾向を追跡</p>

      <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <input
            type="text"
            value={racerSearch}
            onChange={e => setRacerSearch(e.target.value)}
            placeholder="選手名またはIDを入力"
            style={{
              flex: 1, padding: '1rem',
              background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
              borderRadius: '8px', color: '#fff', fontSize: '1rem'
            }}
            onKeyPress={e => e.key === 'Enter' && searchRacer()}
          />
          <button
            className="btn-primary"
            onClick={searchRacer}
            disabled={racerLoading}
            style={{ padding: '1rem 2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Search size={18} />
            {racerLoading ? '検索中...' : '検索'}
          </button>
        </div>
      </div>

      {racerStats && (
        <div className="card" style={{ padding: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{
              width: '80px', height: '80px', borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--primary), var(--success))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2rem', fontWeight: '900'
            }}>
              {racerStats.name?.charAt(0) || '?'}
            </div>
            <div>
              <h2 style={{ fontSize: '1.75rem', fontWeight: '800' }}>{racerStats.name || '不明'}</h2>
              <p style={{ color: 'var(--text-dim)' }}>ID: {racerStats.racer_id}</p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>出走数</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>{racerStats.total_races || 0}</div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>勝率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--success)' }}>
                {racerStats.win_rate ? (racerStats.win_rate * 100).toFixed(1) : 0}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>2連率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--primary)' }}>
                {racerStats.top2_rate ? (racerStats.top2_rate * 100).toFixed(1) : 0}%
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>3連率</div>
              <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                {racerStats.top3_rate ? (racerStats.top3_rate * 100).toFixed(1) : 0}%
              </div>
            </div>
          </div>

          {racerStats.course_stats && (
            <div>
              <h3 style={{ marginBottom: '1rem', fontWeight: '700' }}>コース別成績</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.5rem' }}>
                {[1, 2, 3, 4, 5, 6].map(course => {
                  const stat = racerStats.course_stats?.[course] || { win_rate: 0 };
                  return (
                    <div key={course} style={{
                      textAlign: 'center', padding: '1rem',
                      background: `rgba(${course === 1 ? '255,255,255' : course === 2 ? '0,0,0' : course === 3 ? '255,0,0' : course === 4 ? '0,0,255' : course === 5 ? '255,255,0' : '0,255,0'}, 0.1)`,
                      borderRadius: '8px'
                    }}>
                      <div style={{ fontSize: '1.25rem', fontWeight: '800', marginBottom: '0.25rem' }}>{course}</div>
                      <div style={{ fontSize: '0.875rem', color: stat.win_rate > 0.2 ? 'var(--success)' : 'var(--text-dim)' }}>
                        {(stat.win_rate * 100).toFixed(0)}%
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {racerStats.recent_trend && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                {racerStats.recent_trend > 0 ? (
                  <><TrendingUp color="var(--success)" /> <span style={{ color: 'var(--success)' }}>上昇傾向</span></>
                ) : (
                  <><TrendingDown color="var(--danger)" /> <span style={{ color: 'var(--danger)' }}>下降傾向</span></>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RacerTracker;
