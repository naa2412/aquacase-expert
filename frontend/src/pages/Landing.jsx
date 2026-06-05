import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Stethoscope, Database, BookOpen, Fish, ArrowRight, Activity, Shield, Zap } from 'lucide-react';
import { getIkan, getGejala, getKasus, getAturan, getPenyakit } from '../api/client';

export default function Landing() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const [ikan, gejala, kasus, aturan, penyakit] = await Promise.all([
          getIkan(), getGejala(), getKasus(), getAturan(), getPenyakit()
        ]);
        setStats({
          ikan: ikan.data.length,
          gejala: gejala.data.length,
          kasus: kasus.data.length,
          aturan: aturan.data.length,
          penyakit: penyakit.data.length,
        });
      } catch {
        setStats({ ikan: '-', gejala: '-', kasus: '-', aturan: '-', penyakit: '-' });
      }
    }
    loadStats();
  }, []);

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto' }}>
      {/* Hero Section */}
      <section style={{ textAlign: 'center', padding: '40px 0 48px' }}>
        <div style={{
          width: '72px',
          height: '72px',
          borderRadius: 'var(--radius-lg)',
          background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 24px',
          boxShadow: '0 8px 24px rgba(3, 105, 161, 0.3)',
        }}>
          <Fish size={36} color="white" />
        </div>

        <h1 style={{
          fontSize: 'clamp(1.75rem, 4vw, 2.5rem)',
          fontWeight: 700,
          marginBottom: '12px',
          background: 'linear-gradient(135deg, var(--color-primary-dark), var(--color-accent))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          AquaCase Expert
        </h1>

        <p style={{
          fontSize: '1.05rem',
          color: 'var(--text-muted)',
          maxWidth: '540px',
          margin: '0 auto 32px',
          lineHeight: 1.7,
        }}>
          Sistem Pakar Diagnosis Penyakit Ikan Air Tawar Menggunakan Metode
          Hybrid Case-Based Reasoning (CBR) Dan Rule-Based Reasoning (RBR)
          Dengan Certainty Factor.
        </p>

        <Link to="/diagnosis" className="btn btn-primary" style={{
          padding: '14px 32px',
          fontSize: '1rem',
          borderRadius: 'var(--radius-lg)',
        }}>
          <Stethoscope size={20} />
          Mulai Diagnosis
          <ArrowRight size={18} />
        </Link>
      </section>

      {/* Stats Section */}
      <section style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px',
        marginBottom: '48px',
      }}>
        {[
          { label: 'Jenis Ikan', value: stats?.ikan, icon: Fish, color: '#0284c7' },
          { label: 'Penyakit', value: stats?.penyakit, icon: Activity, color: '#dc2626' },
          { label: 'Gejala', value: stats?.gejala, icon: Stethoscope, color: '#059669' },
          { label: 'Rule Base', value: stats?.aturan, icon: BookOpen, color: '#d97706' },
          { label: 'Case Base', value: stats?.kasus, icon: Database, color: '#7c3aed' },
        ].map((item) => (
          <div key={item.label} className="glass-card" style={{ padding: '24px 20px', textAlign: 'center' }}>
            <item.icon size={24} style={{ color: item.color, marginBottom: '8px' }} />
            <div className="font-mono" style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              color: item.color,
              lineHeight: 1.2,
            }}>
              {stats ? item.value : (
                <div className="skeleton" style={{ height: '32px', width: '60px', margin: '0 auto' }} />
              )}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {item.label}
            </p>
          </div>
        ))}
      </section>

      {/* Feature Cards */}
      <section style={{ marginBottom: '48px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '24px' }}>Bagaimana Sistem Bekerja</h2>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: '20px',
        }}>
          {[
            {
              icon: BookOpen,
              title: 'Rule-Based Reasoning',
              desc: 'Menggunakan aturan pakar dengan metode Forward Chaining dan Certainty Factor untuk menghitung tingkat keyakinan diagnosis.',
              color: '#0284c7',
            },
            {
              icon: Database,
              title: 'Case-Based Reasoning',
              desc: 'Membandingkan gejala input dengan kasus-kasus lampau menggunakan algoritma Nearest Neighbor Similarity (Mancasari, 2012).',
              color: '#059669',
            },
            {
              icon: Zap,
              title: 'Hybrid Fusion',
              desc: 'Menggabungkan hasil RBR dan CBR dengan bobot 0.45, 0.35, 0.20 untuk menghasilkan diagnosis yang lebih akurat dan terjelaskan.',
              color: '#d97706',
            },
          ].map((feat) => (
            <div key={feat.title} className="glass-card" style={{ padding: '28px 24px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: 'var(--radius-md)',
                background: `${feat.color}12`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '16px',
              }}>
                <feat.icon size={22} style={{ color: feat.color }} />
              </div>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '8px' }}>{feat.title}</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.65 }}>
                {feat.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Explanation Facility */}
      <section className="glass-card-static" style={{
        padding: '36px 40px',
        textAlign: 'center',
        marginBottom: '48px',
      }}>
        <Shield size={32} style={{ color: 'var(--color-primary)', marginBottom: '14px' }} />
        <h3 style={{ marginBottom: '12px', fontSize: '1.15rem' }}>Explanation Facility</h3>
        <p style={{
          fontSize: '1rem',
          color: 'var(--text-muted)',
          margin: '0 auto',
          lineHeight: 1.8,
          textAlign: 'justify',
        }}>
          Setiap hasil diagnosis disertai penjelasan lengkap: aturan yang aktif, kasus serupa dari basis kasus, breakdown perhitungan skor hybrid fusion, dan rekomendasi penanganan yang diambil langsung dari basis pengetahuan.
        </p>
      </section>
    </div>
  );
}
