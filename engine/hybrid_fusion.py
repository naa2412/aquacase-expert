"""
hybrid_fusion.py — Hybrid Fusion Engine untuk AquaCase Expert
=============================================================
Menggabungkan hasil RBR (Certainty Factor) dan CBR (Similarity)
menjadi satu skor diagnosis akhir.

RUMUS FUSION:
    Skor = (0.45 x CF_RBR) + (0.35 x Similarity_CBR) + (0.20 x Agreement)

AGREEMENT LOGIC (3-level, sesuai spesifikasi):
    1.0  — RBR dan CBR sepakat penyakit yang sama
    0.5  — RBR dan CBR berbeda, tapi selisih skor < 0.15 (konflik lemah)
    0.0  — RBR dan CBR berbeda, selisih skor >= 0.15 (konflik kuat)

CONFLICT HANDLING:
    Konflik LEMAH: id berbeda + selisih < 0.15  → tampilkan 2 kandidat
    Konflik KUAT:  id berbeda + selisih >= 0.15  → wajib validasi pakar

"""

import json
from rbr import RuleBasedReasoning
from cbr import CaseBasedReasoning
from explanation import ExplanationFacility


class HybridFusionEngine:
    def __init__(self, rbr_engine: RuleBasedReasoning, cbr_engine: CaseBasedReasoning,
                 # [FIX-1] Bobot default sesuai spesifikasi: 0.45 + 0.35 + 0.20 = 1.0
                 w_rbr: float = 0.45, w_cbr: float = 0.35, w_agreement: float = 0.20,
                 threshold: float = 0.6):
        """
        Inisialisasi Mesin Hybrid Fusion.

        Parameters
        ----------
        rbr_engine   : Instance RuleBasedReasoning yang sudah di-load KB
        cbr_engine   : Instance CaseBasedReasoning yang sudah di-load case base
        w_rbr        : Bobot untuk CF dari RBR (default 0.45)
        w_cbr        : Bobot untuk Similarity dari CBR (default 0.35)
        w_agreement  : Bobot untuk Agreement score (default 0.20)
        threshold    : Batas minimal final_score agar diagnosis dianggap valid
        """
        self.rbr = rbr_engine
        self.cbr = cbr_engine
        self.threshold = threshold

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

        Parameters
        ----------
        kode_ikan    : Kode jenis ikan target (misal 'J01')
        gejala_input : {kode_gejala: cf_user} — gejala dari pengguna

        Returns
        -------
        dict dengan field sesuai API contract:
          - is_conflict       : bool
          - diagnosis_akhir   : dict atau None (jika konflik kuat)
          - kandidat_konflik  : list (jika konflik)
          - semua_kandidat    : list semua penyakit + skor
          - explanation       : dict penjelasan lengkap
        """
        # 1. Eksekusi RBR & CBR
        rbr_result = self.rbr.diagnosis(gejala_input)
        cbr_result = self.cbr.diagnosis(kode_ikan, gejala_input, top_n=5)

        # 2. Ambil ID Penyakit Teratas dari masing-masing engine
        # [FIX-2] RBR output pakai 'kode_penyakit', bukan 'id_penyakit'
        top_rbr_id = (rbr_result['diagnosis'][0]['kode_penyakit']
                      if rbr_result.get('diagnosis') else None)
        top_cbr_id = (cbr_result['diagnosis_utama']['kode_penyakit']
                      if cbr_result.get('diagnosis_utama') else None)

        # 3. Ekstraksi Skor per penyakit
        # [FIX-2] Field 'kode_penyakit' konsisten
        rbr_scores = {
            d['kode_penyakit']: max(0.0, min(1.0, d['cf_akhir']))
            for d in rbr_result.get('diagnosis', [])
        }

        cbr_scores = {}
        for case in cbr_result.get('top_kasus', []):
            pid = case['kode_penyakit']
            sim = case['similarity']
            if pid not in cbr_scores or sim > cbr_scores[pid]:
                cbr_scores[pid] = max(0.0, min(1.0, sim))

        # 4. Weighted Fusion Process
        all_diseases = set(rbr_scores.keys()).union(set(cbr_scores.keys()))
        fused_results = []

        for pid in all_diseases:
            cf_rbr = rbr_scores.get(pid, 0.0)
            sim_cbr = cbr_scores.get(pid, 0.0)

            # [FIX-3] Agreement Logic 3-level sesuai spesifikasi:
            #   1.0 — RBR dan CBR sepakat penyakit ini sebagai top-1
            #   0.5 — keduanya berbeda, tapi selisih skor < 0.15 (konflik lemah)
            #   0.0 — keduanya berbeda, selisih skor >= 0.15 (konflik kuat)
            if top_rbr_id == top_cbr_id and top_rbr_id == pid:
                agreement_score = 1.0
            elif top_rbr_id != top_cbr_id and pid in (top_rbr_id, top_cbr_id):
                # Hitung selisih skor antara kedua top candidates
                rbr_top_score = rbr_scores.get(top_rbr_id, 0.0) if top_rbr_id else 0.0
                cbr_top_score = cbr_scores.get(top_cbr_id, 0.0) if top_cbr_id else 0.0
                selisih = abs(rbr_top_score - cbr_top_score)
                agreement_score = 0.5 if selisih < 0.15 else 0.0
            else:
                agreement_score = 0.0

            # Perhitungan Skor Akhir
            final_score = (
                (self.w_rbr * cf_rbr) +
                (self.w_cbr * sim_cbr) +
                (self.w_agreement * agreement_score)
            )

            # Lookup nama penyakit dari KB
            nama_penyakit = self.rbr.penyakit_info.get(pid, pid)

            fused_results.append({
                'kode_penyakit': pid,
                'nama_penyakit': nama_penyakit,
                'cf_rbr': round(cf_rbr, 4),
                'sim_cbr': round(sim_cbr, 4),
                'agreement_score': agreement_score,
                'final_score': round(final_score, 4)
            })

        # 5. Urutkan berdasarkan Final Score terbesar
        fused_results.sort(key=lambda x: x['final_score'], reverse=True)

        # 6. Conflict Handling & Output
        return self._build_output(
            fused_results, top_rbr_id, top_cbr_id,
            rbr_result, cbr_result
        )

    def _build_output(self, fused_results: list, top_rbr_id: str,
                      top_cbr_id: str, rbr_raw: dict, cbr_raw: dict) -> dict:
        """
        Membangun output akhir sesuai API contract.

        [FIX-5] Output mencakup is_conflict, diagnosis_akhir, kandidat_konflik.
        """
        if not fused_results:
            return {
                'is_conflict': False,
                'diagnosis_akhir': None,
                'kandidat_konflik': [],
                'semua_kandidat': [],
                'explanation': {
                    'summary': {
                        'status_diagnosis': 'GAGAL',
                        'pesan_utama': 'Tidak ada gejala yang cocok dengan basis pengetahuan.'
                    }
                }
            }

        best_match = fused_results[0]

        # --- CONFLICT HANDLING LOGIC ---
        # [FIX-4] Threshold konflik sesuai spesifikasi: 0.15
        is_conflict = False
        kandidat_konflik = []

        if top_rbr_id and top_cbr_id and (top_rbr_id != top_cbr_id):
            if len(fused_results) >= 2:
                selisih_skor = fused_results[0]['final_score'] - fused_results[1]['final_score']

                if selisih_skor < 0.15:
                    # Konflik lemah — tampilkan 2 kandidat, tapi tetap beri diagnosis
                    is_conflict = False
                    kandidat_konflik = [
                        {
                            'kode_penyakit': fused_results[0]['kode_penyakit'],
                            'nama_penyakit': fused_results[0]['nama_penyakit'],
                            'final_score': fused_results[0]['final_score'],
                            'dominasi': 'RBR' if fused_results[0]['cf_rbr'] > fused_results[0]['sim_cbr'] else 'CBR'
                        },
                        {
                            'kode_penyakit': fused_results[1]['kode_penyakit'],
                            'nama_penyakit': fused_results[1]['nama_penyakit'],
                            'final_score': fused_results[1]['final_score'],
                            'dominasi': 'RBR' if fused_results[1]['cf_rbr'] > fused_results[1]['sim_cbr'] else 'CBR'
                        }
                    ]

                if selisih_skor >= 0.15:
                    # Konflik kuat — TIDAK bisa disimpulkan, wajib validasi pakar
                    is_conflict = True
                    kandidat_konflik = [
                        {
                            'kode_penyakit': fused_results[0]['kode_penyakit'],
                            'nama_penyakit': fused_results[0]['nama_penyakit'],
                            'final_score': fused_results[0]['final_score'],
                            'dominasi': 'RBR' if fused_results[0]['cf_rbr'] > fused_results[0]['sim_cbr'] else 'CBR'
                        },
                        {
                            'kode_penyakit': fused_results[1]['kode_penyakit'],
                            'nama_penyakit': fused_results[1]['nama_penyakit'],
                            'final_score': fused_results[1]['final_score'],
                            'dominasi': 'RBR' if fused_results[1]['cf_rbr'] > fused_results[1]['sim_cbr'] else 'CBR'
                        }
                    ]

        # --- EXPLANATION FACILITY ---
        # [FIX-6] Pass solusi_info dan rules_data ke ExplanationFacility
        explainer = ExplanationFacility(
            w_rbr=self.w_rbr,
            w_cbr=self.w_cbr,
            w_agreement=self.w_agreement,
            threshold=self.threshold,
            solusi_info=self.rbr.solusi_info,
            penyakit_info=self.rbr.penyakit_info,
            rules_data=self.rbr.rules,
            gejala_info=self.rbr.gejala_info,
        )

        explanation_data = explainer.generate_full_explanation(
            best_match=best_match if not is_conflict else None,
            rbr_raw=rbr_raw,
            cbr_raw=cbr_raw,
            is_conflict=is_conflict,
            kandidat_konflik=kandidat_konflik
        )

        # [FIX-5] Output sesuai API contract
        return {
            'is_conflict': is_conflict,
            'diagnosis_akhir': best_match if not is_conflict else None,
            'kandidat_konflik': kandidat_konflik if is_conflict else [],
            'semua_kandidat': fused_results,
            'explanation': explanation_data
        }
