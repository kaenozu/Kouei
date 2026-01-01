import React, { useState, useEffect } from 'react';
import { Target, TrendingUp, Star, AlertCircle, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const HighValueRaces = () => {
  const [races, setRaces] = useState([]);
  const [loading, setLoading] = useState(false);
  const [minProb, setMinProb] = useState(0.65);
  const [stats, setStats] = useState({ count: 0, avgProb: 0 });

  const fetchHighValueRaces = async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/api/notifications/high-value-races?threshold=${minProb}`);
      const data = await resp.json();
      setRaces(data.races || []);
      
      // 統計計算
      const avgProb = data.races?.length > 0 
        ? data.races.reduce((sum, r) => sum + r.probability, 0) / data.races.length
        : 0;
      setStats({ count: data.count || 0, avgProb });
    } catch (e) {
      console.error('Failed to fetch high value races', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchHighValueRaces();
    // 5分ごとに更新
    const interval = setInterval(fetchHighValueRaces, 300000);
    return () => clearInterval(interval);
  }, [minProb]);

  const getConfidenceColor = (prob) => {
    if (prob >= 0.75) return '#00ff88';
    if (prob >= 0.65) return '#00f2ff';
    return '#ffd700';
  };

  return (
    <div style={{ padding: '2rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <Target size={32} color="#00f2ff" />
        <div>
          <h1 style={{ margin: 0, fontSize: '2rem', color: '#fff' }}>High Value Races</h1>
          <p style={{ margin: 0, color: '#888' }}>高確率レースを狙ってROI向上</p>
        </div>
        <button 
          onClick={fetchHighValueRaces}
          disabled={loading}
          style={{
            marginLeft: 'auto',
            padding: '0.5rem 1rem',
            background: 'rgba(0, 242, 255, 0.2)',
            border: '1px solid #00f2ff',
            borderRadius: '8px',
            color: '#00f2ff',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <RefreshCw size={16} className={loading ? 'spin' : ''} />
          更新
        </button>
      </div>

      {/* フィルター */}
      <div style={{ 
        background: 'rgba(255,255,255,0.05)', 
        borderRadius: '12px', 
        padding: '1.5rem',
        marginBottom: '2rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
          <div>
            <label style={{ color: '#888', display: 'block', marginBottom: '0.5rem' }}>
              最低確率閾値
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {[0.55, 0.60, 0.65, 0.70, 0.75].map(prob => (
                <button
                  key={prob}
                  onClick={() => setMinProb(prob)}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '8px',
                    border: minProb === prob ? '2px solid #00f2ff' : '1px solid #333',
                    background: minProb === prob ? 'rgba(0, 242, 255, 0.2)' : 'transparent',
                    color: minProb === prob ? '#00f2ff' : '#888',
                    cursor: 'pointer'
                  }}
                >
                  {(prob * 100).toFixed(0)}%
                </button>
              ))}
            </div>
          </div>
          
          <div style={{ 
            marginLeft: 'auto', 
            display: 'flex', 
            gap: '2rem',
            background: 'rgba(0,0,0,0.3)',
            padding: '1rem 2rem',
            borderRadius: '12px'
          }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#888', fontSize: '0.8rem' }}>対象レース</div>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: '#00f2ff' }}>{stats.count}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ color: '#888', fontSize: '0.8rem' }}>平均確率</div>
              <div style={{ fontSize: '2rem', fontWeight: '900', color: '#00ff88' }}>
                {(stats.avgProb * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 注意書き */}
      <div style={{
        background: 'rgba(255, 193, 7, 0.1)',
        border: '1px solid rgba(255, 193, 7, 0.3)',
        borderRadius: '12px',
        padding: '1rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <AlertCircle size={24} color="#ffc107" />
        <div style={{ color: '#ffc107' }}>
          <strong>戦略ヒント:</strong> 確率70%以上のレースに絞ることで、的中率が向上しROI改善が期待できます。
          ただし、低オッズになりやすいため、資金管理に注意してください。
        </div>
      </div>

      {/* レース一覧 */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', 
        gap: '1rem' 
      }}>
        {races.map((race, idx) => (
          <div 
            key={idx}
            style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '12px',
              padding: '1.5rem',
              border: `1px solid ${getConfidenceColor(race.probability)}30`
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div>
                <span style={{ 
                  background: 'rgba(0, 242, 255, 0.2)', 
                  padding: '0.25rem 0.5rem', 
                  borderRadius: '4px',
                  color: '#00f2ff',
                  fontSize: '0.8rem',
                  marginRight: '0.5rem'
                }}>
                  {race.jyo_name}
                </span>
                <span style={{ color: '#fff', fontWeight: '700' }}>
                  {race.race_no}R
                </span>
              </div>
              <div style={{
                background: `${getConfidenceColor(race.probability)}20`,
                color: getConfidenceColor(race.probability),
                padding: '0.25rem 0.75rem',
                borderRadius: '999px',
                fontWeight: '900',
                fontSize: '0.9rem'
              }}>
                {(race.probability * 100).toFixed(1)}%
              </div>
            </div>
            
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '1rem',
              background: 'rgba(0,0,0,0.3)',
              padding: '1rem',
              borderRadius: '8px'
            }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #ff6b6b, #ffd93d)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '900',
                fontSize: '1.2rem',
                color: '#000'
              }}>
                {race.boat_no}
              </div>
              <div>
                <div style={{ color: '#888', fontSize: '0.8rem' }}>推奨艇</div>
                <div style={{ color: '#fff', fontWeight: '600' }}>
                  {race.boat_no}号艇
                </div>
              </div>
              {race.confidence === 'S' && (
                <Star size={20} color="#ffd700" fill="#ffd700" style={{ marginLeft: 'auto' }} />
              )}
            </div>
          </div>
        ))}
      </div>

      {races.length === 0 && !loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem', 
          color: '#888' 
        }}>
          現在、条件に合うレースがありません。閾値を下げてみてください。
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default HighValueRaces;
