import json
import os
import sys

class Rule:
    def __init__(self, id_rule, gejala_list, id_penyakit, cf_pakar):
        """
        Representasi sebuah Aturan (Rule) dalam Knowledge Base.
        id_rule     : String ID Rule (misal: 'R001')
        gejala_list : List dari ID Gejala yang merupakan premis (syarat) dengan kondisi AND
        id_penyakit : String ID Penyakit yang menjadi konklusi
        cf_pakar    : Float Nilai Certainty Factor dari pakar untuk rule ini
        """
        self.id_rule = id_rule
        self.gejala_list = gejala_list
        self.id_penyakit = id_penyakit
        self.cf_pakar = cf_pakar

class RuleBasedReasoning:
    def __init__(self):
        self.rules = []
        self.penyakit_info = {}
        self.gejala_info = {}

    def load_knowledge_base(self, folder_path):
        """ Memuat data penyakit, gejala, dan rule dari file-file JSON dalam folder AquaCase_Knowledge_Base """
        penyakit_file = os.path.join(folder_path, 'penyakit.json')
        gejala_file = os.path.join(folder_path, 'gejala.json')
        rules_file = os.path.join(folder_path, 'rules.json')

        # Load Penyakit
        if os.path.exists(penyakit_file):
            with open(penyakit_file, 'r', encoding='utf-8') as f:
                data_penyakit = json.load(f)
                for p in data_penyakit:
                    self.penyakit_info[p['kode_penyakit']] = p['nama_penyakit']

        # Load Gejala
        if os.path.exists(gejala_file):
            with open(gejala_file, 'r', encoding='utf-8') as f:
                data_gejala = json.load(f)
                for g in data_gejala:
                    self.gejala_info[g['kode_gejala']] = g['nama_gejala']

        # Load Rules
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                data_rules = json.load(f)
                for r in data_rules:
                    self.rules.append(Rule(
                        id_rule=r['kode_rule'],
                        gejala_list=r['gejala'],
                        id_penyakit=r['kode_penyakit'],
                        cf_pakar=float(r['cf_pakar'])
                    ))

    def kombinasi_cf(self, cf1, cf2):
        """ 
        Menggabungkan 2 nilai CF menggunakan rumus Certainty Factor.
        Digunakan apabila ada lebih dari 1 rule yang menghasilkan kesimpulan (penyakit) yang sama.
        """
        if cf1 >= 0 and cf2 >= 0:
            return cf1 + cf2 * (1 - cf1)
        elif cf1 < 0 and cf2 < 0:
            return cf1 + cf2 * (1 + cf1)
        else:
            return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2)))

    def diagnosis(self, input_user):
        """
        Menjalankan inferensi RBR dengan Certainty Factor.
        Proses sesuai dengan metode:
        1. Hitung CF Komposit = Min(CF_Gejala1, CF_Gejala2, ...)
        2. Hitung CF Rule = CF Komposit * CF Pakar
        3. Hitung CF Gabungan jika ada beberapa rule untuk 1 penyakit.

        input_user: dict berisi { 'id_gejala': nilai_cf_user }
                    misal: {'G01': 0.5, 'G05': 0.7}
        """
        hasil_sementara = {}  # Format: {id_penyakit: [cf_rule1, cf_rule2, ...]}
        rules_triggered = []

        # 1. Evaluasi setiap rule (Menghitung CF Komposit & CF Rule)
        for rule in self.rules:
            cf_user_list = [input_user.get(g, 0.0) for g in rule.gejala_list]
            
            # Kondisi AND: CF Komposit adalah nilai minimum dari semua premis (gejala)
            cf_komposit = min(cf_user_list) if cf_user_list else 0.0
            
            # Rule terpicu jika CF komposit > 0
            if cf_komposit > 0:
                cf_rule = cf_komposit * rule.cf_pakar
                rules_triggered.append({
                    'id_rule': rule.id_rule,
                    'premis': rule.gejala_list,
                    'id_penyakit': rule.id_penyakit,
                    'cf_komposit': cf_komposit,
                    'cf_pakar': rule.cf_pakar,
                    'cf_rule': cf_rule
                })
                
                # Simpan nilai CF Rule untuk dihitung gabungannya nanti
                if rule.id_penyakit not in hasil_sementara:
                    hasil_sementara[rule.id_penyakit] = []
                hasil_sementara[rule.id_penyakit].append(cf_rule)

        # 2. Menghitung CF Gabungan untuk penyakit yang sama
        hasil_akhir = []
        for id_penyakit, cf_list in hasil_sementara.items():
            if not cf_list:
                continue
            
            # Gabungkan jika ada lebih dari 1 CF
            cf_gabungan = cf_list[0]
            for cf in cf_list[1:]:
                cf_gabungan = self.kombinasi_cf(cf_gabungan, cf)
                
            hasil_akhir.append({
                'id_penyakit': id_penyakit,
                'nama_penyakit': self.penyakit_info.get(id_penyakit, f"Penyakit {id_penyakit}"),
                'cf_akhir': cf_gabungan,
                'persentase': round(cf_gabungan * 100, 2)
            })

        # Urutkan berdasarkan CF terbesar
        hasil_akhir = sorted(hasil_akhir, key=lambda x: x['cf_akhir'], reverse=True)
        
        return {
            'diagnosis': hasil_akhir,
            'rules_triggered': rules_triggered
        }

# ==========================================
# Contoh Penggunaan / Testing
# ==========================================
if __name__ == "__main__":
    rbr = RuleBasedReasoning()
    
    # 1. Memuat Knowledge Base dari folder JSON temanmu
    kb_folder = 'AquaCase_Knowledge_Base'
    rbr.load_knowledge_base(kb_folder)

    # 2. Menerima Input dari Pengguna
    # Jika program dijalankan dari terminal/backend dan diberi argumen JSON
    if len(sys.argv) > 1:
        try:
            gejala_input_user = json.loads(sys.argv[1])
        except json.JSONDecodeError:
            print(json.dumps({"error": "Format input JSON tidak valid."}))
            sys.exit(1)
    else:
        # Default testing sesuai data Tabel 6.3 di Tesis
        gejala_input_user = {
            'G01': 0.5,
            'G05': 0.7,
            'G06': 0.4,
            'G09': 0.3
        }

    # 3. Proses Inferensi (Diagnosis)
    hasil = rbr.diagnosis(gejala_input_user)

    # 4. Tampilkan Hasil
    # Format output berupa JSON string agar mudah dibaca oleh Front-End / Backend lain
    print(json.dumps(hasil, indent=4))
