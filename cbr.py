"""
cbr.py — Case-Based Reasoning (CBR) untuk AquaCase Expert
=========================================================
Implementasi siklus 4R (Retrieve, Reuse, Revise, Retain)
menggunakan NN Similarity (Mancasari, 2012).

Struktur data mengikuti case_base.json dan case_gejala.json
yang sudah ada di repo.

Penulis  : (nama kamu)
Kelompok : AquaCase Expert — UGM
"""

import json
import os
from typing import Optional


# ===========================================================
# BAGIAN 1: REPRESENTASI DATA (Frame/Case)
# ===========================================================

class Case:
    """
    Representasi satu kasus dalam Case Base.
    Setiap kasus adalah 'memori' kejadian penyakit yang pernah
    tercatat, lengkap dengan jenis ikan, gejala beserta bobotnya,
    penyakit yang terdiagnosis, dan keyakinan pakar.
    """

    def __init__(self, kode_kasus: str, kode_penyakit: str,
                 kode_ikan: str, jenis_ikan: str, cf_pakar: float,
                 gejala: list[dict]):
        """
        Parameters
        ----------
        kode_kasus   : str   - ID kasus, misal 'K001'
        kode_penyakit: str   - ID penyakit hasil diagnosis, misal 'P01'
        kode_ikan    : str   - ID jenis ikan, misal 'J01'
        jenis_ikan   : str   - Nama jenis ikan, misal 'Nila'
        cf_pakar     : float - Keyakinan pakar atas kasus ini (P(S) dalam rumus)
        gejala       : list  - Daftar dict {'kode_gejala': str, 'bobot': float}
        """
        self.kode_kasus    = kode_kasus
        self.kode_penyakit = kode_penyakit
        self.kode_ikan     = kode_ikan
        self.jenis_ikan    = jenis_ikan
        self.cf_pakar      = cf_pakar
        # Konversi list gejala ke dict untuk akses cepat: {kode_gejala: bobot}
        self.gejala: dict[str, float] = {
            g["kode_gejala"]: g["bobot"] for g in gejala
        }

    def __repr__(self):
        return (f"Case({self.kode_kasus}, ikan={self.jenis_ikan}, "
                f"penyakit={self.kode_penyakit}, "
                f"gejala={list(self.gejala.keys())})")


# ===========================================================
# BAGIAN 2: CASE-BASED REASONING ENGINE
# ===========================================================

