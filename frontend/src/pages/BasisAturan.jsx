import { useState, useEffect, useMemo } from 'react';
import { Search, BookOpen, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { getAturan, getPenyakit } from '../api/client';
import { SkeletonTable } from '../components/Skeleton';

export default function BasisAturan() {
  const [aturan, setAturan] = useState([]);
  const [penyakitList, setPenyakitList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterPenyakit, setFilterPenyakit] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [aturanRes, penyakitRes] = await Promise.all([getAturan(), getPenyakit()]);
        setAturan(aturanRes.data);
        setPenyakitList(penyakitRes.data);
      } catch (err) {
        setError(err.userMessage || 'Gagal menghubungi server. Pastikan backend berjalan di port 8000.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = useMemo(() => {
    return aturan.filter((r) => {
      const q = search.toLowerCase();
      const matchSearch =
        r.kode_rule?.toLowerCase().includes(q) ||
        r.nama_penyakit_rule?.toLowerCase().includes(q) ||
        r.rule_text?.toLowerCase().includes(q) ||
        r.gejala_detail?.some(g => g.nama_gejala?.toLowerCase().includes(q));
      const matchPenyakit = filterPenyakit
        ? r.kode_penyakit === filterPenyakit
        : true;
      return matchSearch && matchPenyakit;
    });
  }, [aturan, search, filterPenyakit]);

  if (loading) {
    return (
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Basis Aturan (RBR)</h1>
        <SkeletonTable rows={10} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: '960px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Basis Aturan (RBR)</h1>
        <div className="glass-card-static" style={{ padding: '32px', textAlign: 'center' }}>
          <p style={{ color: 'var(--color-danger)' }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ marginBottom: '4px' }}>Basis Aturan (RBR)</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          {aturan.length} aturan dalam knowledge base
        </p>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex',
        gap: '12px',
        marginBottom: '20px',
        flexWrap: 'wrap',
      }}>
        <div className="search-input-wrapper" style={{ flex: '1', minWidth: '200px' }}>
          <Search className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Cari aturan, penyakit, atau gejala..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div style={{ position: 'relative', minWidth: '200px' }}>
          <select
            value={filterPenyakit}
            onChange={(e) => setFilterPenyakit(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 16px',
              border: '1.5px solid #cbd5e1',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.875rem',
              fontFamily: 'var(--font-body)',
              color: filterPenyakit ? 'var(--text-main)' : 'var(--text-muted)',
              background: 'white',
              cursor: 'pointer',
              outline: 'none',
              appearance: 'none',
              paddingRight: '36px',
            }}
          >
            <option value="">Semua Penyakit</option>
            {penyakitList.map((p) => (
              <option key={p.kode_penyakit} value={p.kode_penyakit}>
                {p.kode_penyakit} - {p.nama_penyakit}
              </option>
            ))}
          </select>
          <Filter size={16} style={{
            position: 'absolute',
            right: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
            pointerEvents: 'none',
          }} />
        </div>
      </div>

      {/* Count */}
      <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
        Menampilkan {filtered.length} dari {aturan.length} aturan
      </p>

      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '80px' }}>Kode</th>
                <th>Aturan (IF - THEN)</th>
                <th style={{ width: '80px' }}>CF</th>
                <th style={{ width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 100).map((r) => {
                const isExpanded = expandedId === r.kode_rule;
                return (
                  <>
                    <tr key={r.kode_rule} style={{ cursor: 'pointer' }}
                        onClick={() => setExpandedId(isExpanded ? null : r.kode_rule)}>
                      <td className="font-mono" style={{ fontWeight: 600, fontSize: '0.8rem' }}>
                        {r.kode_rule}
                      </td>
                      <td>
                        <span style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.8rem',
                          color: 'var(--text-secondary)',
                        }}>
                          {r.rule_text}
                        </span>
                      </td>
                      <td className="font-mono" style={{ fontWeight: 600 }}>
                        {r.cf_pakar?.toFixed(2)}
                      </td>
                      <td>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${r.kode_rule}-detail`}>
                        <td colSpan={4} style={{
                          padding: '12px 20px 16px',
                          background: 'rgba(14, 165, 233, 0.03)',
                        }}>
                          <div style={{ marginBottom: '10px' }}>
                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                              Penyakit:
                            </span>
                            <span style={{ marginLeft: '8px', fontSize: '0.85rem' }}>
                              {r.nama_penyakit_rule} ({r.kode_penyakit})
                            </span>
                          </div>
                          <div>
                            <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                              Premis:
                            </span>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '6px' }}>
                              {r.gejala_detail?.map((g, i) => (
                                <span key={i} className="badge badge-info" style={{ fontSize: '0.72rem' }}>
                                  {g.kode_gejala}: {g.nama_gejala}
                                </span>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                );
              })}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="empty-state" style={{ padding: '32px' }}>
            <Search style={{ width: '40px', height: '40px', color: 'var(--text-muted)', opacity: 0.3, marginBottom: '8px' }} />
            <p className="empty-state-text" style={{ fontSize: '0.85rem' }}>
              Tidak ditemukan aturan yang cocok dengan pencarian.
            </p>
          </div>
        )}

        {filtered.length > 100 && (
          <div style={{
            padding: '12px',
            textAlign: 'center',
            color: 'var(--text-muted)',
            fontSize: '0.82rem',
            borderTop: '1px solid rgba(0,0,0,0.06)',
          }}>
            Menampilkan 100 dari {filtered.length} aturan. Gunakan filter untuk mempersempit pencarian.
          </div>
        )}
      </div>
    </div>
  );
}
