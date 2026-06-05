import { useState, useEffect } from 'react';
import { Search, Database, Eye, X, Fish, ChevronDown, ChevronUp } from 'lucide-react';
import { getKasus } from '../api/client';
import { SkeletonTable } from '../components/Skeleton';

export default function BasisKasus() {
  const [kasus, setKasus] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const res = await getKasus();
        setKasus(res.data);
      } catch (err) {
        setError(err.userMessage || 'Gagal menghubungi server. Pastikan backend berjalan di port 8000.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = kasus.filter((k) => {
    const q = search.toLowerCase();
    return (
      k.kode_kasus?.toLowerCase().includes(q) ||
      k.nama_penyakit?.toLowerCase().includes(q) ||
      k.jenis_ikan?.toLowerCase().includes(q) ||
      k.kode_penyakit?.toLowerCase().includes(q)
    );
  });

  if (loading) {
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Basis Kasus (CBR)</h1>
        <SkeletonTable rows={8} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Basis Kasus (CBR)</h1>
        <div className="glass-card-static" style={{ padding: '32px', textAlign: 'center' }}>
          <p style={{ color: 'var(--color-danger)' }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '24px',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div>
          <h1 style={{ marginBottom: '4px' }}>Basis Kasus (CBR)</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {kasus.length} kasus tersimpan dalam case base
          </p>
        </div>
        <div className="search-input-wrapper">
          <Search className="search-icon" />
          <input
            type="text"
            className="search-input"
            placeholder="Cari kasus, penyakit, atau ikan..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="glass-card-static" style={{ overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Kode</th>
                <th>Ikan</th>
                <th>Penyakit</th>
                <th>CF Pakar</th>
                <th>Gejala</th>
                <th style={{ width: '40px' }}></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((k) => {
                const isExpanded = expandedId === k.kode_kasus;
                return (
                  <>
                    <tr key={k.kode_kasus} style={{ cursor: 'pointer' }}
                        onClick={() => setExpandedId(isExpanded ? null : k.kode_kasus)}>
                      <td className="font-mono" style={{ fontWeight: 600, fontSize: '0.82rem' }}>
                        {k.kode_kasus}
                      </td>
                      <td>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <Fish size={14} style={{ color: 'var(--color-accent)' }} />
                          {k.jenis_ikan}
                        </span>
                      </td>
                      <td style={{ maxWidth: '220px' }}>
                        <div style={{ fontWeight: 500, fontSize: '0.82rem' }}>
                          {k.nama_penyakit}
                        </div>
                        <div className="font-mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                          {k.kode_penyakit}
                        </div>
                      </td>
                      <td className="font-mono" style={{ fontWeight: 600 }}>
                        {k.cf_pakar?.toFixed(2)}
                      </td>
                      <td>{k.gejala?.length || 0}</td>
                      <td>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr key={`${k.kode_kasus}-detail`}>
                        <td colSpan={6} style={{
                          padding: '12px 20px 16px',
                          background: 'rgba(14, 165, 233, 0.03)',
                        }}>
                          <p style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '8px' }}>
                            Detail Gejala:
                          </p>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {k.gejala?.map((g, i) => (
                              <span key={i} className="badge badge-info" style={{
                                fontSize: '0.72rem',
                                padding: '4px 10px',
                              }}>
                                {g.nama_gejala || g.kode_gejala}
                                <span className="font-mono" style={{ marginLeft: '4px', opacity: 0.7 }}>
                                  ({g.bobot?.toFixed(1)})
                                </span>
                              </span>
                            ))}
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
              Tidak ditemukan kasus yang cocok dengan pencarian.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
