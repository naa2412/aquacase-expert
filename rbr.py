import json

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

    def tambah_penyakit(self, id_penyakit, nama_penyakit):
        """ Menambahkan referensi data penyakit """
        self.penyakit_info[id_penyakit] = nama_penyakit

    def tambah_gejala(self, id_gejala, nama_gejala):
        """ Menambahkan referensi data gejala """
        self.gejala_info[id_gejala] = nama_gejala

    def tambah_rule(self, id_rule, gejala_list, id_penyakit, cf_pakar):
        """ Menambahkan rule ke dalam Knowledge Base """
        rule = Rule(id_rule, gejala_list, id_penyakit, cf_pakar)
        self.rules.append(rule)

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
            # Mengambil nilai CF user untuk setiap gejala di rule
            # Jika user tidak menginputkan gejala tersebut, defaultnya 0.0
            cf_user_list = [input_user.get(g, 0.0) for g in rule.gejala_list]
            
            # Kondisi AND: CF Komposit adalah nilai minimum dari semua premis (gejala)
            cf_komposit = min(cf_user_list) if cf_user_list else 0.0
            
            # Rule terpicu jika CF komposit > 0 (berarti semua gejala dalam rule terpenuhi)
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
# Contoh Penggunaan / Testing (Sesuai Data di PDF)
# ==========================================
if __name__ == "__main__":
    rbr = RuleBasedReasoning()
    
    # --- 1. Membangun Referensi Penyakit ---
    rbr.tambah_penyakit('P01', 'Motile Aeromonas Septicemia (MAS)')
    rbr.tambah_penyakit('P02', 'Pseudomonas septicemia')
    rbr.tambah_penyakit('P03', 'Streptococciosis')
    rbr.tambah_penyakit('P04', 'Vibrios')
    rbr.tambah_penyakit('P05', 'Bintik Putih (White Spot)')
    rbr.tambah_penyakit('P06', 'Trichodiniasis (Gatal)')
    rbr.tambah_penyakit('P07', 'Gyrodactylosis')
    rbr.tambah_penyakit('P08', 'Dactylogyrosis')
    rbr.tambah_penyakit('P09', 'Koi Herpes Virus (KHV)')
    rbr.tambah_penyakit('P10', 'White Spot Syndrome (WSS)')
    rbr.tambah_penyakit('P11', 'IHHNV')
    rbr.tambah_penyakit('P12', 'Saprolegniasis')
    rbr.tambah_penyakit('P13', 'Mycosis')
    
    # --- 2. Membangun Knowledge Base (Rules) ---
    # Contoh data rule dari pengujian Bab 6.4
    rbr.tambah_rule('R003', ['G06', 'G05'], 'P01', 0.9)
    rbr.tambah_rule('R006', ['G01', 'G05'], 'P01', 0.9)
    rbr.tambah_rule('R007', ['G06', 'G01'], 'P01', 0.9)
    rbr.tambah_rule('R028', ['G01', 'G05', 'G06'], 'P01', 0.9)
    rbr.tambah_rule('R150', ['G20', 'G21'], 'P05', 0.9)

    # --- 3. Input dari Pengguna ---
    # Sesuai contoh pada Tabel 6.3
    gejala_input_user = {
        'G01': 0.5,
        'G05': 0.7,
        'G06': 0.4,
        'G09': 0.3
    }

    # --- 4. Proses Inferensi (Diagnosis) ---
    hasil = rbr.diagnosis(gejala_input_user)

    # --- 5. Tampilkan Hasil ---
    print("=== Hasil Diagnosis RBR-CF (AquaCase Expert) ===")
    print("\n[+] Rules yang terpicu:")
    for rt in hasil['rules_triggered']:
        print(f" - {rt['id_rule']}: Premis={rt['premis']} -> {rt['id_penyakit']} "
              f"| CF Komposit={rt['cf_komposit']:.2f}, CF Pakar={rt['cf_pakar']}, CF Rule={rt['cf_rule']:.3f}")
    
    print("\n[+] Diagnosis Akhir (CF Gabungan):")
    for res in hasil['diagnosis']:
        print(f"Penyakit: {res['nama_penyakit']} ({res['id_penyakit']})")
        print(f"Nilai CF Akhir: {res['cf_akhir']:.4f} ({res['persentase']}%)")
        print("-" * 50)
