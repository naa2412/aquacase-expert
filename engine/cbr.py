"""
cbr.py — Case-Based Reasoning (CBR) untuk AquaCase Expert
Implementasi siklus 4R (Retrieve, Reuse, Revise, Retain)
menggunakan NN Similarity (Mancasari, 2012).

RUMUS (Mancasari, 2012):
    Sim(S,T) = [Σ f(Si,Ti)·wi / Σ wi] × P(S)

    Di mana:
    - f(Si,Ti) = 1 jika gejala ke-i dari SOURCE ada di TARGET, 0 jika tidak
    - wi       = bobot gejala ke-i di SOURCE case
    - P(S)     = cf_pakar dari source case (keyakinan pakar)
    - Kasus dengan jenis ikan berbeda langsung similarity = 0
"""

import json
import os
from pathlib import Path
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
        kode_kasus    : str   - ID unik kasus, misal 'K001'
        kode_penyakit : str   - ID penyakit hasil diagnosis, misal 'P01'
        kode_ikan     : str   - ID jenis ikan, misal 'J01'
        jenis_ikan    : str   - Nama jenis ikan, misal 'Nila'
        cf_pakar      : float - Keyakinan pakar atas kasus ini — P(S) dalam rumus
        gejala        : list  - [{'kode_gejala': str, 'bobot': float}, ...]
        """
        self.kode_kasus    = kode_kasus
        self.kode_penyakit = kode_penyakit
        self.kode_ikan     = kode_ikan
        self.jenis_ikan    = jenis_ikan
        self.cf_pakar      = cf_pakar
        # Konversi ke dict untuk akses O(1): {kode_gejala: bobot}
        self.gejala: dict[str, float] = {
            g["kode_gejala"]: g["bobot"] for g in gejala
        }

    def __repr__(self):
        return (f"Case({self.kode_kasus}, ikan={self.jenis_ikan}, "
                f"penyakit={self.kode_penyakit}, "
                f"n_gejala={len(self.gejala)})")


# ===========================================================
# BAGIAN 2: CASE-BASED REASONING ENGINE
# ===========================================================

class CaseBasedReasoning:
    """
    Engine CBR dengan siklus 4R:
      Retrieve → hitung similarity semua kasus, ambil top-N
      Reuse    → pakai diagnosis dari kasus paling mirip (+ vote tally)
      Revise   → koreksi hasil jika pakar mengoreksi
      Retain   → simpan kasus baru ke case base dengan cek duplikat
    """

    def __init__(self,
                 path_case_base : str   = "data/case_base.json",
                 path_penyakit  : str   = "data/penyakit.json",
                 path_gejala    : str   = "data/gejala.json",
                 path_solusi    : str   = "data/solusi.json",
                 threshold      : float = 0.0):
        """
        Parameters
        ----------
        path_case_base : Path ke case_base.json
        path_penyakit  : Path ke penyakit.json
        path_gejala    : Path ke gejala.json
        path_solusi    : Path ke solusi.json
        threshold      : Hanya pertimbangkan kasus dengan similarity >= threshold
        """
        self.threshold          = threshold
        self.path_case_base     = path_case_base   # simpan untuk retain()
        self.cases: list[Case]  = []
        self.penyakit_info: dict[str, str] = {}    # {kode_penyakit: nama}
        self.gejala_info:   dict[str, str] = {}    # {kode_gejala: nama}
        self.solusi_info:   dict[str, str] = {}    # {kode_penyakit: solusi}

        self._load_penyakit(path_penyakit)
        self._load_gejala(path_gejala)
        self._load_solusi(path_solusi)
        self._load_case_base(path_case_base)

    # ----------------------------------------------------------
    # LOADER 
    # ----------------------------------------------------------

    def _load_json(self, path: str) -> list | dict:
        if not os.path.exists(path):
            print(f"[PERINGATAN] File tidak ditemukan: {path}")
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
                           target_kode_ikan: Optional[str]) -> dict:
        """
        Menghitung similarity antara source case (S) dan target query (T).

        Rumus NN Similarity (Mancasari, 2012):
            Sim(S,T) = [Σ f(Si,Ti)·wi / Σ wi] × P(S)

        Keterangan variabel:
            f(Si,Ti) = 1 jika gejala source ke-i ADA di target query, 0 jika tidak
            wi       = bobot gejala ke-i di source case
            P(S)     = cf_pakar dari source case
            Σ        = penjumlahan atas SEMUA gejala di source case

        Parameters
        ----------
        source           : Case yang dibandingkan (dari case base)
        target_gejala    : {kode_gejala: cf_user} — input dari pengguna
        target_kode_ikan : kode ikan target, atau None untuk semua jenis ikan

        Returns
        -------
        dict berisi similarity dan komponen breakdown untuk explanation
        """
        # Filter jenis ikan — jika target_kode_ikan None, lewati filter ini
        if target_kode_ikan is not None and source.kode_ikan != target_kode_ikan:
            return {
                "similarity"          : 0.0,
                "terlewat_karena_ikan": True,
                "penjelasan"          : f"Jenis ikan berbeda: {source.jenis_ikan}"
            }

        gejala_target = set(target_gejala.keys())
        gejala_source = set(source.gejala.keys())

        # Iterasi atas semua gejala SOURCE
        sum_fw   = 0.0   # Σ f(Si,Ti)·wi
        sum_w    = 0.0   # Σ wi
        detail_gejala = []

        for kode_g, bobot_s in source.gejala.items():
            f = 1.0 if kode_g in gejala_target else 0.0
            sum_fw += f * bobot_s
            sum_w  += bobot_s
            detail_gejala.append({
                "kode_gejala" : kode_g,
                "nama_gejala" : self.gejala_info.get(kode_g, kode_g),
                "bobot_source": bobot_s,
                "cocok"       : bool(f)
            })

        if sum_w == 0:
            return {"similarity": 0.0, "penjelasan": "Bobot source kosong."}

        # Komponen similarity
        komponen_bobot = sum_fw / sum_w      # Σf·w / Σw
        komponen_pakar = source.cf_pakar     # P(S)
        similarity     = komponen_bobot * komponen_pakar

        # Informasi tambahan (untuk explanation, bukan untuk kalkulasi)
        gejala_cocok     = gejala_target & gejala_source
        gejala_tidak     = gejala_target - gejala_source
        j_si_ti          = len(gejala_cocok)   # gejala target yang ada di source
        j_ti             = len(gejala_target)  # total gejala target

        return {
            "similarity"          : round(similarity, 6),
            "komponen_bobot"      : round(komponen_bobot, 4),
            "komponen_pakar"      : komponen_pakar,
            "sum_fw"              : round(sum_fw, 4),
            "sum_w"               : round(sum_w, 4),
            "j_si_ti"             : j_si_ti,
            "j_ti"                : j_ti,
            "coverage_info"       : f"{j_si_ti}/{j_ti} gejala target ditemukan di source",
            "detail_gejala"       : detail_gejala,
            "terlewat_karena_ikan": False
        }

    def retrieve(self,
                 target_gejala    : dict[str, float],
                 target_kode_ikan : Optional[str] = None,
                 top_n            : int = 5) -> list[dict]:
        """
        Langkah RETRIEVE: hitung similarity semua kasus, kembalikan top-N.

        Parameters
        ----------
        target_gejala    : {kode_gejala: cf_user} — input dari pengguna
        target_kode_ikan : kode ikan target (None = tidak filter jenis ikan)
        top_n            : jumlah kasus teratas yang dikembalikan

        Returns
        -------
        List of dict diurutkan dari similarity tertinggi, berisi:
          - case       : objek Case
          - similarity : nilai similarity
          - detail_sim : breakdown komponen (untuk explanation facility)
        """
        hasil = []

        for case in self.cases:
            detail = self._hitung_similarity(case, target_gejala, target_kode_ikan)
            sim    = detail.get("similarity", 0.0)

            # Skip kasus dengan jenis ikan berbeda atau di bawah threshold
            if detail.get("terlewat_karena_ikan", False):
                continue
            if sim < self.threshold:
                continue

            hasil.append({
                "case"      : case,
                "similarity": sim,
                "detail_sim": detail
            })

        # Urutkan dari similarity terbesar
        hasil.sort(key=lambda x: x["similarity"], reverse=True)
        return hasil[:top_n]

    # ----------------------------------------------------------
    # REUSE — Ambil diagnosis dari top-N dengan vote tally
    # ----------------------------------------------------------

    def reuse(self, retrieved_cases: list[dict]) -> Optional[dict]:
        """
        Langkah REUSE: tentukan diagnosis dari top-N kasus.

        Strategi: vote tally berbobot similarity.
        Setiap kasus memberikan 'suara' sebesar similarity-nya
        untuk penyakit yang didiagnosisnya. Penyakit dengan total
        suara terbesar menang — lebih robust daripada sekadar ambil #1.

        Jika top-1 dan pemenang vote tally berbeda, keduanya dicatat
        untuk dipertimbangkan dalam conflict handling di hybrid fusion.

        Returns None jika tidak ada kasus ditemukan.
        """
        if not retrieved_cases:
            return None

        # Vote tally: {kode_penyakit: total_similarity}
        vote: dict[str, float] = {}
        for item in retrieved_cases:
            kode = item["case"].kode_penyakit
            vote[kode] = vote.get(kode, 0.0) + item["similarity"]

        # Pemenang vote
        kode_pemenang = max(vote, key=vote.get)

        # Kasus dengan similarity tertinggi (untuk referensi)
        best = retrieved_cases[0]
        best_case = best["case"]

        return {
            "kode_penyakit"   : kode_pemenang,
            "nama_penyakit"   : self.penyakit_info.get(kode_pemenang, kode_pemenang),
            "similarity_best" : best["similarity"],
            "vote_tally"      : vote,
            "kode_kasus_ref"  : best_case.kode_kasus,
            "solusi"          : self.solusi_info.get(kode_pemenang, "Solusi belum tersedia."),
            "cf_pakar"        : best_case.cf_pakar,
            # Flag konflik jika top-1 dan vote-winner berbeda
            "ada_konflik_vote": best_case.kode_penyakit != kode_pemenang,
            "kode_penyakit_top1": best_case.kode_penyakit
        }

    # ----------------------------------------------------------
    # REVISE — Koreksi diagnosis oleh pakar
    # ----------------------------------------------------------

    def revise(self,
               hasil_reuse     : dict,
               koreksi_penyakit: Optional[str] = None,
               koreksi_solusi  : Optional[str] = None) -> dict:
        """
        Langkah REVISE: koreksi hasil diagnosis jika pakar tahu
        diagnosis otomatis salah.

        Parameters
        ----------
        hasil_reuse        : dict hasil dari reuse()
        koreksi_penyakit   : kode penyakit yang benar (opsional)
        koreksi_solusi     : teks solusi yang benar (opsional)

        Returns
        -------
        dict hasil diagnosis yang sudah direvisi, dengan flag 'direvisi'
        """
        hasil = hasil_reuse.copy()
        hasil["direvisi"] = False

        if koreksi_penyakit and koreksi_penyakit != hasil["kode_penyakit"]:
            print(f"[REVISE] Penyakit: {hasil['kode_penyakit']} → {koreksi_penyakit}")
            hasil["kode_penyakit"] = koreksi_penyakit
            hasil["nama_penyakit"] = self.penyakit_info.get(
                koreksi_penyakit, koreksi_penyakit
            )
            hasil["direvisi"] = True

        if koreksi_solusi:
            print("[REVISE] Solusi diperbarui oleh pakar.")
            hasil["solusi"]   = koreksi_solusi
            hasil["direvisi"] = True

        return hasil

    # ----------------------------------------------------------
    # RETAIN — Simpan kasus baru ke case base
    # ----------------------------------------------------------

    def retain(self,
               kode_ikan     : str,
               jenis_ikan    : str,
               target_gejala : dict[str, float],
               kode_penyakit : str,
               cf_pakar      : float = 0.9,
               threshold_duplikat: float = 0.95) -> tuple[bool, str]:
        """
        Langkah RETAIN: tambahkan kasus baru ke case base jika belum
        ada kasus yang terlalu mirip (smart retain policy).

        Smart retain policy:
            Jika similarity kasus baru dengan kasus existing >= threshold_duplikat,
            kasus dianggap duplikat dan TIDAK disimpan.
            Ini mencegah case base membengkak dengan kasus redundan.

        Parameters
        ----------
        kode_ikan           : kode jenis ikan, misal 'J01'
        jenis_ikan          : nama jenis ikan, misal 'Nila'
        target_gejala       : {kode_gejala: cf_user} — input pengguna
        kode_penyakit       : diagnosis final (setelah revisi jika ada)
        cf_pakar            : tingkat keyakinan pakar (default 0.9)
        threshold_duplikat  : batas similarity untuk mendeteksi duplikat

        Returns
        -------
        (True, kode_kasus)   jika berhasil disimpan
        (False, alasan)      jika ditolak karena duplikat
        """
        # Cek duplikat: retrieve top-1 dan cek similarity-nya
        top1 = self.retrieve(
            target_gejala    = target_gejala,
            target_kode_ikan = kode_ikan,
            top_n            = 1
        )
        if top1 and top1[0]["similarity"] >= threshold_duplikat:
            kasus_mirip = top1[0]["case"].kode_kasus
            sim_val     = top1[0]["similarity"]
            alasan = (
                f"Kasus terlalu mirip dengan {kasus_mirip} "
                f"(similarity={sim_val:.3f} >= {threshold_duplikat}). "
                f"Tidak disimpan untuk menghindari duplikasi."
            )
            print(f"[RETAIN] Ditolak — {alasan}")
            return False, alasan

        # Generate kode kasus baru yang unik
        kode_existing = {c.kode_kasus for c in self.cases}
        counter       = len(self.cases) + 1
        kode_baru     = f"K{counter:03d}"
        while kode_baru in kode_existing:
            counter  += 1
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
        print(f"[RETAIN] Kasus baru ditambahkan: {kode_baru}")

        # Simpan ke file JSON (path sama dengan yang diload)
        self._simpan_case_base(self.path_case_base)

        return True, kode_baru

    def _simpan_case_base(self, path: str):
        """Tulis ulang seluruh case base ke file JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
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
                  kode_ikan    : Optional[str],
                  target_gejala: dict[str, float],
                  top_n        : int = 5) -> dict:
        """
        Menjalankan siklus CBR lengkap (Retrieve + Reuse).
        Revise dan Retain dipanggil terpisah jika diperlukan.

        Parameters
        ----------
        kode_ikan      : kode jenis ikan target, atau None untuk semua jenis
        target_gejala  : {kode_gejala: cf_user} — gejala yang diamati
        top_n          : jumlah kasus referensi teratas yang ditampilkan

        Returns
        -------
        dict berisi:
          - diagnosis_utama : hasil reuse (penyakit, similarity, solusi)
          - top_kasus       : top-N kasus beserta komponen similarity
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
                    "sum_fw"  : sim.get("sum_fw"),
                    "sum_w"   : sim.get("sum_w"),
                    "bobot"   : sim.get("komponen_bobot"),
                    "pakar"   : sim.get("komponen_pakar"),
                    "coverage": sim.get("coverage_info"),
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
                          top_kasus    : list[dict]) -> dict:
        """
        Menghasilkan penjelasan transparan tentang bagaimana
        sistem mencapai kesimpulannya (Explanation Facility).
        Menampilkan breakdown rumus Sim(S,T) = [Σf·w / Σw] × P(S).
        """
        if not top_kasus:
            return {
                "ringkasan": "Tidak ditemukan kasus yang cukup mirip dalam case base.",
                "detail"   : []
            }

        best        = top_kasus[0]
        best_case   = best["case"]
        best_detail = best["detail_sim"]

        gejala_cocok      = [g for g in best_detail.get("detail_gejala", []) if g["cocok"]]
        gejala_tidak_cocok = [g for g in best_detail.get("detail_gejala", []) if not g["cocok"]]

        nama_penyakit_best = self.penyakit_info.get(
            best_case.kode_penyakit, best_case.kode_penyakit
        )

        ringkasan = (
            f"Kasus paling mirip: {best_case.kode_kasus} "
            f"(ikan: {best_case.jenis_ikan}, "
            f"penyakit: {nama_penyakit_best}) "
            f"dengan similarity {best['similarity']:.4f}. "
            f"{best_detail.get('coverage_info', '')}."
        )

        return {
            "ringkasan"     : ringkasan,
            "gejala_target" : list(target_gejala.keys()),
            "kasus_referensi": best_case.kode_kasus,
            "gejala_cocok"  : [g["nama_gejala"] for g in gejala_cocok],
            "gejala_tidak_cocok": [g["nama_gejala"] for g in gejala_tidak_cocok],
            "rumus"         : {
                "Σ(f·w)"   : best_detail.get("sum_fw"),
                "Σ(w)"     : best_detail.get("sum_w"),
                "P(S)"     : best_detail.get("komponen_pakar"),
                "Σ(f·w)/Σ(w)": best_detail.get("komponen_bobot"),
                "Sim(S,T)" : best["similarity"],
                "formula"  : "Sim(S,T) = [Σ f(Si,Ti)·wi / Σ wi] × P(S)"
            },
            "detail_tiap_kasus": [
                {
                    "kode_kasus": item["case"].kode_kasus,
                    "similarity": item["similarity"],
                    "penyakit"  : self.penyakit_info.get(
                        item["case"].kode_penyakit,
                        item["case"].kode_penyakit
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

    cbr = CaseBasedReasoning(
        path_case_base = "data/case_base.json",
        path_penyakit  = "data/penyakit.json",
        path_gejala    = "data/gejala.json",
        path_solusi    = "data/solusi.json",
        threshold      = 0.0
    )

    # --- Skenario 1: Diagnosis ---
    print("\n--- SKENARIO 1: Diagnosis Ikan Nila ---")

    input_gejala     = {"G01": 0.8, "G02": 0.7, "G05": 0.6}
    kode_ikan_target = "J01"  # Nila

    hasil = cbr.diagnosis(
        kode_ikan     = kode_ikan_target,
        target_gejala = input_gejala,
        top_n         = 3
    )

    dx = hasil["diagnosis_utama"]
    if dx:
        print(f"\n[DIAGNOSIS UTAMA]")
        print(f"  Penyakit    : {dx['nama_penyakit']} ({dx['kode_penyakit']})")
        print(f"  Similarity  : {dx['similarity_best']:.4f}")
        print(f"  Kasus ref   : {dx['kode_kasus_ref']}")
        print(f"  Vote tally  : {dx['vote_tally']}")
        if dx.get("ada_konflik_vote"):
            print(f"  [!] Konflik: top-1={dx['kode_penyakit_top1']} vs "
                  f"vote-winner={dx['kode_penyakit']}")
    else:
        print("[DIAGNOSIS] Tidak ditemukan kasus yang cocok.")

    print(f"\n[TOP KASUS]")
    for i, k in enumerate(hasil["top_kasus"], 1):
        print(f"  {i}. {k['kode_kasus']} | {k['nama_penyakit']:<35} | "
              f"sim={k['similarity']:.4f} | "
              f"{k['komponen']['coverage']}")

    exp = hasil["explanation"]
    print(f"\n[EXPLANATION]")
    print(f"  {exp['ringkasan']}")
    r = exp["rumus"]
    print(f"\n  Formula: {r['formula']}")
    print(f"  Σ(f·w) = {r['Σ(f·w)']} | Σ(w) = {r['Σ(w)']}")
    print(f"  Σ(f·w)/Σ(w) = {r['Σ(f·w)/Σ(w)']} | P(S) = {r['P(S)']}")
    print(f"  → Sim(S,T) = {r['Sim(S,T)']:.6f}")
    print(f"\n  Gejala COCOK     : {exp['gejala_cocok']}")
    print(f"  Gejala TDK COCOK : {exp['gejala_tidak_cocok']}")

    # --- Skenario 2: Retain ---
    print("\n--- SKENARIO 2: Retain kasus baru ---")
    ok, pesan = cbr.retain(
        kode_ikan     = "J01",
        jenis_ikan    = "Nila",
        target_gejala = input_gejala,
        kode_penyakit = dx["kode_penyakit"] if dx else "P01",
        cf_pakar      = 0.9,
        threshold_duplikat = 0.95
    )
    print(f"  Retain: {'Berhasil' if ok else 'Ditolak'} — {pesan}")
    print(f"  Total kasus sekarang: {len(cbr.cases)}")

    print("\n" + "=" * 60)
    print("  Demo selesai!")
    print("=" * 60)
