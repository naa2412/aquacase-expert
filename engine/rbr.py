"""
rbr.py — Rule-Based Reasoning (RBR) untuk AquaCase Expert
=========================================================
Implementasi Forward Chaining dengan Certainty Factor (CF).

ALUR INFERENSI:
  Untuk setiap rule:
    1. CF Komposit  = min(CF_user[G1], CF_user[G2], ...) — kondisi AND
    2. CF Rule      = CF_Komposit × CF_Pakar

  Untuk setiap penyakit yang memiliki lebih dari 1 rule aktif:
    3. CF Gabungan  = kombinasi_cf(CF_rule1, CF_rule2, ...)
       Rumus: CF(A,B) = CF(A) + CF(B)×(1 - CF(A))   [keduanya positif]
              CF(A,B) = CF(A) + CF(B)×(1 + CF(A))   [keduanya negatif]
              CF(A,B) = (CF(A)+CF(B)) / (1 - min(|CF(A)|, |CF(B)|))  [beda tanda]
"""

import json
import os
from typing import Optional


# ===========================================================
# BAGIAN 1: REPRESENTASI RULE
# ===========================================================

class Rule:
    """
    Representasi satu aturan (production rule) dalam Knowledge Base.

    Format rule: IF (G1 AND G2 AND ... AND Gn) THEN Penyakit [CF = cf_pakar]
    """

    def __init__(self, id_rule: str, gejala_list: list[str],
                 id_penyakit: str, cf_pakar: float):
        """
        Parameters
        ----------
        id_rule      : ID unik rule, misal 'R001'
        gejala_list  : list kode gejala sebagai premis (kondisi AND)
        id_penyakit  : kode penyakit sebagai konklusi
        cf_pakar     : nilai CF dari pakar untuk rule ini (0.0 – 1.0)
        """
        self.id_rule     = id_rule
        self.gejala_list = gejala_list
        self.id_penyakit = id_penyakit
        self.cf_pakar    = cf_pakar

    def __repr__(self):
        return (f"Rule({self.id_rule}, "
                f"premis={self.gejala_list}, "
                f"konklusi={self.id_penyakit}, "
                f"cf_pakar={self.cf_pakar})")


# ===========================================================
# BAGIAN 2: RULE-BASED REASONING ENGINE
# ===========================================================

