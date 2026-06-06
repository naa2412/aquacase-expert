# Perancangan Sistem Pakar Diagnosis Penyakit Ikan Air Tawar Menggunakan Hybrid Case-Based Reasoning dan Rule-Based Reasoning

## AquaCase Expert

AquaCase Expert adalah prototipe sistem pakar berbasis web untuk membantu proses diagnosis penyakit ikan air tawar. Sistem ini menggunakan pendekatan hybrid, yaitu menggabungkan Rule-Based Reasoning (RBR) dan Case-Based Reasoning (CBR) agar hasil diagnosis lebih informatif dan dapat dibandingkan dari sisi aturan maupun kasus terdahulu.

## Anggota Kelompok

1. Andra Kusnaedi Ilyaz - 24/537757/PA/22793
2. Azhar Maulana - 24/533487/PA/22582
3. Bobby Rahman Hartanto - 24/539383/PA/22903
4. Kukuh Agus Hermawan - 24/533395/PA/22573
5. Rayhan Haldi Hermawan - 24/545406/PA/23176

## Deskripsi Sistem

Sistem digunakan dengan cara memilih jenis ikan, memilih gejala yang diamati, dan mengisi tingkat keyakinan atau Certainty Factor (CF) pada setiap gejala. Setelah data dimasukkan, sistem akan menampilkan hasil diagnosis berupa kandidat penyakit, skor akhir, tingkat keyakinan, analisis RBR, analisis CBR, serta rekomendasi penanganan.

Demo sistem dapat diakses melalui:

```text
https://aquacase-expert-eosin.vercel.app
```

## Metode yang Digunakan

* **Rule-Based Reasoning (RBR)** digunakan untuk mencocokkan gejala pengguna dengan aturan pakar yang tersedia pada knowledge base.
* **Case-Based Reasoning (CBR)** digunakan untuk membandingkan gejala kasus baru dengan data kasus lama berdasarkan nilai similarity.
* **Hybrid Fusion** digunakan untuk menggabungkan skor CF RBR, similarity CBR, dan agreement score menjadi skor akhir diagnosis.

## Sumber Data

Knowledge base diadaptasi dari tesis Hisma Abduh tentang diagnosis penyakit ikan air tawar menggunakan Rule-Based Reasoning dan Case-Based Reasoning. Data penyakit ikan berasal dari Balai Pengembangan Teknologi Kelautan dan Perikanan Argomulyo, Yogyakarta.

## Cakupan Knowledge Base

Data yang digunakan dalam sistem mencakup:

* 9 jenis ikan air tawar
* 45 gejala penyakit
* 13 jenis penyakit ikan
* 142 data kasus CBR
* 30 data uji
* 458 rule RBR
* Solusi pengobatan dan pengendalian untuk setiap penyakit
