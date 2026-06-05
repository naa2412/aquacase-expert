import json
from rbr import RuleBasedReasoning
from cbr import CaseBasedReasoning

class HybridFusionEngine:
    def __init__(self, rbr_engine: RuleBasedReasoning, cbr_engine: CaseBasedReasoning, 
                 w_rbr: float = 0.3, w_cbr: float = 0.5, w_agreement: float = 0.2):
        """
        Inisialisasi Mesin Hybrid Fusion.
        
        :param w_rbr: Bobot untuk skor Certainty Factor dari RBR (default 0.3)
        :param w_cbr: Bobot untuk skor Similarity dari CBR (default 0.5)
        :param w_agreement: Bobot bonus jika RBR dan CBR sepakat (default 0.2)
        """
        self.rbr = rbr_engine
        self.cbr = cbr_engine
        
        # Validasi bobot agar total = 1.0
        total_weight = w_rbr + w_cbr + w_agreement
        if abs(total_weight - 1.0) > 1e-5:
            raise ValueError("Total bobot (w_rbr + w_cbr + w_agreement) harus sama dengan 1.0")
            
        self.w_rbr = w_rbr
        self.w_cbr = w_cbr
        self.w_agreement = w_agreement

    def diagnose(self, kode_ikan: str, gejala_input: dict) -> dict:
        """
        Menjalankan diagnosis hybrid dan mengembalikan hasil fusion.
        """
        # 1. Eksekusi RBR
        rbr_result = self.rbr.diagnosis(gejala_input)
        
        # Ambil ID penyakit teratas dari RBR (untuk perhitungan agreement)
        top_rbr_id = rbr_result['diagnosis'][0]['id_penyakit'] if rbr_result['diagnosis'] else None
        
        # Map skor RBR per penyakit: { 'P01': 0.85, 'P02': 0.40, ... }
        rbr_scores = {d['id_penyakit']: max(0.0, min(1.0, d['cf_akhir'])) for d in rbr_result['diagnosis']}

        # 2. Eksekusi CBR
        cbr_result = self.cbr.diagnosis(kode_ikan, gejala_input, top_n=5)
        
        # Ambil ID penyakit teratas dari CBR
        top_cbr_id = cbr_result['diagnosis_utama']['kode_penyakit'] if cbr_result['diagnosis_utama'] else None
        
        # Map skor CBR per penyakit. 
        # Jika ada beberapa kasus untuk penyakit yang sama, ambil similarity TERTINGGI (max)
        cbr_scores = {}
        for case in cbr_result['top_kasus']:
            pid = case['kode_penyakit']
            sim = case['similarity']
            if pid not in cbr_scores or sim > cbr_scores[pid]:
                cbr_scores[pid] = max(0.0, min(1.0, sim))

        # 3. Weighted Fusion Process
        # Gabungkan semua kandidat penyakit yang muncul di RBR atau CBR
        all_diseases = set(rbr_scores.keys()).union(set(cbr_scores.keys()))
        
        fused_results = []
        for pid in all_diseases:
            cf_rbr = rbr_scores.get(pid, 0.0)
            sim_cbr = cbr_scores.get(pid, 0.0)
            
            # Logika Agreement: 
            # Nilai 1.0 HANYA jika penyakit ini adalah juara 1 di RBR DAN juara 1 di CBR.
            # Ini adalah "Strong Agreement" yang memberikan boost signifikan.
            is_strong_agreement = (top_rbr_id == top_cbr_id) and (top_rbr_id == pid)
            agreement_score = 1.0 if is_strong_agreement else 0.0
            
            # Rumus Weighted Hybrid Fusion
            final_score = (self.w_rbr * cf_rbr) + (self.w_cbr * sim_cbr) + (self.w_agreement * agreement_score)
            
            # Ambil nama penyakit (fallback ke RBR atau CBR info)
            nama_penyakit = self.rbr.penyakit_info.get(pid) or self.cbr.penyakit_info.get(pid, f"Penyakit {pid}")
            
            fused_results.append({
                'id_penyakit': pid,
                'nama_penyakit': nama_penyakit,
                'cf_rbr': round(cf_rbr, 4),
                'sim_cbr': round(sim_cbr, 4),
                'agreement_score': agreement_score,
                'final_score': round(final_score, 4)
            })

        # 4. Urutkan berdasarkan Final Score terbesar
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)

        # 5. Bangun Output & Explanation Facility
        return self._build_output(fused_results, top_rbr_id, top_cbr_id, rbr_result, cbr_result)

    def _build_output(self, fused_results: list, top_rbr_id: str, top_cbr_id: str, rbr_raw: dict, cbr_raw: dict) -> dict:
        """Membentuk output akhir yang ramah untuk Frontend/Laporan."""
        if not fused_results or fused_results[0]['final_score'] == 0.0:
            return {
                'status': 'GAGAL',
                'pesan': 'Tidak ada diagnosis yang memenuhi threshold minimal.',
                'detail': []
            }

        best_match = fused_results[0]
        
        # Generate Penjelasan (Explanation Facility)
        explanation = self._generate_explanation(best_match, top_rbr_id, top_cbr_id)

        return {
            'status': 'BERHASIL',
            'diagnosis_akhir': best_match,
            'semua_kandidat': fused_results,
            'explanation': explanation,
            'debug_info': { # Opsional: untuk presentasi ke dosen
                'top_rbr': top_rbr_id,
                'top_cbr': top_cbr_id,
                'bobot_digunakan': {'w_rbr': self.w_rbr, 'w_cbr': self.w_cbr, 'w_agreement': self.w_agreement}
            }
        }

    def _generate_explanation(self, best: dict, top_rbr_id: str, top_cbr_id: str) -> str:
        """Membuat narasi penjelasan mengapa sistem memilih diagnosis ini."""
        nama = best['nama_penyakit']
        score = best['final_score'] * 100
        
        # Cek komponen mana yang dominan
        komponen = []
        if best['cf_rbr'] > 0:
            komponen.append(f"aturan pakar mendukung ({best['cf_rbr']*100:.1f}%)")
        if best['sim_cbr'] > 0:
            komponen.append(f"mirip dengan kasus historis ({best['sim_cbr']*100:.1f}%)")
        if best['agreement_score'] == 1.0:
            komponen.append("terdapat kesepakatan penuh (agreement) antara analisis aturan dan kasus historis")

        penjelasan = (
            f"Sistem mendiagnosis penyakit sebagai **{nama}** dengan tingkat keyakinan hybrid sebesar **{score:.2f}%**. "
            f"Keputusan ini diambil karena: "
        )
        
        if len(komponen) > 1:
            penjelasan += ", ".join(komponen[:-1]) + f", dan {komponen[-1]}."
        else:
            penjelasan += komponen[0] + "."
            
        if best['agreement_score'] == 0.0 and best['cf_rbr'] > 0 and best['sim_cbr'] > 0:
            penjelasan += " (Catatan: RBR dan CBR menunjuk ke penyakit teratas yang berbeda, namun penyakit ini memiliki kombinasi skor tertinggi)."

        return penjelasan


