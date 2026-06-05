export default function ScoreBar({ value, label, showPercent = true }) {
  // value: 0.0 - 1.0
  const percent = Math.round(value * 100);
  const level = value >= 0.75 ? 'high' : value >= 0.50 ? 'medium' : 'low';

  return (
    <div style={{ width: '100%' }}>
      {label && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '6px',
        }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {label}
          </span>
          {showPercent && (
            <span className="font-mono" style={{
              fontSize: '0.82rem',
              fontWeight: 600,
              color: level === 'high' ? 'var(--score-high)' :
                     level === 'medium' ? 'var(--score-medium)' : 'var(--score-low)',
            }}>
              {percent}%
            </span>
          )}
        </div>
      )}
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${level}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
