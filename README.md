# AquaCase Expert - Knowledge Base JSON

Folder ini berisi knowledge base hasil ekstraksi dari tesis Hisma Abduh tentang diagnosis penyakit ikan air tawar menggunakan Rule-Based Reasoning dan Case-Based Reasoning.

Isi folder:

* `README.md`: penjelasan isi folder dan catatan penting knowledge base.
* `knowledge_base.json`: semua data knowledge base dalam satu file gabungan.
* `metadata.json`: informasi ringkas tentang sumber data, jumlah data, dan struktur knowledge base.
* `ikan.json`: data 9 jenis ikan air tawar.
* `penyakit.json`: data 13 penyakit ikan.
* `gejala.json`: data 45 gejala penyakit ikan.
* `solusi.json`: data pengobatan dan penanganan untuk setiap penyakit.
* `gejala_penyakit.json`: relasi antara penyakit dan gejala yang berhubungan.
* `rules.json`: 458 rule untuk Rule-Based Reasoning (RBR).
* `rule_gejala.json`: detail gejala yang membentuk setiap rule RBR.
* `case_base.json`: 142 data kasus untuk Case-Based Reasoning (CBR) dari Lampiran A.
* `case_gejala.json`: detail gejala pada setiap kasus CBR.
* `data_uji.json`: 30 data uji dari paper.
* `validation_report.json`: laporan validasi jumlah data dan kelengkapan struktur JSON.
* `load_kb.py`: script untuk memastikan semua JSON bisa dibaca dan dirun di Python.

Catatan penting:

1. Paper/tesis berisi 458 jumlah aturan yaitu dari R001 sampai R458.
2. Pada paper terdapat kode gejala hasil ekstraksi yang tampak tidak konsisten dengan nama gejala. Untuk membuat data runnable, kolom `gejala` dinormalisasi dari nama gejala ke master `gejala.json`. Kode hasil ekstraksi tetap disimpan di `raw_condition_codes`.
3. Semua `cf_pakar` rule dibuat 0.9 karena contoh perhitungan RBR pada tesis menggunakan CF Rule 0.9 untuk rule yang aktif, dan case base juga menggunakan keyakinan pakar 0.9.
