/**
 * Stats Card Component
 * 統計カードコンポーネント
 */
import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function StatsCard({ title, value, unit = '', change = null, icon, color = 'var(--primary)' }) {
  const isPositive = change !== null && change >= 0;

  return (
    <div
      className="card"
      style={{
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>
          {title}
        </span>
        {icon && <span style={{ color }}>{icon}</span>}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
        <span style={{ fontSize: '2.5rem', fontWeight: '900', color }}>
          {typeof value === 'number' ? value.toLocaleString() : value}
        </span>
        {unit && <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>{unit}</span>}
      </div>

      {change !== null && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.25rem',
            fontSize: '0.85rem',
            color: isPositive ? 'var(--success)' : 'var(--error)',
          }}
        >
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{isPositive ? '+' : ''}{change}%</span>
          <span style={{ color: 'var(--text-muted)' }}>前日比</span>
        </div>
      )}
    </div>
  );
}
