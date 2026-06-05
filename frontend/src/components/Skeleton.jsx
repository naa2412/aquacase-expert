export default function Skeleton({ width, height, style, className = '' }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width: width || '100%',
        height: height || '16px',
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="glass-card-static" style={{ padding: '24px' }}>
      <Skeleton height="20px" width="50%" style={{ marginBottom: '16px' }} />
      <Skeleton height="14px" width="80%" style={{ marginBottom: '8px' }} />
      <Skeleton height="14px" width="65%" style={{ marginBottom: '8px' }} />
      <Skeleton height="14px" width="90%" />
    </div>
  );
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="glass-card-static" style={{ padding: '20px', overflow: 'hidden' }}>
      <Skeleton height="40px" style={{ marginBottom: '12px' }} />
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} height="48px" style={{ marginBottom: '6px' }} />
      ))}
    </div>
  );
}