class CaseBasedReasoning:
    """
    Engine CBR dengan siklus 4R:
      Retrieve  → hitung similarity semua kasus, ambil top-N
      Reuse     → pakai diagnosis dari kasus paling mirip
      Revise    → koreksi hasil jika diperlukan (manual / opsional)
      Retain    → simpan kasus baru ke case base
    """

    def __init__(self,
                 path_case_base: str = "AquaCase_Knowledge_Base/case_base.json",
                 path_penyakit: str  = "AquaCase_Knowledge_Base/penyakit.json",
                 path_gejala: str    = "AquaCase_Knowledge_Base/gejala.json",
                 path_solusi: str    = "AquaCase_Knowledge_Base/solusi.json",
                 threshold: float   = 0.0):
        """
        Parameters
        ----------
        path_case_base : Path ke file case_base.json
        path_penyakit  : Path ke file penyakit.json
        path_gejala    : Path ke file gejala.json
        path_solusi    : Path ke file solusi.json
        threshold      : Hanya pertimbangkan kasus dengan similarity >= threshold
        """
        self.threshold   = threshold
        self.cases: list[Case] = []
        self.penyakit_info: dict[str, str]  = {}   # {kode: nama}
        self.gejala_info:   dict[str, str]  = {}   # {kode: nama}
        self.solusi_info:   dict[str, str]  = {}   # {kode_penyakit: solusi}

        self._load_penyakit(path_penyakit)
        self._load_gejala(path_gejala)
        self._load_solusi(path_solusi)
        self._load_case_base(path_case_base)

    # ----------------------------------------------------------
    # LOADER — baca JSON dari disk
    # ----------------------------------------------------------

    def _load_json(self, path: str) -> list | dict:
        if not os.path.exists(path):
            print(f"[PERINGATAN] File tidak ditemukan: {path}. Menggunakan data kosong.")
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_case_base(self, path: str):
        data = self._load_json(path)
        for item in data:
            case = Case(
                kode_kasus    = item["kode_kasus"],
                kode_penyakit = item["kode_penyakit"],
                kode_ikan     = item["kode_ikan"],
                jenis_ikan    = item["jenis_ikan"],
                cf_pakar      = item.get("cf_pakar", 0.9),
                gejala        = item.get("gejala", [])
            )
            self.cases.append(case)
        print(f"[INFO] Loaded {len(self.cases)} kasus dari {path}")

    def _load_penyakit(self, path: str):
        data = self._load_json(path)
        for item in data:
            self.penyakit_info[item["kode_penyakit"]] = item["nama_penyakit"]

    def _load_gejala(self, path: str):
        data = self._load_json(path)
        for item in data:
            self.gejala_info[item["kode_gejala"]] = item["nama_gejala"]

    def _load_solusi(self, path: str):
        data = self._load_json(path)
        for item in data:
            # solusi.json bisa berbentuk {kode_penyakit, solusi} atau mirip itu
            kode = item.get("kode_penyakit", "")
            sol  = item.get("solusi", "Belum ada solusi terdaftar.")
            if kode:
                self.solusi_info[kode] = sol

    # ----------------------------------------------------------
    # RETRIEVE — Hitung NN Similarity
    # ----------------------------------------------------------

    def _hitung_similarity(self,
                           source: Case,
                           target_gejala: dict[str, float],
                           target_kode_ikan: str) -> dict:
        """
        Menghitung similarity antara source case (S) dan target case (T)
        menggunakan rumus NN Similarity (Mancasari, 2012):

            Sim(S,T) = ( Σ f(Si,Ti)*wi / Σ wi ) * P(S) * ( J(Si,Ti) / J(Ti) )

        Catatan:
        - f(Si,Ti) = 1 jika gejala ke-i dari target ADA di source, 0 jika tidak
        - wi       = bobot gejala ke-i di SOURCE case
        - P(S)     = cf_pakar dari source case
        - J(Si,Ti) = jumlah gejala target yang cocok di source
        - J(Ti)    = total gejala target

        Selain itu, kasus dengan jenis ikan berbeda mendapat penalti similarity.
        """

        # Jenis ikan berbeda → similarity langsung 0
        # (ikan berbeda = kasus tidak relevan)
        if source.kode_ikan != target_kode_ikan:
            return {
                "similarity": 0.0,
                "penjelasan": f"Jenis ikan berbeda ({source.jenis_ikan} vs target)",
                "terlewat_karena_ikan": True
            }

        gejala_target: set[str] = set(target_gejala.keys())
        gejala_source: set[str] = set(source.gejala.keys())

        # J(Ti) = jumlah gejala target
        j_ti = len(gejala_target)
        if j_ti == 0:
            return {"similarity": 0.0, "penjelasan": "Target tidak punya gejala."}

        # J(Si,Ti) = gejala target yang ADA di source
        cocok = gejala_target & gejala_source
        j_si_ti = len(cocok)

        # Σ f(Si,Ti)*wi dan Σ wi (iterasi atas gejala SOURCE)
        sum_f_w = 0.0
        sum_w   = 0.0
        detail_gejala = []

        for kode_g, bobot_s in source.gejala.items():
            f = 1.0 if kode_g in gejala_target else 0.0
            sum_f_w += f * bobot_s
            sum_w   += bobot_s
            detail_gejala.append({
                "kode_gejala" : kode_g,
                "nama_gejala" : self.gejala_info.get(kode_g, kode_g),
                "bobot_source": bobot_s,
                "cocok"       : bool(f)
            })

        # Hindari pembagian nol
        if sum_w == 0:
            return {"similarity": 0.0, "penjelasan": "Bobot source case kosong."}

        komponen_bobot     = sum_f_w / sum_w          # Σ f*w / Σ w
        komponen_pakar     = source.cf_pakar           # P(S)
        komponen_coverage  = j_si_ti / j_ti            # J(Si,Ti) / J(Ti)

        similarity = komponen_bobot * komponen_pakar * komponen_coverage

        return {
            "similarity"         : round(similarity, 6),
            "komponen_bobot"     : round(komponen_bobot, 4),
            "komponen_pakar"     : komponen_pakar,
            "komponen_coverage"  : round(komponen_coverage, 4),
            "j_ti"               : j_ti,
            "j_si_ti"            : j_si_ti,
            "sum_f_w"            : round(sum_f_w, 4),
            "sum_w"              : round(sum_w, 4),
            "detail_gejala"      : detail_gejala,
            "terlewat_karena_ikan": False
        }

    def retrieve(self,
                 target_gejala: dict[str, float],
                 target_kode_ikan: str,
                 top_n: int = 5) -> list[dict]:
        """
        Langkah RETRIEVE: hitung similarity semua kasus, kembalikan top-N.

        Parameters
        ----------
        target_gejala    : {kode_gejala: cf_user} — input dari pengguna
        target_kode_ikan : kode jenis ikan target, misal 'J01'
        top_n            : berapa kasus teratas yang dikembalikan

        Returns
        -------
        List of dict diurutkan dari similarity tertinggi, masing-masing berisi:
          - case        : objek Case
          - similarity  : nilai similarity
          - detail_sim  : breakdown komponen similarity (untuk explanation)
        """
        hasil = []

        for case in self.cases:
            detail = self._hitung_similarity(case, target_gejala, target_kode_ikan)
            sim    = detail.get("similarity", 0.0)

            if sim >= self.threshold and not detail.get("terlewat_karena_ikan", False):
                hasil.append({
                    "case"       : case,
                    "similarity" : sim,
                    "detail_sim" : detail
                })

        # Urutkan dari similarity terbesar
        hasil.sort(key=lambda x: x["similarity"], reverse=True)
        return hasil[:top_n]

    # ----------------------------------------------------------
    # REUSE — Ambil diagnosis dari kasus paling mirip
    # ----------------------------------------------------------

    def reuse(self, retrieved_cases: list[dict]) -> Optional[dict]:
        """
        Langkah REUSE: ambil diagnosis dari kasus dengan similarity tertinggi.

        Jika ada beberapa kasus di posisi teratas dengan penyakit berbeda,
        sistem menggunakan kasus #1 (similarity tertinggi).

        Returns dict hasil diagnosis atau None jika tidak ada kasus ditemukan.
        """
        if not retrieved_cases:
            return None

        best = retrieved_cases[0]
        case = best["case"]

        return {
            "kode_penyakit" : case.kode_penyakit,
            "nama_penyakit" : self.penyakit_info.get(case.kode_penyakit, case.kode_penyakit),
            "similarity"    : best["similarity"],
            "kode_kasus_ref": case.kode_kasus,
            "solusi"        : self.solusi_info.get(case.kode_penyakit, "Solusi belum tersedia."),
            "cf_pakar"      : case.cf_pakar
        }

    # ----------------------------------------------------------
    # REVISE — Koreksi diagnosis (opsional / manual)
    # ----------------------------------------------------------

    def revise(self,
               hasil_reuse: dict,
               koreksi_penyakit: Optional[str] = None,
               koreksi_solusi: Optional[str]   = None) -> dict:
        """
        Langkah REVISE: koreksi hasil diagnosis jika pakar/user
        mengetahui bahwa diagnosis otomatis salah.

        Parameters
        ----------
        hasil_reuse        : dict hasil dari reuse()
        koreksi_penyakit   : kode penyakit yang benar (opsional)
        koreksi_solusi     : solusi yang benar (opsional)

        Returns
        -------
        dict hasil diagnosis yang sudah direvisi
        """
        hasil = hasil_reuse.copy()
        hasil["direvisi"] = False

        if koreksi_penyakit and koreksi_penyakit != hasil["kode_penyakit"]:
            print(f"[REVISE] Koreksi penyakit: {hasil['kode_penyakit']} → {koreksi_penyakit}")
            hasil["kode_penyakit"] = koreksi_penyakit
            hasil["nama_penyakit"] = self.penyakit_info.get(koreksi_penyakit, koreksi_penyakit)
            hasil["direvisi"]      = True

        if koreksi_solusi:
            print(f"[REVISE] Koreksi solusi diterapkan.")
            hasil["solusi"]    = koreksi_solusi
            hasil["direvisi"]  = True

        return hasil

    # ----------------------------------------------------------
    # RETAIN — Simpan kasus baru ke case base
    # ----------------------------------------------------------

    def retain(self,
               kode_ikan: str,
               jenis_ikan: str,
               target_gejala: dict[str, float],
               kode_penyakit: str,
               cf_pakar: float = 0.9,
               path_simpan: str = "case_base.json") -> Case:
        """
        Langkah RETAIN: tambahkan kasus baru ke case base (dalam memori
        dan ke file JSON agar persisten).

        Parameters
        ----------
        kode_ikan      : kode jenis ikan, misal 'J01'
        jenis_ikan     : nama jenis ikan, misal 'Nila'
        target_gejala  : {kode_gejala: cf_user} — input pengguna
        kode_penyakit  : diagnosis final (setelah revisi jika ada)
        cf_pakar       : tingkat keyakinan pakar (default 0.9)
        path_simpan    : path file JSON untuk menyimpan kasus baru

        Returns
        -------
        Case baru yang ditambahkan
        """
        # Generate kode kasus baru
        kode_baru = f"K{len(self.cases) + 1:03d}"

        # Pastikan tidak ada duplikasi kode
        kode_existing = {c.kode_kasus for c in self.cases}
        counter = len(self.cases) + 1
        while kode_baru in kode_existing:
            counter += 1
            kode_baru = f"K{counter:03d}"

        # Bangun objek Case baru
        gejala_list = [
            {"kode_gejala": kg, "bobot": bobot}
            for kg, bobot in target_gejala.items()
        ]
        case_baru = Case(
            kode_kasus    = kode_baru,
            kode_penyakit = kode_penyakit,
            kode_ikan     = kode_ikan,
            jenis_ikan    = jenis_ikan,
            cf_pakar      = cf_pakar,
            gejala        = gejala_list
        )

        # Tambahkan ke memori
        self.cases.append(case_baru)
        print(f"[RETAIN] Kasus baru ditambahkan ke memori: {kode_baru}")

        # Simpan ke file JSON
        self._simpan_case_base(path_simpan)

        return case_baru

    def _simpan_case_base(self, path: str):
        """Tulis ulang seluruh case base ke file JSON."""
        data = []
        for c in self.cases:
            data.append({
                "no"           : len(data) + 1,
                "kode_kasus"   : c.kode_kasus,
                "kode_penyakit": c.kode_penyakit,
                "kode_ikan"    : c.kode_ikan,
                "jenis_ikan"   : c.jenis_ikan,
                "cf_pakar"     : c.cf_pakar,
                "gejala"       : [
                    {"kode_gejala": kg, "bobot": bw}
                    for kg, bw in c.gejala.items()
                ]
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[RETAIN] Case base disimpan ke: {path} ({len(data)} kasus)")

    # ----------------------------------------------------------
    # MAIN DIAGNOSIS — Jalankan seluruh siklus CBR
    # ----------------------------------------------------------

    def diagnosis(self,
                  kode_ikan: str,
                  target_gejala: dict[str, float],
                  top_n: int = 5) -> dict:
        """
        Menjalankan siklus CBR lengkap (Retrieve + Reuse).
        Revise dan Retain dipanggil terpisah jika diperlukan.

        Parameters
        ----------
        kode_ikan      : kode jenis ikan yang sakit, misal 'J01'
        target_gejala  : {kode_gejala: cf_user} — gejala yang diamati user
        top_n          : berapa kasus referensi teratas yang ditampilkan

        Returns
        -------
        dict berisi:
          - diagnosis_utama : hasil dari kasus paling mirip
          - top_kasus       : top-N kasus mirip lengkap dengan similarity
          - explanation     : penjelasan proses untuk transparency
        """

        # --- RETRIEVE ---
        top_kasus = self.retrieve(target_gejala, kode_ikan, top_n)

        # --- REUSE ---
        hasil_reuse = self.reuse(top_kasus)

        # --- Bangun output ---
        output = {
            "diagnosis_utama": hasil_reuse,
            "top_kasus"      : [],
            "explanation"    : self._buat_explanation(target_gejala, top_kasus)
        }

        for item in top_kasus:
            c   = item["case"]
            sim = item["detail_sim"]
            output["top_kasus"].append({
                "kode_kasus"   : c.kode_kasus,
                "jenis_ikan"   : c.jenis_ikan,
                "kode_penyakit": c.kode_penyakit,
                "nama_penyakit": self.penyakit_info.get(c.kode_penyakit, c.kode_penyakit),
                "similarity"   : item["similarity"],
                "cf_pakar"     : c.cf_pakar,
                "komponen"     : {
                    "bobot"   : sim.get("komponen_bobot"),
                    "pakar"   : sim.get("komponen_pakar"),
                    "coverage": sim.get("komponen_coverage"),
                    "j_si_ti" : sim.get("j_si_ti"),
                    "j_ti"    : sim.get("j_ti"),
                }
            })

        return output

    # ----------------------------------------------------------
    # EXPLANATION FACILITY
    # ----------------------------------------------------------

    def _buat_explanation(self,
                          target_gejala: dict[str, float],
                          top_kasus: list[dict]) -> dict:
        """
        Menghasilkan penjelasan transparan tentang bagaimana
        sistem mencapai kesimpulannya (Explanation Facility).
        """
        if not top_kasus:
            return {
                "ringkasan": "Tidak ditemukan kasus yang cukup mirip dalam case base.",
                "detail"   : []
            }

        best        = top_kasus[0]
        best_case   = best["case"]
        best_detail = best["detail_sim"]

        gejala_cocok = [
            g for g in best_detail.get("detail_gejala", []) if g["cocok"]
        ]
        gejala_tidak_cocok = [
            g for g in best_detail.get("detail_gejala", []) if not g["cocok"]
        ]

        ringkasan = (
            f"Sistem menemukan kasus paling mirip adalah {best_case.kode_kasus} "
            f"(ikan: {best_case.jenis_ikan}, penyakit: "
            f"{self.penyakit_info.get(best_case.kode_penyakit, best_case.kode_penyakit)}) "
            f"dengan similarity score {best['similarity']:.4f}. "
            f"Dari {best_detail.get('j_ti', '?')} gejala target, "
            f"{best_detail.get('j_si_ti', '?')} gejala ditemukan pada kasus referensi."
        )

        return {
            "ringkasan"          : ringkasan,
            "gejala_target"      : list(target_gejala.keys()),
            "kasus_referensi"    : best_case.kode_kasus,
            "gejala_cocok"       : [g["nama_gejala"] for g in gejala_cocok],
            "gejala_tidak_cocok" : [g["nama_gejala"] for g in gejala_tidak_cocok],
            "rumus"              : {
                "Σ(f*w)"    : best_detail.get("sum_f_w"),
                "Σ(w)"      : best_detail.get("sum_w"),
                "P(S)"      : best_detail.get("komponen_pakar"),
                "J(Si,Ti)"  : best_detail.get("j_si_ti"),
                "J(Ti)"     : best_detail.get("j_ti"),
                "Sim(S,T)"  : best["similarity"]
            },
            "detail_tiap_kasus"  : [
                {
                    "kode_kasus" : item["case"].kode_kasus,
                    "similarity" : item["similarity"],
                    "penyakit"   : self.penyakit_info.get(
                        item["case"].kode_penyakit, item["case"].kode_penyakit
                    )
                }
                for item in top_kasus
            ]
        }


# ===========================================================
# BAGIAN 3: DEMO / TESTING
# ===========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  AquaCase Expert — CBR Engine Demo")
    print("=" * 60)

    # Inisialisasi CBR (pastikan file JSON ada di direktori yang sama)
    cbr = CaseBasedReasoning(
        path_case_base = "AquaCase_Knowledge_Base/case_base.json",
        path_penyakit  = "AquaCase_Knowledge_Base/penyakit.json",
        path_gejala    = "AquaCase_Knowledge_Base/gejala.json",
        path_solusi    = "AquaCase_Knowledge_Base/solusi.json",
        threshold      = 0.0
    )

    # ----------------------------------------------------------
    # Skenario 1: Ikan Nila dengan beberapa gejala
    # (mengikuti gaya input di rbr.py)
    # ----------------------------------------------------------
    print("\n--- SKENARIO 1: Ikan Nila ---")

    input_gejala = {
        "G01": 0.8,   # Nafsu makan menurun
        "G02": 0.7,   # Gerakan lemah
        "G05": 0.6,   # Luka di tubuh
    }
    kode_ikan_target = "J01"  # Nila

    hasil = cbr.diagnosis(
        kode_ikan     = kode_ikan_target,
        target_gejala = input_gejala,
        top_n         = 3
    )

    # Tampilkan diagnosis utama
    dx = hasil["diagnosis_utama"]
    if dx:
        print(f"\n[DIAGNOSIS UTAMA]")
        print(f"  Penyakit    : {dx['nama_penyakit']} ({dx['kode_penyakit']})")
        print(f"  Similarity  : {dx['similarity']:.4f} ({dx['similarity']*100:.2f}%)")
        print(f"  Kasus ref   : {dx['kode_kasus_ref']}")
        print(f"  Solusi      : {dx['solusi']}")
    else:
        print("[DIAGNOSIS] Tidak ditemukan kasus yang cocok.")

    # Tampilkan top kasus mirip
    print(f"\n[TOP {len(hasil['top_kasus'])} KASUS MIRIP]")
    for i, k in enumerate(hasil["top_kasus"], 1):
        print(f"  {i}. {k['kode_kasus']} | {k['nama_penyakit']:<35} | "
              f"sim={k['similarity']:.4f} | "
              f"cov={k['komponen']['coverage']:.2f} "
              f"({k['komponen']['j_si_ti']}/{k['komponen']['j_ti']} gejala cocok)")

    # Tampilkan explanation
    exp = hasil["explanation"]
    print(f"\n[EXPLANATION]")
    print(f"  {exp['ringkasan']}")
    print(f"\n  Rumus breakdown kasus terbaik:")
    r = exp["rumus"]
    print(f"    Σ(f*w) = {r['Σ(f*w)']}  |  Σ(w) = {r['Σ(w)']}")
    print(f"    P(S)   = {r['P(S)']}    |  J(Si,Ti)/J(Ti) = {r['J(Si,Ti)']}/{r['J(Ti)']}")
    print(f"    ➜ Sim(S,T) = {r['Sim(S,T)']:.6f}")

    print(f"\n  Gejala COCOK    : {exp['gejala_cocok']}")
    print(f"  Gejala TDK COCOK: {exp['gejala_tidak_cocok']}")

    # ----------------------------------------------------------
    # Skenario 2: Contoh Retain (simpan kasus baru)
    # ----------------------------------------------------------
    print("\n--- SKENARIO 2: RETAIN kasus baru ---")
    print("  (Kasus ini tidak benar-benar disimpan ke disk di demo ini.)")
    print("  Untuk menyimpan, panggil: cbr.retain(..., path_simpan='case_base.json')")

    # Simulasi retain tanpa menulis ke disk
    kode_baru = f"K{len(cbr.cases)+1:03d}"
    print(f"  → Kasus baru akan diberi kode: {kode_baru}")
    print(f"  → Total kasus setelah retain: {len(cbr.cases)+1}")

    print("\n" + "=" * 60)
    print("  Demo selesai!")
    print("=" * 60)