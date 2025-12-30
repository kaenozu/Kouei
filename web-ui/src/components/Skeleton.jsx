/**
 * Skeleton Loading Components
 */
import React from 'react';

const baseStyle = {
  background: 'linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%)',
  backgroundSize: '200% 100%',
  animation: 'shimmer 1.5s infinite',
  borderRadius: '8px',
};

export function SkeletonBox({ width = '100%', height = '20px', style = {} }) {
  return (
    <div
      style={{
        ...baseStyle,
        width,
        height,
        ...style,
      }}
    />
  );
}

export function SkeletonCard({ lines = 3 }) {
  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      <SkeletonBox width="60%" height="24px" style={{ marginBottom: '1rem' }} />
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonBox
          key={i}
          width={`${80 - i * 10}%`}
          height="16px"
          style={{ marginBottom: '0.5rem' }}
        />
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }) {
  return (
    <div className="card" style={{ padding: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: '1rem', marginBottom: '1rem' }}>
        {Array.from({ length: cols }).map((_, i) => (
          <SkeletonBox key={i} height="20px" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIdx) => (
        <div
          key={rowIdx}
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
            gap: '1rem',
            padding: '0.75rem 0',
            borderBottom: '1px solid var(--glass-border)',
          }}
        >
          {Array.from({ length: cols }).map((_, colIdx) => (
            <SkeletonBox key={colIdx} height="16px" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonPrediction() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <SkeletonCard lines={2} />
      <SkeletonTable rows={6} cols={5} />
      <SkeletonCard lines={4} />
    </div>
  );
}

export default {
  SkeletonBox,
  SkeletonCard,
  SkeletonTable,
  SkeletonPrediction,
};
