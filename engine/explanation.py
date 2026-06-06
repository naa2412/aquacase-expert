"""
explanation.py — Explanation Facility untuk AquaCase Expert
===========================================================
Menghasilkan penjelasan tentang bagaimana sistem
mencapai kesimpulan diagnosis.

OUTPUT WAJIB:
    - pesan_utama        : sebut nama penyakit, CF, similarity secara eksplisit
    - aturan_aktif       : teks IF-THEN dari lookup KB (bukan hanya ID)
    - top_similar_cases  : 3 kasus + gejala cocok/tidak cocok
    - fusion_breakdown   : komponen skor per bobot
    - status_threshold   : "Kuat" >= 0.75 / "Sedang" 0.50-0.74 / "Lemah" < 0.50
    - rekomendasi        : lookup field 'penanganan' di KB (bukan hardcoded)
"""

from typing import Optional


class ExplanationFacility:
    def __init__(self, w_rbr: float, w_cbr: float, w_agreement: float,
                 threshold: float, solusi_info: dict = None,
                 penyakit_info: dict = None, rules_data: list = None,
                 gejala_info: dict = None):
        """
        Inisialisasi pembuat penjelasan dengan parameter yang sama
        dengan Hybrid Engine, ditambah akses ke data KB.

        Parameters
        ----------
        w_rbr         : Bobot RBR dalam fusion
        w_cbr         : Bobot CBR dalam fusion
        w_agreement   : Bobot Agreement dalam fusion
        threshold     : Batas minimal skor
        solusi_info   : {kode_penyakit: solusi} dari solusi.json
        penyakit_info : {kode_penyakit: nama_penyakit} dari penyakit.json
        rules_data    : list[Rule] dari RBR engine
        gejala_info   : {kode_gejala: nama_gejala} dari gejala.json
        """
        self.w_rbr = w_rbr
        self.w_cbr = w_cbr
        self.w_agreement = w_agreement
        self.threshold = threshold
        self.solusi_info = solusi_info or {}
        self.penyakit_info = penyakit_info or {}
        self.rules_data = rules_data or []
        self.gejala_info = gejala_info or {}

    def generate_full_explanation(self, best_match: Optional[dict],
                                  rbr_raw: dict, cbr_raw: dict,
                                  is_conflict: bool,
                                  kandidat_konflik: list) -> dict:
        """
        Membangun objek penjelasan komprehensif untuk dirender oleh UI.

        Returns
        -------
        dict berisi: summary, rbr_analysis, cbr_analysis, fusion_breakdown,
                     conflict_analysis, rekomendasi
        """
        explanation = {
            "summary": self._build_summary(best_match, is_conflict, kandidat_konflik),
            "rbr_analysis": self._build_rbr_details(
                rbr_raw,
                best_match.get('kode_penyakit') if best_match else None
            ),
            "cbr_analysis": self._build_cbr_details(cbr_raw),
            "fusion_breakdown": self._build_fusion_breakdown(best_match) if best_match else None,
            "conflict_analysis": self._build_conflict_details(kandidat_konflik) if is_conflict else None,
            "rekomendasi": self._get_recommendation(best_match, is_conflict)
        }

        return explanation

    def _build_summary(self, best: Optional[dict], is_conflict: bool,
                       konflik: list) -> dict:
        """
        Membuat ringkasan diagnosis akhir dengan pesan_utama yang
        menyebut nama penyakit, CF, dan similarity secara eksplisit.
        """
        if is_conflict:
            return {
                "status_diagnosis": "KONFLIK (Butuh Validasi Pakar)",
                "pesan_utama": (
                    f"Sistem mendeteksi ambiguitas antara "
                    f"{konflik[0]['nama_penyakit']} (skor: {konflik[0]['final_score']:.2f}) "
                    f"dan {konflik[1]['nama_penyakit']} (skor: {konflik[1]['final_score']:.2f}). "
                    f"Diperlukan validasi pakar untuk konfirmasi diagnosis."
                ),
                "skor_akhir": None,
                "is_threshold_passed": False,
                "status_threshold": "Konflik"
            }

        if not best:
            return {
                "status_diagnosis": "GAGAL",
                "pesan_utama": "Tidak ada diagnosis yang dapat dihasilkan.",
                "skor_akhir": None,
                "is_threshold_passed": False,
                "status_threshold": "Tidak ada data"
            }

        skor = best['final_score']
        cf_rbr = best.get('cf_rbr', 0.0)
        sim_cbr = best.get('sim_cbr', 0.0)

        if skor >= 0.75:
            status = "Kuat"
        elif skor >= 0.50:
            status = "Sedang"
        else:
            status = "Lemah"

        return {
            "status_diagnosis": "BERHASIL",
            # pesan_utama menyebut nama penyakit, CF, similarity eksplisit
            "pesan_utama": (
                f"Berdasarkan analisis hybrid, ikan didiagnosis mengalami "
                f"{best['nama_penyakit']} dengan skor akhir {skor:.2f} "
                f"(CF RBR: {cf_rbr:.2f}, Similarity CBR: {sim_cbr:.2f}). "
                f"Tingkat keyakinan: {status}."
            ),
            "skor_akhir": round(skor * 100, 2),
            "is_threshold_passed": skor >= self.threshold,
            "status_threshold": status
        }

    def _build_rbr_details(self, rbr_raw: dict, target_pid: Optional[str]) -> dict:
        """
        Menyusun penjelasan dari sisi Rule-Based Reasoning.
        [FIX-8] Mengambil dari 'rules_triggered' (bukan 'rules_aktif')
        dan konversi ke teks IF-THEN dari lookup KB.
        """
        # Cari CF score untuk penyakit target dari output RBR
        cf_score = 0.0
        for diag in rbr_raw.get('diagnosis', []):
            if diag.get('kode_penyakit') == target_pid:
                cf_score = diag['cf_akhir']
                break

        rules_triggered = rbr_raw.get('rules_triggered', [])

        # Filter rules yang relevan dengan penyakit target
        rules_for_target = [
            r for r in rules_triggered
            if r.get('id_penyakit') == target_pid
        ]

        # Konversi ke teks IF-THEN yang informatif
        aturan_aktif = []
        for r in rules_for_target:
            premis_names = [
                p.get('nama_gejala', p.get('kode_gejala', '?'))
                for p in r.get('premis', [])
            ]
            nama_penyakit = r.get('nama_penyakit', target_pid)
            rule_text = (
                f"IF {' AND '.join(premis_names)} "
                f"THEN {nama_penyakit} "
                f"[CF Pakar: {r.get('cf_pakar', 0)}, CF Rule: {r.get('cf_rule', 0)}]"
            )
            aturan_aktif.append({
                "id_rule": r.get('id_rule'),
                "rule_text": rule_text,
                "cf_pakar": r.get('cf_pakar'),
                "cf_komposit": r.get('cf_komposit'),
                "cf_rule": r.get('cf_rule'),
                "premis": r.get('premis', [])
            })

        return {
            "cf_score": round(cf_score, 4),
            "cf_score_persen": round(cf_score * 100, 2),
            "keterangan": (
                "Certainty Factor (CF) dihitung berdasarkan aturan pakar "
                "menggunakan metode Forward Chaining. CF Komposit = min(CF user) "
                "per premis, lalu CF Rule = CF Komposit x CF Pakar."
            ),
            "jumlah_rule_aktif": len(aturan_aktif),
            "aturan_aktif": aturan_aktif
        }

    def _build_cbr_details(self, cbr_raw: dict) -> dict:
        """
        Menyusun penjelasan dari sisi Case-Based Reasoning.
        [FIX-9] Field similarity diambil dari 'similarity_best'.
        Ditambah top_similar_cases dengan gejala cocok/tidak cocok.
        """
        top_case = cbr_raw.get('diagnosis_utama')
        if not top_case:
            return {
                "similarity_score": 0,
                "similarity_persen": 0,
                "top_similar_cases": [],
                "gejala_cocok": [],
                "gejala_tidak_cocok": []
            }

        similarity = top_case.get('similarity_best', 0.0)

        # Bangun top_similar_cases dari top_kasus di cbr_raw
        top_kasus_raw = cbr_raw.get('top_kasus', [])
        top_similar_cases = []
        for k in top_kasus_raw[:3]:  # top-3
            top_similar_cases.append({
                "kode_kasus": k.get('kode_kasus'),
                "jenis_ikan": k.get('jenis_ikan'),
                "kode_penyakit": k.get('kode_penyakit'),
                "nama_penyakit": k.get('nama_penyakit'),
                "similarity": k.get('similarity'),
                "similarity_persen": round(k.get('similarity', 0) * 100, 2),
                "coverage": k.get('komponen', {}).get('coverage', ''),
            })

        # Gejala cocok/tidak cocok dari explanation CBR
        cbr_explanation = cbr_raw.get('explanation', {})
        gejala_cocok = cbr_explanation.get('gejala_cocok', [])
        gejala_tidak_cocok = cbr_explanation.get('gejala_tidak_cocok', [])

        return {
            "similarity_score": round(similarity, 4),
            "similarity_persen": round(similarity * 100, 2),
            "kode_kasus_terdekat": top_case.get('kode_kasus_ref', 'Tidak diketahui'),
            "nama_penyakit_cbr": top_case.get('nama_penyakit', ''),
            "top_similar_cases": top_similar_cases,
            "gejala_cocok": gejala_cocok,
            "gejala_tidak_cocok": gejala_tidak_cocok,
            "keterangan": (
                "Persentase kemiripan dihitung menggunakan algoritma "
                "Nearest Neighbor (Mancasari, 2012): "
                "Sim(S,T) = [Sum f(Si,Ti)*wi / Sum wi] x P(S)."
            )
        }

    def _build_fusion_breakdown(self, best: dict) -> dict:
        """
        Mengirimkan komponen perhitungan matematika pembentuk skor akhir.
        [FIX-11] Copy-paste bug diperbaiki: bobot_cbr pakai self.w_cbr.
        """
        cf_rbr = best.get('cf_rbr', 0.0)
        sim_cbr = best.get('sim_cbr', 0.0)
        agreement = best.get('agreement_score', 0.0)

        return {
            "rumus": "Skor = (W_rbr x CF_RBR) + (W_cbr x Similarity_CBR) + (W_agr x Agreement)",
            "komponen": {
                "bobot_rbr": self.w_rbr,
                "skor_cf_rbr": round(cf_rbr, 4),
                "kontribusi_rbr": round(self.w_rbr * cf_rbr, 4),
                "bobot_cbr": self.w_cbr,
                "skor_sim_cbr": round(sim_cbr, 4),
                "kontribusi_cbr": round(self.w_cbr * sim_cbr, 4),
                "bobot_agreement": self.w_agreement,
                "skor_agreement": agreement,
                "kontribusi_agreement": round(self.w_agreement * agreement, 4),
            },
            "skor_akhir": round(
                (self.w_rbr * cf_rbr) +
                (self.w_cbr * sim_cbr) +
                (self.w_agreement * agreement),
                4
            )
        }

    def _build_conflict_details(self, konflik: list) -> dict:
        """
        Menyusun perbandingan mendalam saat terjadi konflik antara RBR dan CBR.
        """
        if len(konflik) < 2:
            return {"penyebab": "Data konflik tidak lengkap."}

        return {
            "penyebab": (
                "RBR dan CBR merekomendasikan penyakit yang berbeda di "
                "peringkat teratas, dengan selisih skor keseluruhan yang "
                "signifikan (>= 0.15). Diperlukan validasi pakar."
            ),
            "kandidat_1": {
                "kode_penyakit": konflik[0].get('kode_penyakit'),
                "nama": konflik[0]['nama_penyakit'],
                "skor_gabungan": round(konflik[0]['final_score'] * 100, 2),
                "dominasi": konflik[0].get('dominasi', 'N/A')
            },
            "kandidat_2": {
                "kode_penyakit": konflik[1].get('kode_penyakit'),
                "nama": konflik[1]['nama_penyakit'],
                "skor_gabungan": round(konflik[1]['final_score'] * 100, 2),
                "dominasi": konflik[1].get('dominasi', 'N/A')
            }
        }

    def _get_recommendation(self, best: Optional[dict], is_conflict: bool) -> str:
        """
        [FIX-7] Memberikan rekomendasi penanganan dari lookup solusi.json,
        bukan teks hardcoded generik.
        """
        if is_conflict:
            return (
                "Segera isolasi ikan yang menunjukkan gejala dan "
                "konsultasikan hasil sistem ini ke pakar perikanan "
                "setempat untuk analisis uji lab lanjutan."
            )

        if not best:
            return "Tidak ada rekomendasi karena diagnosis tidak tersedia."

        kode_penyakit = best.get('kode_penyakit', '')

        # Lookup solusi dari KB (solusi.json)
        solusi = self.solusi_info.get(kode_penyakit, '')

        if solusi:
            return solusi
        else:
            # Fallback jika solusi belum terdaftar di KB
            nama = best.get('nama_penyakit', kode_penyakit)
            return (
                f"Solusi untuk {nama} belum tersedia dalam basis pengetahuan. "
                f"Konsultasikan ke pakar perikanan untuk penanganan lebih lanjut."
            )