class RuleBasedReasoning:
    """
    Engine RBR dengan Forward Chaining dan Certainty Factor.

    Forward Chaining: evaluasi setiap rule dari premis ke konklusi.
    CF mengukur keyakinan diagnosis — bukan probabilitas.
    """

    def __init__(self):
        self.rules:         list[Rule]       = []
        self.penyakit_info: dict[str, str]   = {}  # {kode: nama}
        self.gejala_info:   dict[str, str]   = {}  # {kode: nama}
        self.solusi_info:   dict[str, str]   = {}  # {kode_penyakit: solusi}

    # ----------------------------------------------------------
    # LOADER — baca Knowledge Base dari file JSON
    # ----------------------------------------------------------

    def load_knowledge_base(self, folder_path: str):
        """
        Memuat data penyakit, gejala, rule, dan solusi dari
        file-file JSON dalam satu folder.

        Struktur folder yang diharapkan:
          folder_path/
            penyakit.json  — [{kode_penyakit, nama_penyakit}, ...]
            gejala.json    — [{kode_gejala, nama_gejala}, ...]
            rules.json     — [{kode_rule, gejala, kode_penyakit, cf_pakar}, ...]
            solusi.json    — [{kode_penyakit, solusi}, ...]

        Parameters
        ----------
        folder_path : path ke folder berisi file-file JSON KB
        """
        self._load_penyakit(os.path.join(folder_path, "penyakit.json"))
        self._load_gejala(os.path.join(folder_path, "gejala.json"))
        self._load_rules(os.path.join(folder_path, "rules.json"))
        self._load_solusi(os.path.join(folder_path, "solusi.json"))

        print(f"[INFO] KB dimuat: {len(self.penyakit_info)} penyakit, "
              f"{len(self.gejala_info)} gejala, {len(self.rules)} rules")

    def _load_json(self, path: str) -> list | dict:
        if not os.path.exists(path):
            print(f"[PERINGATAN] File tidak ditemukan: {path}")
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_penyakit(self, path: str):
        for item in self._load_json(path):
            self.penyakit_info[item["kode_penyakit"]] = item["nama_penyakit"]

    def _load_gejala(self, path: str):
        for item in self._load_json(path):
            self.gejala_info[item["kode_gejala"]] = item["nama_gejala"]

    def _load_solusi(self, path: str):
        for item in self._load_json(path):
            kode = item.get("kode_penyakit", "")
            if kode:
                # solusi.json memiliki field 'pengobatan' dan 'pengendalian',
                # bukan field tunggal 'solusi'. Gabungkan keduanya.
                pengobatan = item.get("pengobatan", "")
                pengendalian = item.get("pengendalian", "")
                bagian = []
                if pengobatan:
                    bagian.append(f"Pengobatan: {pengobatan}")
                if pengendalian:
                    bagian.append(f"Pengendalian: {pengendalian}")
                self.solusi_info[kode] = "\n\n".join(bagian) if bagian else "Solusi belum tersedia."

    def _load_rules(self, path: str):
        self.rules = []
        for r in self._load_json(path):
            # Validasi CF pakar dalam rentang [0, 1]
            cf_pakar = float(r.get("cf_pakar", 0.0))
            cf_pakar = max(0.0, min(1.0, cf_pakar))

            self.rules.append(Rule(
                id_rule     = r["kode_rule"],
                gejala_list = r["gejala"],
                id_penyakit = r["kode_penyakit"],
                cf_pakar    = cf_pakar,
            ))

    # ----------------------------------------------------------
    # CERTAINTY FACTOR — operasi kombinasi
    # ----------------------------------------------------------

    @staticmethod
    def kombinasi_cf(cf1: float, cf2: float) -> float:
        """
        Menggabungkan dua nilai CF menggunakan rumus standar CF.

        Kasus 1 — keduanya positif:
          CF(A,B) = CF(A) + CF(B) × (1 - CF(A))

        Kasus 2 — keduanya negatif:
          CF(A,B) = CF(A) + CF(B) × (1 + CF(A))

        Kasus 3 — beda tanda:
          CF(A,B) = (CF(A) + CF(B)) / (1 - min(|CF(A)|, |CF(B)|))
          Guard: jika min(|CF|) == 1.0, kembalikan cf1 (hindari ZeroDivisionError)

        Digunakan saat ada beberapa rule yang menghasilkan penyakit
        yang sama — CF-nya digabungkan secara sequential.
        """
        if cf1 >= 0 and cf2 >= 0:
            return cf1 + cf2 * (1 - cf1)
        elif cf1 < 0 and cf2 < 0:
            return cf1 + cf2 * (1 + cf1)
        else:
            denom = 1 - min(abs(cf1), abs(cf2))
            if denom == 0:
                return cf1   # edge case: salah satu CF bernilai ±1
            return (cf1 + cf2) / denom

    @staticmethod
    def _validasi_cf_user(cf_val: float) -> float:
        """Pastikan nilai CF user dalam rentang [0.0, 1.0]."""
        return max(0.0, min(1.0, float(cf_val)))

    # ----------------------------------------------------------
    # DIAGNOSIS — Forward Chaining + CF
    # ----------------------------------------------------------

    def diagnosis(self,
                  input_user: dict[str, float],
                  threshold_cf: float = 0.0) -> dict:
        """
        Menjalankan inferensi RBR dengan Certainty Factor.

        Langkah-langkah:
          1. Evaluasi setiap rule:
             - Hitung CF Komposit = min(CF_user[G] untuk setiap G di premis)
             - Jika CF Komposit > 0: rule terpicu
             - Hitung CF Rule = CF_Komposit × CF_Pakar
          2. Gabungkan CF Rule untuk penyakit yang sama (kombinasi_cf sequential)
          3. Urutkan hasil dari CF terbesar, filter oleh threshold_cf

        Parameters
        ----------
        input_user   : {kode_gejala: cf_user} — gejala yang diamati user
                       CF user adalah keyakinan user terhadap gejala tersebut
                       Contoh: {'G01': 0.8, 'G05': 0.6}
        threshold_cf : hanya tampilkan penyakit dengan CF >= threshold (default 0)

        Returns
        -------
        dict berisi:
          - diagnosis         : list penyakit diurutkan CF tertinggi
          - rules_triggered   : list detail rule yang terpicu
          - diagnosis_utama   : penyakit dengan CF tertinggi (atau None)
          - explanation       : narasi ringkas untuk explanation facility
        """
        # Validasi dan normalisasi input CF user
        input_validated = {
            g: self._validasi_cf_user(v)
            for g, v in input_user.items()
        }

        hasil_sementara: dict[str, list[float]] = {}  # {kode_penyakit: [cf_rule, ...]}
        rules_triggered: list[dict]             = []

        # --- STEP 1: Evaluasi setiap rule ---
        for rule in self.rules:
            # Ambil CF user untuk setiap gejala premis
            # Gejala yang tidak ada di input → CF = 0.0 → rule tidak terpicu
            cf_user_list = [
                input_validated.get(g, 0.0)
                for g in rule.gejala_list
            ]

            # Kondisi AND: kekuatan premis = elemen terlemah
            cf_komposit = min(cf_user_list) if cf_user_list else 0.0

            # Rule terpicu jika semua premis terpenuhi (CF > 0)
            if cf_komposit <= 0:
                continue

            cf_rule = cf_komposit * rule.cf_pakar

            # Detail rule untuk explanation
            rules_triggered.append({
                "id_rule"      : rule.id_rule,
                "premis"       : [
                    {
                        "kode_gejala": g,
                        "nama_gejala": self.gejala_info.get(g, g),
                        "cf_user"    : input_validated.get(g, 0.0),
                    }
                    for g in rule.gejala_list
                ],
                "id_penyakit"  : rule.id_penyakit,
                "nama_penyakit": self.penyakit_info.get(rule.id_penyakit, rule.id_penyakit),
                "cf_komposit"  : round(cf_komposit, 4),
                "cf_pakar"     : rule.cf_pakar,
                "cf_rule"      : round(cf_rule, 4),
            })

            # Kumpulkan CF Rule per penyakit
            if rule.id_penyakit not in hasil_sementara:
                hasil_sementara[rule.id_penyakit] = []
            hasil_sementara[rule.id_penyakit].append(cf_rule)

        # --- STEP 2: Gabungkan CF Rule per penyakit ---
        hasil_akhir: list[dict] = []
        for kode_p, cf_list in hasil_sementara.items():
            cf_gabungan = cf_list[0]
            for cf in cf_list[1:]:
                cf_gabungan = self.kombinasi_cf(cf_gabungan, cf)

            # Clamp hasil akhir ke [0, 1] untuk keamanan
            cf_gabungan = max(0.0, min(1.0, cf_gabungan))

            if cf_gabungan < threshold_cf:
                continue

            # Hitung jumlah rule aktif untuk penyakit ini
            rules_untuk_penyakit = [
                r for r in rules_triggered if r["id_penyakit"] == kode_p
            ]

            hasil_akhir.append({
                "kode_penyakit" : kode_p,
                "nama_penyakit" : self.penyakit_info.get(kode_p, kode_p),
                "cf_akhir"      : round(cf_gabungan, 4),
                "persentase"    : round(cf_gabungan * 100, 2),
                "jumlah_rule"   : len(rules_untuk_penyakit),
                "solusi"        : self.solusi_info.get(kode_p, "Solusi belum tersedia."),
            })

        # --- STEP 3: Urutkan dari CF terbesar ---
        hasil_akhir.sort(key=lambda x: x["cf_akhir"], reverse=True)

        # Diagnosis utama (CF tertinggi)
        diagnosis_utama = hasil_akhir[0] if hasil_akhir else None

        return {
            "diagnosis"      : hasil_akhir,
            "rules_triggered": rules_triggered,
            "diagnosis_utama": diagnosis_utama,
            "explanation"    : self._buat_explanation(
                input_validated, rules_triggered, diagnosis_utama
            ),
        }

    # ----------------------------------------------------------
    # EXPLANATION FACILITY
    # ----------------------------------------------------------

    def _buat_explanation(self,
                          input_user       : dict[str, float],
                          rules_triggered  : list[dict],
                          diagnosis_utama  : Optional[dict]) -> dict:
        """
        Menghasilkan penjelasan transparan tentang bagaimana
        sistem mencapai kesimpulan (Explanation Facility).
        """
        if not diagnosis_utama:
            return {
                "ringkasan"   : "Tidak ada rule yang terpicu. "
                                "Pastikan gejala yang dimasukkan ada dalam knowledge base.",
                "rules_aktif" : [],
                "gejala_input": list(input_user.keys()),
            }

        kode_p   = diagnosis_utama["kode_penyakit"]
        nama_p   = diagnosis_utama["nama_penyakit"]
        cf_final = diagnosis_utama["cf_akhir"]
        n_rules  = diagnosis_utama["jumlah_rule"]

        # Rules aktif untuk penyakit utama
        rules_penyakit_utama = [
            r for r in rules_triggered if r["id_penyakit"] == kode_p
        ]

        ringkasan = (
            f"Sistem mendiagnosis {nama_p} ({kode_p}) "
            f"dengan CF akhir = {cf_final:.4f} ({cf_final*100:.2f}%). "
            f"Sebanyak {n_rules} rule terpicu untuk penyakit ini. "
            f"CF dihitung dari kombinasi sequential seluruh CF Rule."
        )

        return {
            "ringkasan"          : ringkasan,
            "gejala_input"       : [
                {
                    "kode"  : g,
                    "nama"  : self.gejala_info.get(g, g),
                    "cf_user": v,
                }
                for g, v in input_user.items()
            ],
            "rules_aktif_utama"  : rules_penyakit_utama,
            "total_rules_aktif"  : len(rules_triggered),
            "rumus"              : {
                "cf_komposit": "min(CF_user[G1], CF_user[G2], ...) — kondisi AND",
                "cf_rule"    : "CF_Komposit × CF_Pakar",
                "cf_gabungan": "CF(A,B) = CF(A) + CF(B) × (1 - CF(A))  [jika keduanya positif]",
            },
        }

    # ----------------------------------------------------------
    # UTILITY
    # ----------------------------------------------------------

    def get_rules_by_penyakit(self, kode_penyakit: str) -> list[Rule]:
        """Kembalikan semua rule untuk satu penyakit tertentu."""
        return [r for r in self.rules if r.id_penyakit == kode_penyakit]

    def get_gejala_by_penyakit(self, kode_penyakit: str) -> list[str]:
        """Kembalikan semua kode gejala unik yang terkait dengan satu penyakit."""
        gejala = set()
        for rule in self.get_rules_by_penyakit(kode_penyakit):
            gejala.update(rule.gejala_list)
        return sorted(gejala)