# ==========================================
# CONTOH PENGGUNAAN / TESTING
# ==========================================
if __name__ == "__main__":
    print("="*60)
    print("  AquaCase Expert — HYBRID FUSION ENGINE DEMO")
    print("="*60)

    # 1. Inisialisasi Engine
    rbr = RuleBasedReasoning()
    rbr.load_knowledge_base('AquaCase_Knowledge_Base')
    
    cbr = CaseBasedReasoning(
        path_case_base="AquaCase_Knowledge_Base/case_base.json",
        path_penyakit="AquaCase_Knowledge_Base/penyakit.json",
        path_gejala="AquaCase_Knowledge_Base/gejala.json",
        path_solusi="AquaCase_Knowledge_Base/solusi.json"
    )

    # 2. Inisialisasi Hybrid Fusion dengan Bobot Tertentu
    # Misal: Kita lebih percaya pengalaman kasus (CBR), tapi aturan (RBR) tetap penting
    hybrid = HybridFusionEngine(
        rbr_engine=rbr, 
        cbr_engine=cbr, 
        w_rbr=0.3, 
        w_cbr=0.5, 
        w_agreement=0.2
    )

    # 3. Input Pengguna (Skenario: Ikan Nila sakit)
    input_gejala = {
        "G01": 0.8,  # Nafsu makan menurun
        "G02": 0.7,  # Gerakan lemah
        "G05": 0.6,  # Luka di tubuh
    }
    kode_ikan = "J01" # Nila

    # 4. Jalankan Diagnosis Hybrid
    hasil_hybrid = hybrid.diagnose(kode_ikan, input_gejala)

    # 5. Tampilkan Hasil
    print("\n--- HASIL DIAGNOSIS HYBRID ---")
    if hasil_hybrid['status'] == 'BERHASIL':
        dx = hasil_hybrid['diagnosis_akhir']
        print(f"Penyakit Terdeteksi : {dx['nama_penyakit']} ({dx['id_penyakit']})")
        print(f"Final Hybrid Score  : {dx['final_score']:.4f} ({dx['final_score']*100:.2f}%)")
        print(f"  ├─ Kontribusi RBR (CF) : {dx['cf_rbr']:.4f}")
        print(f"  ├─ Kontribusi CBR (Sim): {dx['sim_cbr']:.4f}")
        print(f"  └─ Agreement Score     : {dx['agreement_score']:.1f}")
        
        print("\n--- EXPLANATION FACILITY ---")
        print(hasil_hybrid['explanation'])
        
        print("\n--- SEMUA KANDIDAT (RANKING) ---")
        for i, kandidat in enumerate(hasil_hybrid['semua_kandidat'], 1):
            print(f"{i}. {kandidat['nama_penyakit']:<25} | Score: {kandidat['final_score']:.4f}")
    else:
        print(hasil_hybrid['pesan'])
