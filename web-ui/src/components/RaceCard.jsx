/**
 * Race Card Component
 */
import React from 'react';
import { Clock, CheckCircle2, Trophy } from 'lucide-react';

const BOAT_COLORS = {
  1: '#FFFFFF',
  2: '#000000',
  3: '#FF0000',
  4: '#0000FF',
  5: '#FFFF00',
  6: '#00FF00',
};

export default function RaceCard({ race, onClick, selected }) {
  const statusIcon = {
    finished: <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />,
    awaiting_result: <Clock size={16} style={{ color: 'var(--warning)' }} />,
    no_data: <Clock size={16} style={{ color: 'var(--text-muted)' }} />,
  };

  return (
    <div
      className={`card race-card ${selected ? 'selected' : ''}`}
      onClick={() => onClick?.(race)}
      style={{
        cursor: 'pointer',
        padding: '1rem',
        transition: 'all 0.2s ease',
        border: selected ? '2px solid var(--primary)' : '1px solid var(--glass-border)',
        background: selected ? 'rgba(var(--primary-rgb), 0.1)' : 'var(--glass-bg)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontWeight: '900', fontSize: '1.2rem' }}>
            {race.jyo_name} {race.race_no}R
          </span>
          {statusIcon[race.status]}
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {race.start_time}
        </span>
      </div>

      {race.race_name && (
        <div style={{ fontSize: '0.85rem', color: 'var(--secondary)', marginBottom: '0.5rem' }}>
          {race.race_name}
        </div>
      )}

      {race.racers && race.racers.length > 0 && (
        <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {race.racers.slice(0, 6).map((racer, idx) => (
            <span
              key={idx}
              style={{
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                background: BOAT_COLORS[idx + 1],
                color: idx === 0 || idx === 4 ? '#000' : '#fff',
                border: idx === 0 ? '1px solid #ccc' : 'none',
              }}
            >
              {racer}
            </span>
          ))}
        </div>
      )}

      {race.has_prediction && (
        <div style={{ marginTop: '0.5rem' }}>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '0.75rem',
              background: 'var(--primary)',
              color: '#fff',
            }}
          >
            AI予測可能
          </span>
        </div>
      )}
    </div>
  );
}