# ===========================================================
# BAGIAN 3: DEMO / TESTING
# ===========================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("  AquaCase Expert — RBR Engine Demo")
    print("=" * 60)

    rbr = RuleBasedReasoning()
    rbr.load_knowledge_base("data")

    # Input dari argumen command-line atau default testing
    if len(sys.argv) > 1:
        try:
            gejala_input_user = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Format input JSON tidak valid."}))
            sys.exit(1)
    else:
        # Default: skenario uji
        gejala_input_user = {
            "G01": 0.5,
            "G05": 0.7,
            "G06": 0.4,
            "G09": 0.3,
        }

    print(f"\nInput gejala: {gejala_input_user}")

    hasil = rbr.diagnosis(gejala_input_user)

    # Tampilkan diagnosis
    dx_utama = hasil["diagnosis_utama"]
    if dx_utama:
        print(f"\n[DIAGNOSIS UTAMA]")
        print(f"  Penyakit  : {dx_utama['nama_penyakit']} ({dx_utama['kode_penyakit']})")
        print(f"  CF Akhir  : {dx_utama['cf_akhir']:.4f} ({dx_utama['persentase']}%)")
        print(f"  Rule aktif: {dx_utama['jumlah_rule']} rule")
        print(f"  Solusi    : {dx_utama['solusi'][:80]}...")
    else:
        print("\n[DIAGNOSIS] Tidak ada rule yang terpicu.")

    # Tampilkan semua diagnosis
    print(f"\n[SEMUA KANDIDAT PENYAKIT]")
    for i, dx in enumerate(hasil["diagnosis"], 1):
        print(f"  {i}. [{dx['kode_penyakit']}] {dx['nama_penyakit']:<40} "
              f"CF={dx['cf_akhir']:.4f} ({dx['persentase']}%) "
              f"— {dx['jumlah_rule']} rule")

    # Tampilkan rules yang terpicu
    print(f"\n[RULES TERPICU — {len(hasil['rules_triggered'])} rule]")
    for r in hasil["rules_triggered"][:5]:  # tampilkan 5 pertama
        premis_str = ", ".join(g["kode_gejala"] for g in r["premis"])
        print(f"  {r['id_rule']} | IF [{premis_str}] → {r['id_penyakit']} "
              f"| CF_komposit={r['cf_komposit']} "
              f"× CF_pakar={r['cf_pakar']} "
              f"= CF_rule={r['cf_rule']}")
    if len(hasil["rules_triggered"]) > 5:
        print(f"  ... dan {len(hasil['rules_triggered'])-5} rule lainnya")

    # Tampilkan explanation
    exp = hasil["explanation"]
    print(f"\n[EXPLANATION]")
    print(f"  {exp['ringkasan']}")
    print(f"\n  Rumus yang digunakan:")
    for k, v in exp["rumus"].items():
        print(f"    {k}: {v}")

    # Output JSON ke stdout (untuk integrasi dengan backend/frontend)
    print(f"\n[JSON OUTPUT]")
    print(json.dumps(hasil, indent=2, ensure_ascii=False)[:500] + "...")