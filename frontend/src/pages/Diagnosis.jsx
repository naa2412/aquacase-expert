import { useState, useEffect } from 'react';
import {
  Fish, ChevronRight, ChevronLeft, Stethoscope, AlertTriangle,
  CheckCircle2, Info, BarChart3, BookOpen, Database, ArrowRight,
  RefreshCcw, XCircle,
} from 'lucide-react';
import { getIkan, getGejala, postDiagnose } from '../api/client';
import { useHistory } from '../context/HistoryContext';
import SymptomChip from '../components/SymptomChip';
import ScoreBar from '../components/ScoreBar';
import { SkeletonCard } from '../components/Skeleton';

// Helper: Kapitalisasi huruf depan setiap kata
function toTitleCase(str) {
  if (!str) return '';
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Diagnosis() {
  // Step state
  const [step, setStep] = useState(1);

  // Data dari API
  const [ikanList, setIkanList] = useState([]);
  const [gejalaList, setGejalaList] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [loadError, setLoadError] = useState('');

  // User input
  const [selectedIkan, setSelectedIkan] = useState(null);
  const [selectedGejala, setSelectedGejala] = useState({}); // {kode: cf}

  // Result
  const [result, setResult] = useState(null);
  const [diagnosing, setDiagnosing] = useState(false);
  const [diagnoseError, setDiagnoseError] = useState('');

  const { tambahRiwayat } = useHistory();

  // Load data
  useEffect(() => {
    async function load() {
      try {
        setLoadingData(true);
        setLoadError('');
        const [ikanRes, gejalaRes] = await Promise.all([getIkan(), getGejala()]);
        setIkanList(Array.isArray(ikanRes.data) ? ikanRes.data : []);
        setGejalaList(Array.isArray(gejalaRes.data) ? gejalaRes.data : []);
      } catch (err) {
        setLoadError(err.userMessage || 'Gagal menghubungi server. Pastikan backend berjalan di port 8000.');
      } finally {
        setLoadingData(false);
      }
    }
    load();
  }, []);

  // Toggle gejala
  const toggleGejala = (kode) => {
    setSelectedGejala((prev) => {
      const next = { ...prev };
      if (next[kode] !== undefined) {
        delete next[kode];
      } else {
        next[kode] = 0.8; // default CF
      }
      return next;
    });
  };

  // Update CF
  const updateCf = (kode, value) => {
    setSelectedGejala((prev) => ({ ...prev, [kode]: value }));
  };

  // Submit diagnosis
  const handleDiagnose = async () => {
    if (Object.keys(selectedGejala).length === 0) {
      setDiagnoseError('Pilih minimal satu gejala untuk memulai diagnosis');
      return;
    }

    try {
      setDiagnosing(true);
      setDiagnoseError('');
      const res = await postDiagnose({
        kode_ikan: selectedIkan.kode_ikan,
        gejala_input: selectedGejala,
      });
      setResult(res.data);
      setStep(3);

      // Simpan ke riwayat
      tambahRiwayat({
        kode_ikan: selectedIkan.kode_ikan,
        jenis_ikan: selectedIkan.jenis_ikan,
        gejala_input: selectedGejala,
        gejala_names: Object.keys(selectedGejala).map(k => {
          const g = gejalaList.find(g => g.kode_gejala === k);
          return g ? g.nama_gejala : k;
        }),
        result: res.data,
      });
    } catch (err) {
      setDiagnoseError(err.userMessage || 'Terjadi kesalahan saat memproses diagnosis.');
    } finally {
      setDiagnosing(false);
    }
  };

  // Reset
  const handleReset = () => {
    setStep(1);
    setSelectedIkan(null);
    setSelectedGejala({});
    setResult(null);
    setDiagnoseError('');
  };

  // Step indicator
  const renderSteps = () => (
    <div className="steps">
      <div className={`step ${step === 1 ? 'active' : step > 1 ? 'completed' : ''}`}>
        <span className="step-number">{step > 1 ? <CheckCircle2 size={16} /> : '1'}</span>
        <span>Pilih Ikan</span>
      </div>
      <div className={`step-divider ${step > 1 ? 'completed' : ''}`} />
      <div className={`step ${step === 2 ? 'active' : step > 2 ? 'completed' : ''}`}>
        <span className="step-number">{step > 2 ? <CheckCircle2 size={16} /> : '2'}</span>
        <span>Pilih Gejala</span>
      </div>
      <div className={`step-divider ${step > 2 ? 'completed' : ''}`} />
      <div className={`step ${step === 3 ? 'active' : ''}`}>
        <span className="step-number">3</span>
        <span>Hasil</span>
      </div>
    </div>
  );

  // Loading state
  if (loadingData) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Diagnosis Penyakit</h1>
        <SkeletonCard />
        <div style={{ marginTop: '16px' }}><SkeletonCard /></div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ marginBottom: '24px' }}>Diagnosis Penyakit</h1>
        <div className="glass-card-static" style={{ padding: '40px', textAlign: 'center' }}>
          <XCircle size={40} style={{ color: 'var(--color-danger)', marginBottom: '12px' }} />
          <p style={{ color: 'var(--color-danger)', fontWeight: 500, marginBottom: '16px' }}>
            {loadError}
          </p>
          <button className="btn btn-primary" onClick={() => window.location.reload()}>
            <RefreshCcw size={16} />
            Coba Lagi
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '8px' }}>Diagnosis Penyakit</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '28px' }}>
        Pilih jenis ikan dan gejala yang diamati untuk mendapatkan diagnosis.
      </p>

      {renderSteps()}

      {/* ============ STEP 1: Pilih Ikan ============ */}
      {step === 1 && (
        <div className="glass-card-static" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Fish size={22} style={{ color: 'var(--color-primary)' }} />
            Pilih Jenis Ikan
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
            Pilih jenis ikan yang ingin didiagnosis.
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
            gap: '12px',
            marginBottom: '24px',
          }}>
            {ikanList.map((ikan) => (
              <button
                key={ikan.kode_ikan}
                onClick={() => setSelectedIkan(ikan)}
                style={{
                  padding: '16px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: selectedIkan?.kode_ikan === ikan.kode_ikan
                    ? '2px solid var(--color-primary)'
                    : '1.5px solid #cbd5e1',
                  background: selectedIkan?.kode_ikan === ikan.kode_ikan
                    ? 'linear-gradient(135deg, #e0f2fe, #bae6fd)'
                    : 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  textAlign: 'center',
                }}
              >
                <Fish size={24} style={{
                  color: selectedIkan?.kode_ikan === ikan.kode_ikan
                    ? 'var(--color-primary)' : 'var(--text-muted)',
                  marginBottom: '6px',
                }} />
                <div style={{
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  color: selectedIkan?.kode_ikan === ikan.kode_ikan
                    ? 'var(--color-primary-dark)' : 'var(--text-secondary)',
                }}>
                  {ikan.jenis_ikan}
                </div>
                <div className="font-mono" style={{
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  marginTop: '2px',
                }}>
                  {ikan.kode_ikan}
                </div>
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              className="btn btn-primary"
              disabled={!selectedIkan}
              onClick={() => setStep(2)}
            >
              Lanjutkan
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* ============ STEP 2: Pilih Gejala ============ */}
      {step === 2 && (
        <div className="glass-card-static" style={{ padding: '28px' }}>
          <h2 style={{ marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Stethoscope size={22} style={{ color: 'var(--color-primary)' }} />
            Pilih Gejala yang Diamati
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '20px' }}>
            Pilih gejala dan atur tingkat keyakinan (0.1 - 1.0) untuk setiap gejala.
            Ikan yang dipilih: <strong>{selectedIkan?.jenis_ikan}</strong>
          </p>

          {diagnoseError && (
            <div style={{
              padding: '12px 16px',
              background: 'var(--color-danger-bg)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-danger)',
              fontSize: '0.875rem',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <AlertTriangle size={16} />
              {diagnoseError}
            </div>
          )}

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '10px',
            marginBottom: '24px',
            maxHeight: '480px',
            overflowY: 'auto',
            padding: '6px 4px',
          }}>
            {gejalaList.map((g) => (
              <SymptomChip
                key={g.kode_gejala}
                kode={g.kode_gejala}
                nama={g.nama_gejala}
                selected={selectedGejala[g.kode_gejala] !== undefined}
                cf={selectedGejala[g.kode_gejala] || 0.8}
                onToggle={toggleGejala}
                onCfChange={updateCf}
              />
            ))}
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTop: '1px solid rgba(0,0,0,0.06)',
            paddingTop: '16px',
          }}>
            <button className="btn btn-secondary" onClick={() => setStep(1)}>
              <ChevronLeft size={18} />
              Kembali
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                {Object.keys(selectedGejala).length} gejala dipilih
              </span>
              <button
                className="btn btn-primary"
                disabled={diagnosing || Object.keys(selectedGejala).length === 0}
                onClick={handleDiagnose}
              >
                {diagnosing ? 'Memproses...' : 'Diagnosa'}
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ============ STEP 3: Hasil ============ */}
      {step === 3 && result && (
        <div>
          {/* Diagnosis Result Card */}
          <div className="glass-card" style={{ padding: '28px', marginBottom: '20px' }}>
            {result.is_conflict ? (
              /* CONFLICT */
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                  <AlertTriangle size={24} style={{ color: 'var(--color-warning)' }} />
                  <h2 style={{ color: 'var(--color-warning)' }}>Konflik Terdeteksi</h2>
                </div>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: 1.65 }}>
                  {result.explanation?.summary?.pesan_utama}
                </p>

                {result.kandidat_konflik?.map((k, i) => (
                  <div key={i} className="glass-card-static" style={{
                    padding: '16px 20px',
                    marginBottom: '10px',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span className="badge badge-warning" style={{ marginBottom: '6px', display: 'inline-block' }}>
                          Kandidat {i + 1} - Dominasi {k.dominasi}
                        </span>
                        <h4>{toTitleCase(k.nama_penyakit)}</h4>
                      </div>
                      <span className="font-mono" style={{
                        fontSize: '1.25rem',
                        fontWeight: 700,
                        color: 'var(--color-warning)',
                      }}>
                        {(k.final_score * 100).toFixed(2)}%
                      </span>
                    </div>
                    <ScoreBar value={k.final_score} />
                  </div>
                ))}
              </>
            ) : (
              /* NORMAL DIAGNOSIS */
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
                  <CheckCircle2 size={24} style={{ color: 'var(--color-success)' }} />
                  <h2>Hasil Diagnosis</h2>
                  <span className={`badge ${
                    result.explanation?.summary?.status_threshold === 'Kuat' ? 'badge-success' :
                    result.explanation?.summary?.status_threshold === 'Sedang' ? 'badge-info' :
                    'badge-warning'
                  }`}>
                    {result.explanation?.summary?.status_threshold}
                  </span>
                </div>

                <h3 style={{
                  fontSize: '1.3rem',
                  color: 'var(--color-primary-dark)',
                  marginBottom: '8px',
                }}>
                  {toTitleCase(result.diagnosis_akhir?.nama_penyakit)}
                </h3>

                <p style={{
                  color: 'var(--text-muted)',
                  fontSize: '0.875rem',
                  lineHeight: 1.65,
                  marginBottom: '16px',
                }}>
                  {result.explanation?.summary?.pesan_utama}
                </p>

                <ScoreBar
                  value={result.diagnosis_akhir?.final_score || 0}
                  label="Skor Akhir Fusion"
                />
              </>
            )}
          </div>

          {/* Explanation Sections (only for normal diagnosis) */}
          {!result.is_conflict && result.explanation && (
            <>
              {/* Fusion Breakdown */}
              {result.explanation.fusion_breakdown && (
                <div className="glass-card" style={{ padding: '24px', marginBottom: '16px' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                    <BarChart3 size={20} style={{ color: 'var(--color-primary)' }} />
                    Breakdown Fusion
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px', fontFamily: 'var(--font-mono)' }}>
                    {result.explanation.fusion_breakdown.rumus}
                  </p>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    <ScoreBar
                      value={result.explanation.fusion_breakdown.komponen?.skor_cf_rbr || 0}
                      label={`RBR (CF) - Bobot: ${result.explanation.fusion_breakdown.komponen?.bobot_rbr}`}
                    />
                    <ScoreBar
                      value={result.explanation.fusion_breakdown.komponen?.skor_sim_cbr || 0}
                      label={`CBR (Similarity) - Bobot: ${result.explanation.fusion_breakdown.komponen?.bobot_cbr}`}
                    />
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 0',
                      borderTop: '1px solid rgba(0,0,0,0.06)',
                    }}>
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        Agreement Score (Bobot: {result.explanation.fusion_breakdown.komponen?.bobot_agreement})
                      </span>
                      <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                        {result.explanation.fusion_breakdown.komponen?.skor_agreement?.toFixed(1)}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* RBR Analysis */}
              {result.explanation.rbr_analysis && (
                <div className="glass-card" style={{ padding: '24px', marginBottom: '16px' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <BookOpen size={20} style={{ color: 'var(--color-primary)' }} />
                    Analisis RBR
                  </h3>
                  <div style={{ marginBottom: '12px' }}>
                    <ScoreBar
                      value={result.explanation.rbr_analysis.cf_score || 0}
                      label="Certainty Factor (CF)"
                    />
                  </div>
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
                    {result.explanation.rbr_analysis.jumlah_rule_aktif || 0} aturan aktif terpicu
                  </p>

                  {result.explanation.rbr_analysis.aturan_aktif?.slice(0, 5).map((rule, i) => (
                    <div key={i} style={{
                      padding: '10px 14px',
                      background: 'rgba(3, 105, 161, 0.04)',
                      borderRadius: 'var(--radius-md)',
                      marginBottom: '6px',
                      fontSize: '0.8rem',
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.6,
                      overflowWrap: 'break-word',
                    }}>
                      <strong style={{ color: 'var(--color-primary)' }}>{rule.id_rule}:</strong>{' '}
                      {rule.rule_text}
                    </div>
                  ))}
                </div>
              )}

              {/* CBR Analysis */}
              {result.explanation.cbr_analysis && (
                <div className="glass-card" style={{ padding: '24px', marginBottom: '16px' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <Database size={20} style={{ color: 'var(--color-primary)' }} />
                    Analisis CBR
                  </h3>
                  <div style={{ marginBottom: '12px' }}>
                    <ScoreBar
                      value={result.explanation.cbr_analysis.similarity_score || 0}
                      label="Similarity Kasus Terdekat"
                    />
                  </div>

                  {result.explanation.cbr_analysis.top_similar_cases?.length > 0 && (
                    <>
                      <p style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '8px' }}>
                        Kasus Serupa:
                      </p>
                      {result.explanation.cbr_analysis.top_similar_cases.map((c, i) => (
                        <div key={i} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '8px 12px',
                          background: 'rgba(0,0,0,0.02)',
                          borderRadius: 'var(--radius-sm)',
                          marginBottom: '4px',
                          fontSize: '0.82rem',
                        }}>
                          <div>
                            <span style={{ fontWeight: 600 }}>{c.kode_kasus}</span>
                            <span style={{ color: 'var(--text-muted)', margin: '0 6px' }}>-</span>
                            <span style={{ color: 'var(--text-secondary)' }}>{toTitleCase(c.nama_penyakit)}</span>
                            {c.coverage && (
                              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginLeft: '8px' }}>
                                ({c.coverage})
                              </span>
                            )}
                          </div>
                          <span className="font-mono" style={{ fontWeight: 600, color: 'var(--color-primary)' }}>
                            {c.similarity_persen}%
                          </span>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}

              {/* Rekomendasi */}
              {result.explanation.rekomendasi && (
                <div className="glass-card" style={{ padding: '24px', marginBottom: '16px' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <Info size={20} style={{ color: 'var(--color-success)' }} />
                    Rekomendasi Penanganan
                  </h3>
                  <p style={{
                    fontSize: '0.875rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.7,
                    whiteSpace: 'pre-wrap',
                    textAlign: 'justify',
                  }}>
                    {result.explanation.rekomendasi.split(/(pengobatan|pengendalian)/gi).map((part, i) =>
                      /^(pengobatan|pengendalian)$/i.test(part)
                        ? <strong key={i}>{part}</strong>
                        : part
                    )}
                  </p>
                </div>
              )}

              {/* All Candidates Table */}
              {result.semua_kandidat?.length > 1 && (
                <div className="glass-card" style={{ padding: '24px', marginBottom: '16px' }}>
                  <h3 style={{ marginBottom: '12px' }}>Semua Kandidat Penyakit</h3>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Penyakit</th>
                          <th>CF RBR</th>
                          <th>Sim CBR</th>
                          <th>Agreement</th>
                          <th>Skor Akhir</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.semua_kandidat.map((k, i) => (
                          <tr key={i}>
                            <td style={{ fontWeight: i === 0 ? 600 : 400 }}>
                              {toTitleCase(k.nama_penyakit)}
                            </td>
                            <td className="font-mono">{k.cf_rbr?.toFixed(2)}</td>
                            <td className="font-mono">{k.sim_cbr?.toFixed(2)}</td>
                            <td className="font-mono">{k.agreement_score?.toFixed(1)}</td>
                            <td className="font-mono" style={{ fontWeight: 600 }}>
                              {(k.final_score * 100).toFixed(2)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Reset button */}
          <div style={{ textAlign: 'center', paddingTop: '12px', paddingBottom: '32px' }}>
            <button className="btn btn-primary" onClick={handleReset}>
              <RefreshCcw size={16} />
              Diagnosis Baru
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
