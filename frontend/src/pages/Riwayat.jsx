import { useState } from 'react';
import {
  Clock, Trash2, Eye, X, Fish, Calendar, ChevronDown, ChevronUp,
  Inbox, Stethoscope, Trash,
} from 'lucide-react';
import { useHistory } from '../context/HistoryContext';
import ConfirmDialog from '../components/ConfirmDialog';
import ScoreBar from '../components/ScoreBar';

function toTitleCase(str) {
  if (!str) return '';
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Riwayat() {
  const { riwayat, hapusRiwayat, hapusSemua } = useHistory();
  const [expandedId, setExpandedId] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [showDeleteAll, setShowDeleteAll] = useState(false);

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (riwayat.length === 0) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Riwayat Diagnosis</h1>
        <div className="glass-card-static empty-state">
          <Inbox className="empty-state-icon" />
          <p className="empty-state-text">
            Belum ada riwayat diagnosis. Mulai diagnosis pertama Anda.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
      }}>
        <div>
          <h1 style={{ marginBottom: '4px' }}>Riwayat Diagnosis</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {riwayat.length} diagnosis tersimpan
          </p>
        </div>
        <button
          className="btn btn-ghost"
          onClick={() => setShowDeleteAll(true)}
          style={{ color: 'var(--color-danger)', fontSize: '0.82rem' }}
        >
          <Trash size={16} />
          Hapus Semua
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {riwayat.map((r) => {
          const isExpanded = expandedId === r.id;
          const res = r.result;
          const isConflict = res?.is_conflict;
          const diagName = isConflict
            ? 'Konflik Terdeteksi'
            : toTitleCase(res?.diagnosis_akhir?.nama_penyakit) || 'Tidak ada diagnosis';
          const score = res?.diagnosis_akhir?.final_score || 0;
          const threshold = res?.explanation?.summary?.status_threshold;

          return (
            <div key={r.id} className="glass-card-static" style={{ overflow: 'hidden' }}>
              {/* Header */}
              <div
                style={{
                  padding: '16px 20px',
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
                onClick={() => setExpandedId(isExpanded ? null : r.id)}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                    <h4 style={{
                      fontSize: '0.95rem',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}>
                      {diagName}
                    </h4>
                    {!isConflict && threshold && (
                      <span className={`badge ${
                        threshold === 'Kuat' ? 'badge-success' :
                        threshold === 'Sedang' ? 'badge-info' : 'badge-warning'
                      }`} style={{ fontSize: '0.7rem' }}>
                        {threshold}
                      </span>
                    )}
                    {isConflict && (
                      <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
                        Konflik
                      </span>
                    )}
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)',
                  }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Fish size={13} />
                      {r.jenis_ikan}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Stethoscope size={13} />
                      {r.gejala_names?.length || 0} gejala
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Calendar size={13} />
                      {formatDate(r.tanggal)}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  {!isConflict && (
                    <span className="font-mono" style={{
                      fontSize: '1rem',
                      fontWeight: 700,
                      color: score >= 0.75 ? 'var(--score-high)' :
                             score >= 0.50 ? 'var(--score-medium)' : 'var(--score-low)',
                    }}>
                      {(score * 100).toFixed(0)}%
                    </span>
                  )}
                  {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </div>
              </div>

              {/* Expanded Detail */}
              {isExpanded && (
                <div style={{
                  padding: '0 20px 16px',
                  borderTop: '1px solid rgba(0,0,0,0.05)',
                }}>
                  <div style={{ paddingTop: '14px' }}>
                    {!isConflict && (
                      <div style={{ marginBottom: '12px' }}>
                        <ScoreBar value={score} label="Skor Fusion" />
                      </div>
                    )}

                    <p style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '6px' }}>
                      Gejala yang dipilih:
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '14px' }}>
                      {r.gejala_names?.map((name, i) => (
                        <span key={i} className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                          {name}
                        </span>
                      ))}
                    </div>

                    {res?.explanation?.rekomendasi && (
                      <div style={{
                        padding: '12px 14px',
                        background: 'var(--color-success-bg)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.82rem',
                        color: 'var(--text-secondary)',
                        lineHeight: 1.6,
                        marginBottom: '12px',
                      }}>
                        <strong style={{ color: 'var(--color-success)' }}>Rekomendasi:</strong>{' '}
                        {res.explanation.rekomendasi.slice(0, 300)}
                        {res.explanation.rekomendasi.length > 300 ? '...' : ''}
                      </div>
                    )}

                    <button
                      className="btn btn-ghost"
                      onClick={(e) => { e.stopPropagation(); setDeleteId(r.id); }}
                      style={{ color: 'var(--color-danger)', fontSize: '0.8rem' }}
                    >
                      <Trash2 size={14} />
                      Hapus riwayat ini
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Delete single confirmation */}
      <ConfirmDialog
        isOpen={deleteId !== null}
        title="Hapus Riwayat"
        message="Apakah Anda yakin ingin menghapus riwayat ini? Tindakan ini tidak dapat dibatalkan."
        onConfirm={() => { hapusRiwayat(deleteId); setDeleteId(null); }}
        onCancel={() => setDeleteId(null)}
      />

      {/* Delete all confirmation */}
      <ConfirmDialog
        isOpen={showDeleteAll}
        title="Hapus Semua Riwayat"
        message="Apakah Anda yakin ingin menghapus semua riwayat diagnosis? Tindakan ini tidak dapat dibatalkan."
        onConfirm={() => { hapusSemua(); setShowDeleteAll(false); }}
        onCancel={() => setShowDeleteAll(false)}
      />
    </div>
  );
}
