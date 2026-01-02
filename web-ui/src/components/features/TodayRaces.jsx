import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export const TodayRaces = ({ onSelectRace }) => {
  const [todayRaces, setTodayRaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchTodayRaces();
  }, []);

  const fetchTodayRaces = async () => {
    setLoading(true);
    try {
      const resp = await fetch('http://localhost:8001/api/today');
      const data = await resp.json();
      if (data && data.races) {
        setTodayRaces(data.races);
      } else {
        setTodayRaces([]);
      }
    } catch (e) {
      console.error('Failed to fetch today races', e);
    }
    setLoading(false);
  };

  const filteredRaces = todayRaces.filter(race => {
    if (filter === 'all') return true;
    if (filter === 'upcoming') return race.status !== 'finished';
    if (filter === 'finished') return race.status === 'finished';
    return true;
  });

  const groupedRaces = filteredRaces.reduce((acc, race) => {
    const key = race.jyo_name || race.jyo_cd;
    if (!acc[key]) acc[key] = [];
    acc[key].push(race);
    return acc;
  }, {});

  return (
    <div style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: '900', marginBottom: '0.5rem' }}>
            <Clock style={{ display: 'inline', marginRight: '0.5rem' }} /> 本日のレース
          </h1>
          <p style={{ color: 'var(--text-dim)' }}>全場のレース一覧</p>
        </div>
        <button
          onClick={fetchTodayRaces}
          disabled={loading}
          className="btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={18} className={loading ? 'spin' : ''} />
          更新
        </button>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
        {['all', 'upcoming', 'finished'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '0.5rem 1rem',
              background: filter === f ? 'var(--primary)' : 'rgba(255,255,255,0.05)',
              color: filter === f ? '#000' : '#fff',
              border: 'none',
              borderRadius: '20px',
              cursor: 'pointer',
              fontSize: '0.875rem'
            }}
          >
            {f === 'all' ? '全て' : f === 'upcoming' ? '未開催' : '終了'}
          </button>
        ))}
      </div>

      {Object.keys(groupedRaces).length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
          <Clock size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
          <p style={{ color: 'var(--text-dim)' }}>レース情報がありません</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {Object.entries(groupedRaces).map(([venue, races]) => (
            <div key={venue} className="card" style={{ padding: '1rem' }}>
              <h3 style={{ marginBottom: '1rem', fontWeight: '700', color: 'var(--primary)' }}>
                🚤 {venue}
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.75rem' }}>
                {races.map((race, i) => (
                  <div
                    key={i}
                    onClick={() => onSelectRace && onSelectRace(race)}
                    style={{
                      padding: '1rem',
                      background: race.status === 'finished' ? 'rgba(255,255,255,0.02)' : 'rgba(0,242,255,0.05)',
                      borderRadius: '12px',
                      border: '1px solid var(--glass-border)',
                      cursor: onSelectRace ? 'pointer' : 'default',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontWeight: '800', fontSize: '1.1rem' }}>{race.race_no}R</span>
                      <span style={{ fontSize: '0.875rem', color: 'var(--text-dim)' }}>{race.start_time}</span>
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                      {race.race_name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      {race.status === 'finished' ? (
                        <><CheckCircle2 size={14} color="var(--success)" /> <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>終了</span></>
                      ) : race.has_prediction ? (
                        <><AlertCircle size={14} color="var(--primary)" /> <span style={{ fontSize: '0.75rem', color: 'var(--primary)' }}>予測あり</span></>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>待機中</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TodayRaces;
