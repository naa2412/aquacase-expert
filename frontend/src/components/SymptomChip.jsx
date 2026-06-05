import { Check } from 'lucide-react';

export default function SymptomChip({ kode, nama, selected, cf, onToggle, onCfChange }) {
  return (
    <div style={{
      borderRadius: 'var(--radius-md)',
      border: selected ? '1.5px solid var(--color-primary)' : '1.5px solid #cbd5e1',
      background: selected ? 'linear-gradient(135deg, #e0f2fe, #f0f9ff)' : 'white',
      padding: '10px 14px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
    }}>
      <button
        type="button"
        onClick={() => onToggle(kode)}
        title={`${kode}: ${nama}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          width: '100%',
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div style={{
          width: '20px',
          height: '20px',
          borderRadius: '4px',
          border: selected ? 'none' : '1.5px solid #94a3b8',
          background: selected ? 'var(--color-primary)' : 'transparent',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transition: 'all 0.2s ease',
        }}>
          {selected && <Check size={13} color="white" strokeWidth={3} />}
        </div>
        <span style={{
          fontSize: '0.85rem',
          fontWeight: selected ? 600 : 400,
          color: selected ? 'var(--color-primary-dark)' : 'var(--text-secondary)',
          flex: 1,
          lineHeight: 1.4,
        }}>
          {nama}
        </span>
        <span className="font-mono" style={{
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
          flexShrink: 0,
        }}>
          {kode}
        </span>
      </button>

      {/* Slider keyakinan — muncul saat dipilih */}
      <div style={{
        overflow: 'hidden',
        maxHeight: selected ? '48px' : '0',
        opacity: selected ? 1 : 0,
        transition: 'max-height 0.3s ease, opacity 0.3s ease, margin 0.3s ease',
        marginTop: selected ? '10px' : '0',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          paddingTop: '8px',
          borderTop: '1px solid rgba(0,0,0,0.06)',
        }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            Keyakinan:
          </span>
          <input
            type="range"
            min="0.1"
            max="1.0"
            step="0.1"
            value={cf}
            onChange={(e) => onCfChange(kode, parseFloat(e.target.value))}
            onClick={(e) => e.stopPropagation()}
            style={{ flex: 1 }}
          />
          <span className="font-mono" style={{
            fontSize: '0.82rem',
            fontWeight: 600,
            color: 'var(--color-primary)',
            minWidth: '32px',
            textAlign: 'right',
          }}>
            {cf.toFixed(1)}
          </span>
        </div>
      </div>
    </div>
  );
}
