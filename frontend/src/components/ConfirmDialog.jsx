import { AlertTriangle, X } from 'lucide-react';

export default function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '20px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: 'var(--color-danger-bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
            <AlertTriangle size={20} style={{ color: 'var(--color-danger)' }} />
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ marginBottom: '6px' }}>{title}</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
              {message}
            </p>
          </div>
          <button className="btn-ghost" onClick={onCancel} style={{ padding: '4px' }}>
            <X size={20} />
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={onCancel} style={{ fontSize: '0.85rem' }}>
            Batal
          </button>
          <button className="btn btn-danger" onClick={onConfirm} style={{ fontSize: '0.85rem' }}>
            Hapus
          </button>
        </div>
      </div>
    </div>
  );
}
