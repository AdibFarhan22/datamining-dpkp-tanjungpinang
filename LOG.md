# LOG PROYEK (kronologis, jujur, apa adanya)

## 2026-11-17
- Audit awal `_chat.txt`: 9.671 pesan, Apr 2025 s/d Sep 2026. Desain disetujui tim (docs/superpowers/specs).
- Dependensi dipasang: scikit-learn, matplotlib, pytest, py7zr (7z biner tidak tersedia; pakai py7zr).

### Tahap 1 Ekstraksi (scripts/01_extract.py)
- **Bug ditemukan dan diperbaiki:** pembaca chat awal tidak mengenali baris yang diawali karakter tak terlihat (LRM U+200E) atau yang teksnya kosong setelah ':'. Akibatnya pesan menempel ke pesan sebelumnya. Hitungan audit awal ("9.671 pesan") **salah**; yang benar **80.230 pesan**. Ditambah tes `tests/test_common.py`.
- Laporan "LAPORAN KEJADIAN": 1.308 pesan; templat kosong 55; duplikat 20; **event unik 1.233**.
- Waktu respons valid 1.135; NULL 98 (terima NULL 20, tiba NULL 69). Tidak ada imputasi.
- Terlambat (>15 menit) 170 = 15,0% dari yang valid. Median 10 menit, maks 827 menit (outlier perlu penanganan).
- Parser tanggal diperbaiki (tanggal di baris berikutnya, "febuari"); 81 event tanpa baris tanggal memakai tanggal pesan (`sumber_tanggal` = tanggal_pesan).

### Tahap 2 Penautan pin (scripts/02_link_pins.py)
- Pin lokasi WhatsApp (`maps.google.com/?q=lat,lon`): **502**, 88% dikirim akun "Hotline Pemadam Dan Penyelamatan". Semua dalam bounding box Tanjungpinang.
- Pin ternyata hampir bersamaan dengan "Terima Laporan": 216 pin dalam ±10 menit dari jam terima vs hanya 16 pada kontrol (waktu pin digeser 7 hari). Jadi penautan lewat waktu bermakna, bukan kebetulan.
- Aturan: satu pin untuk satu event, selisih ≤ 10 menit. Jendela ±5/±10/±30: 178/207/248 event tertaut. Dipilih ±10 (jendela lebar menambah tautan palsu; kontrol ±30 menit memberi ~21% kebetulan).
- **Hasil: 207 event bertitik = 16,8% dari 1.233 event unik.** Klaster spasial hanya mewakili subset ini; harus ditulis di laporan.
- Validasi: median jarak titik ke median kelurahan-nya (dari teks laporan) 1,35 km vs 2,41 km jika label kelurahan diacak (n=115, 6 kelurahan) -> tautan konsisten dengan teks.
- Batasan: tidak ada kebenaran dasar (ground truth) penautan; tautan salah tetap mungkin (perkiraan kebetulan sekitar 3-7% pada ±10 menit).

### Normalisasi lokasi (scripts/geo_norm.py)
- Nama kelurahan mentah: 113 ejaan; hasil normalisasi: **977 event (79,2%) punya kelurahan kanonik (17 kelurahan)**, 33 di luar kota/tak dikenal, 223 NULL (kolom berisi nama kecamatan, kosong, ambigu, atau kalimat kronologis yang salah masuk kolom).
- Hirarki kelurahan->kecamatan diverifikasi dengan data: 941 dari 955 event (98,5%) konsisten; 14 konflik = salah ketik. Aturan: hirarki dipakai, ditandai `koreksi_hirarki`.
- Kecamatan NULL tersisa 120 (tidak ada kelurahan dan kecamatan terbaca). Tidak ditebak.
- Penyengat hanya 1 event: terlalu kecil untuk klaster kelurahan (ditangani saat klaster).

### Perbaikan ekstraksi gelombang 2 dan Tahap 3 Anonimisasi
- **Bug 2:** judul "LAPORAN KEJADIAN EVAKUASI DAN PENYELAMATAN*" membuat jenis kejadian di baris berikutnya tidak terbaca (218 event tanpa jenis) dan 49 event salah dibuang sebagai "templat kosong". Diperbaiki + tes. **Event unik kini 1.280**, jenis kosong tinggal 29.
- Bagian korban/kerugian sebelumnya salah mengambil judul bagian berikutnya; diganti parser bagian (`section`) + tes. Ditambah fitur `regu` (angka/romawi) dan `pos` jaga (Mako SKB, Pos Bintan Centre, Pos Dompak, Pos Senggarang).
- Insiden teknis: heredoc Bash mengubah `\n` menjadi baris baru sehingga berkas kode rusak dua kali. Aturan sejak itu: kode hanya ditulis lewat Write/Edit.
- Anonimisasi (`scripts/03_anonymize.py`): 48 petugas (PTG###), 1.062 pelapor (PLP####), 714 alamat (ALM####) dengan kode konsisten; RT/RW, HP, email, nama dihapus dari teks bebas; koordinat dibulatkan 3 desimal (~110 m); teks kronologis TIDAK dipublikasikan.
- Verifikasi independen pada berkas CSV publik: 0 dari 222 nomor HP, 0 dari 708 nama lengkap bocor. 12 alamat mentah yang masih muncul hanyalah nama tempat umum/institusi tanpa nomor rumah (mis. "Kampus UMRAH", "Kp. Bugis").
- Pemindai kebocoran menghentikan penulisan berkas publik saat pertama dijalankan; penyebabnya salah deteksi ("Warga Sekitar" bukan nama). Dibenahi dengan definisi label generik, bukan dengan melonggarkan pemindai.
- Alur reproduksi: tahap 1-3 butuh `_chat.txt` privat; tahap 4 dst hanya memakai `data/mentah_anonim/` sehingga bisa dijalankan siapa pun dari GitHub.

### Tahap 4 EDA (scripts/04_eda.py) dan Tahap 5 Praproses (scripts/05_preprocess.py)
- EDA: 11 gambar di `figures/eda_*.png`, ringkasan di `reports/eda_ringkasan.md`.
- **Temuan EDA 1 (heaping):** 70,6% waktu respons kelipatan 5 menit; 257 tepat 5, 269 tepat 10, **174 tepat 15**. Petugas membulatkan jam. Batas SPM jatuh persis di puncak -> label sensitif. Jika batas dibaca "<15" (bukan "<=15"), terlambat naik dari 170 ke 344. Dilaporkan sebagai analisis sensitivitas.
- **Temuan EDA 2 (miring):** respons median 10, rata-rata 18,5, p99 345, maks 827 menit; skewness 8,8 (log1p: 1,25). 17 event >180 menit (sebagian mungkin salah ketik jam) -> ditandai `outlier_respons`, tidak dihapus diam-diam.
- **Temuan EDA 3 (pola):** terlambat per pos: Mako SKB 5,5%, Pos Senggarang 8,1%, Pos Bintan Centre 16,7%, Pos Dompak 24,7%, tidak disebut 22,1%. Per jam: dini hari 4,1%, pagi 18,1%, siang 16,5%, malam 12,7%. Ini korelasi; bukan bukti sebab-akibat (Mako SKB di pusat kota, mis.).
- **Temuan EDA 4 (komposisi):** 44,9% evakuasi ular, 17% kebakaran lahan; kebakaran bangunan hanya 27 event. Data didominasi layanan penyelamatan hewan, bukan kebakaran besar.
- **Temuan EDA 5 (cakupan):** hanya 16,2% event punya titik pin; 83,8% tanpa koordinat.
- Praproses: 27 tanggal salah ketik (mis. 2024 vs 2025) dikoreksi ke tanggal pesan; 10 respons negatif -> NULL; kelurahan kanonik 1.023 event; label_usulan 1=170, 0=965, NULL=145 (dikeluarkan dari model, tidak diisi 0).
- Keluaran siap mining: klasifikasi.csv (1.135), titik_geo.csv (207; 195 berlabel), kelurahan_profil.csv (17; 16 layak klaster, Penyengat hanya 1 event).
- Tes anti-kebocoran `tests/test_leakage.py`: dt_tiba, dt_selesai, response_minutes, durasi_tangani dilarang jadi fitur.

### Tahap 6 Klasifikasi (scripts/06_classify.py, reports/klasifikasi_hasil.md)
- Pemisahan berurutan waktu: latih 908 event (16 Apr 2025 - 22 Jun 2026), uji 227 event (24 Jun - 18 Sep 2026). Prevalensi terlambat latih 13,9% vs uji 19,4% (ada pergeseran).
- CV berurutan (5 lipatan) PR-AUC: baseline 0,148; LogReg 0,296; **Random Forest 0,314 (terbaik)**; Gradient Boosting 0,305.
- Uji (ambang 0,431 dari OOF): RF PR-AUC 0,471 (acak 0,194), ROC-AUC 0,658, precision 0,265, recall 0,591, F1 0,366. Selang bootstrap 95% PR-AUC 0,33-0,61, ROC-AUC 0,56-0,75 -> **sinyal ada tetapi lemah-sedang dan tidak pasti**.
- Variabel terpenting: jenis kejadian, pos jaga, regu, jam. Lokasi (kelurahan/kecamatan) hampir tidak menambah (ablasi 0,469 vs 0,471). Tanpa pos & regu: 0,365; hanya jenis+waktu: 0,333.
- **Peringatan kejujuran:** tanpa outlier >180 menit PR-AUC uji turun ke 0,268 (lift 1,6x) -> sebagian "kemampuan" model bersumber dari outlier yang mungkin salah ketik. Sensitivitas definisi label: >10 menit lift 1,46; >15 menit 2,43; >=15 menit 1,44; >20 menit 3,17.
- Model aplikasi: models/model_terlambat.joblib (dilatih seluruh 1.135 event).

### Tahap 7 Klasterisasi (scripts/07_cluster.py, reports/klaster_hasil.md)
- A. 207 titik: K-Means k=3 silhouette 0,446 (tertinggi), stabilitas bootstrap ARI 0,93. DBSCAN terbaik eps=1 km: hanya 1 klaster besar + 1 kecil, noise 12%. Titik membentuk satu gumpalan kota yang sinambung, bukan kantong terpisah.
- Uji chi-kuadrat persen terlambat antar klaster K-Means: p=0,491 -> **tidak ada bukti klaster spasial berbeda tingkat keterlambatannya.**
- B. 16 kelurahan, fitur 6 dimensi, k=4, silhouette 0,34 (struktur lemah), ARI bootstrap 0,81, K-Means = Ward (ARI 1). Klaster: (0) kebakaran-dominan: Air Raja, Dompak, Kampung Bugis, Senggarang; (1) penyelamatan hewan, malam, terlambat rendah 8,8%: 6 kelurahan; (2) volume rendah, terlambat 18,2%; (3) volume tertinggi 9,3 event/bulan: Batu IX, Pinang Kencana. Interpretasi sebagai segmentasi deskriptif, bukan kelompok alami.

### Tahap 8-9 Aplikasi, paket, laporan (17 November 2026)
- Aplikasi Streamlit (`app/app.py`, logika di `app/scoring.py`, 3 tes). Uji asap di browser berhasil (skor 43% untuk contoh; konteks historis tampil). Tangkapan layar otomatis via Edge headless gagal (halaman hanya kerangka), jadi **tangkapan layar harus diambil tim** untuk Lampiran C.
- `scripts/08_package.py`: dist/Mentah_2401020051.7z (47 KB) dan dist/SiapMining_2401020051.7z (71 KB). Dikeluarkan dari git (`*.7z`) karena diunggah lewat Google Form.
- Laporan: `reports/FinPD_2401020051.md` -> PDF 20 halaman, 17 gambar (`scripts/09_build_report.py`, Edge headless).
- Pemindai PII akhir pada seluruh pohon berkas: 2 berkas CSV terindikasi, ternyata angka desimal `pin_gap_min` (bukan HP); dibulatkan 2 desimal. Seluruh rantai tahap 3-9 dijalankan ulang; hasil identik (seed tetap). 33 tes lolos.
- **Belum dikerjakan / harus tim:** (1) kolom tanggal dan PIC pada Gantt (Bab I.4) dan foto kegiatan/lokasi/tangkapan layar (Lampiran C), ditandai **[ISI TIM]**; (2) pemeriksaan `label_final`; (3) verifikasi redaksi tertulis SPM dan identitas penutur rekaman; (4) logo UMRAH pada sampul; (5) rekam video YouTube; (6) `git push` dan unggah formulir.

### Versi Word laporan akhir (17 November 2026)
- `scripts/10_build_docx.js` mengubah `reports/FinPD_2401020051.md` menjadi `reports/FinPD_2401020051.docx` (dapat diedit): sampul, daftar isi otomatis, daftar gambar, 18 tabel, 17 gambar bertitel, 12 penanda **[ISI TIM]** disorot kuning. Butuh `npm install docx`.
- Validasi skema OOXML lulus. **Belum dilihat di Word/LibreOffice** (LibreOffice tidak terpasang); periksa tampilan saat membuka, lalu klik kanan Daftar Isi > Update Field untuk nomor halaman.
- Kekurangan terhadap RTM: **Daftar Tabel belum ada** (tabel belum bertitik judul); logo UMRAH belum dipasang.

### Tangkapan layar aplikasi masuk laporan (17 November 2026)
- `scripts/12_screenshot_app.py` (Playwright + Edge terpasang) mengendalikan aplikasi seperti pengguna dan menyimpan 4 gambar di `figures/app/`: skor berisiko (60%), skor rendah (12%), profil wilayah, peta 207 titik. Skor pada layar cocok dengan hitungan model (60% dan 12%).
- Percobaan pertama salah: slider jam berhenti di 23 (penekanan tombol bertabrakan dengan render ulang Streamlit) sehingga skor 52%, bukan 60%. Dikoreksi dengan membaca nilai slider sebelum mengambil gambar; skrip kini gagal bila slider tidak mencapai target.
- Lampiran C laporan kini memuat C.1 tangkapan layar (4 gambar) dan C.2 foto kegiatan/lokasi (**[ISI TIM]**). PDF 22 halaman (21 gambar), DOCX 21 gambar, validasi OOXML lulus.
- Peta memakai ubin OpenStreetMap/CARTO dari internet; saat mengambil ulang gambar perlu koneksi.

### E-book panduan belajar untuk pemula (17 November 2026)
- `docs/ebook/00..10_*.md` (11 bab: pengantar, gambaran besar, kelayakan data, ekstraksi, label dan EDA, preprocessing, klasifikasi, klasterisasi, aplikasi/hasil/batasan, etika/file/reproduksi, UAS/latihan/glosarium) digabung oleh `scripts/13_build_ebook.py` menjadi `docs/EBOOK_Panduan_Belajar_DPKP.pdf` (46 halaman, 11 gambar, nomor halaman).
- Isi: analogi untuk pemula, cerita kesalahan nyata (9.671 vs 80.230 pesan, judul panjang, kolom korban salah baca, "Warga Sekitar" di pemindai privasi), perhitungan metrik dari matriks konfusi asli, tabel boleh/tidak boleh dikatakan, 12 keterbatasan, 25 pertanyaan UAS, 10 latihan, glosarium 40 istilah.
- Catatan jujur yang diajarkan: akurasi model (0,60) lebih rendah dari baseline "selalu tepat waktu" (0,81); PR-AUC 0,47 turun ke 0,27 tanpa 17 data ekstrem.
- Daftar isi berisi tautan, belum bernomor halaman. Tampilan diperiksa pada 4 halaman hasil render; sisanya belum dilihat satu per satu.

### Laporan akhir diperdalam (17 November 2026)
- Pertanyaan tim: 26 halaman terlalu sedikit? Jawaban: jumlah halaman bukan ukuran mutu; RTM tidak menetapkan minimum. Namun ada bagian yang tipis terhadap rubrik RTM (Bab III "contoh pada data", Bab IV "detail perhitungan", Daftar Tabel). Diperdalam dengan isi nyata, bukan pengisi.
- `scripts/14_report_extras.py` menghitung bahan tambahan dari data (reports/extras/*.md): ringkasan atribut, statistik per jenis/regu/kecamatan/bulan, uji chi-kuadrat dengan koreksi Bonferroni, contoh sebelum-sesudah, koefisien dan contoh perhitungan regresi logistik, impuritas Gini dan pohon ilustrasi, pusat K-Means, contoh silhouette dan DBSCAN, PR-AUC per lipatan, kalibrasi skor, kesalahan per kelompok/pos. Replikasi dicek: PR-AUC uji 0,471 dan label K-Means identik dengan tahap 06/07.
- `scripts/09_build_report.py` kini menyisipkan bahan tambahan, memberi nomor judul tabel (51 tabel), membuat Daftar Isi/Tabel/Gambar (22 gambar), dan nomor halaman. PDF 22 -> 37 halaman; DOCX diperbarui (validasi OOXML lulus), ditambah Daftar Pustaka (11 rujukan + materi kuliah), Lampiran B (kamus data), D (keputusan penting), E (33 tes), F (pertanyaan ke narasumber).
- **Temuan baru yang mengubah penafsiran (dilaporkan apa adanya):**
  1. Evakuasi tawon/lebah 39,0% terlambat (jenis lain 4-19%); 13 dari 17 outlier > 180 menit adalah tawon, 4 hewan lain, 0 kebakaran. Laporan masuk pagi (median pukul 10:00), petugas tiba pukul 17:00-18:59. DUGAAN (belum dikonfirmasi): pemusnahan sarang dijadwalkan sore hari. Tanpa tawon, PR-AUC model turun ke 0,294 (lift 1,78) -> sebagian kemampuan model berasal dari pola ini. Sebelumnya outlier diduga "mungkin salah ketik"; dugaan itu dikoreksi di laporan, e-book, dan skrip video.
  2. Recall model untuk kebakaran hanya 31% (5 dari 16), precision 17%; untuk penyelamatan hewan 77%.
  3. Kalibrasi: skor 0,2-0,6 hanya 15-17% terlambat sebenarnya (tidak lebih tinggi dari rata-rata); hanya skor >= 0,6 sesuai (70%, n=20). Ambang 0,431 menjaring banyak alarm palsu; aplikasi menyebut skor relatif.
  4. PR-AUC Random Forest per lipatan 0,245-0,374 (prevalensi lipatan 9,9-19,2%): Random Forest unggul di lipatan 1-3, Gradient Boosting di lipatan 4-5; ketiga model setara.
  5. Uji chi-kuadrat (Bonferroni 0,0056): regu, pos, jenis, kecamatan, blok jam signifikan (Cramer's V 0,11-0,28); kelurahan (p=0,019), hari, armada, kelompok tidak.
- E-book (bab 4, 6, 8, 10) dan skrip video (segmen 4 dan 8) disinkronkan dengan temuan di atas. Aplikasi TIDAK diubah (pesan "berisiko" tetap faktual: skor di atas ambang); laporan VI.1 menyarankan skor >= 60% dibaca risiko tinggi.

### Aplikasi diubah menjadi tiga tingkat risiko (17 November 2026)
- Alasan: kalibrasi (laporan Bab V.3) menunjukkan skor 0,43-0,60 hanya ±17% terlambat (setara rata-rata), sehingga label "BERISIKO" untuk semua skor di atas ambang 0,431 melebih-lebihkan.
- `app/scoring.py`: fungsi `tingkat(p, ambang)` dan konstanta `TINGGI = 0.60`; `score()` kini mengembalikan `tingkat`. `app/app.py`: tiga pesan (RISIKO TINGGI merah >= 60%, PERHATIAN kuning ambang-60%, RENDAH hijau < ambang) dengan angka kalibrasi, plus catatan recall penyelamatan hewan 77% vs kebakaran 31%.
- Tes bertambah 33 -> 35 (batas tingkat; tiga skenario demo 60% tinggi, 50% perhatian, 12% rendah). Tangkapan layar diambil ulang dengan pemeriksaan otomatis atas skor dan tingkat; gambar baru `figures/app/app_5_skor_perhatian.png`.
- Catatan teknis: server Streamlit lama di port 8502 masih menyajikan kode versi lama; pemeriksaan otomatis di skrip tangkapan layar menangkap hal itu.
- Disinkronkan: laporan (VI.1, V.3, Lampiran C dan E), PDF dan DOCX dibangun ulang, e-book (bab 3, 8, 9), skrip video Segmen 10 (kini 4 langkah, ±15 detik lebih panjang), README.
- Skor demo A sebenarnya 0,6048, tepat di atas batas 0,60; sedikit perubahan data bisa menggeser tingkatnya. Dicatat pada skrip video.

### Persiapan publikasi GitHub (18 November 2026)
- Prinsip: panduan unggah hanya mewajibkan **source code** yang publik. Laporan akhir dikumpulkan lewat Google Form, bukan GitHub.
- `.gitignore` disusun ulang: privasi (chat mentah, raw_private, .ogg, .7z, dist), dokumen kuliah di folder utama (RTM, panduan unggah, proposal), laporan akhir dan berkas antaranya, e-book, skrip video, naskah, panduan push. Disediakan blok opsi ketat (komentar) untuk menahan data/model jika tidak diizinkan.
- Simulasi di salinan sementara (`git init` + `git add -A`): 103 berkas ikut; seluruh item privat terkecualikan (0 cocok). Pemindaian PII pada berkas yang akan terpublikasi (79 berkas teks, 725 nama asli sebagai pembanding): tersisa hanya nilai fiktif untuk tes.
- Temuan dan perbaikan: `tests/test_anon.py` memakai nama asli narasumber dan `tests/test_common.py` memakai nama tampilan WhatsApp petugas sebagai contoh uji; diganti nama fiktif (35 tes tetap lolos; asersi pada test_common dijaga agar tidak menjadi trivial).
- Belum dilakukan: `git init`/commit/push (oleh ketua tim); izin DPKP untuk data anonim publik belum ditanyakan.
- Keputusan tim: data anonim **ikut dipublikasikan setelah izin DPKP**. Naskah pesan izin dan tiga pertanyaan teknis disiapkan di `docs/PESAN_UNTUK_NARASUMBER.md` (privat, di-.gitignore). Jalur cadangan: bila tidak ada izin sampai Kamis 19 November sore, aktifkan "OPSI KETAT" pada `.gitignore` (data/ dan models/ tidak dipublikasikan; data lewat 7z di Google Form).
- 18 November 2026: **DPKP memperbolehkan publikasi data anonim** (disampaikan anggota tim; alasan: data sudah disamarkan). `.gitignore` dipakai apa adanya (opsi ketat tidak diaktifkan). Izin dicatat di README.

### Insiden: berkas data anonim rusak karena disimpan ulang di Excel (18 November 2026)
- Ditemukan saat menguji repositori dari salinan bersih (hanya berkas yang ikut ter-push) sebelum push: tahap 05 gagal pada `data/mentah_anonim/events_mentah_anon.csv`.
- Penyebab: berkas itu tersimpan ulang di Excel. Dua kerusakan: (1) tanggal berubah ke format `4/16/2025 1:08` dan detik hilang; (2) **sembilan isian `jenis_raw` yang diawali "-" (mis. "- Kebakaran Lahan") dibaca Excel sebagai rumus dan menjadi `#NAME?`.** Versi rusak itu sudah ter-commit secara lokal (belum di-push).
- Perbaikan: berkas diregenerasi dari sumbernya (`scripts/03_anonymize.py`, deterministik). Bukti kebenaran: setelah regenerasi, tahap 05 menghasilkan seluruh berkas `data/siap_mining/*.csv` yang **identik** dengan versi ter-commit (artinya hasil analisis tidak pernah memakai data rusak), dan 10 berkas keluaran (siap_mining, mentah_anonim, eda/klasifikasi/klaster) identik pada salinan bersih.
- Dampak: tabel contoh jenis kejadian pada laporan (reports/extras/contoh_jenis.md) sempat memuat `#name?`; kini dibangun ulang (Penyelamatan Lainnya 27 ejaan; baris `#name?` hilang). PDF/DOCX laporan dibangun ulang. Paket dist/*.7z dibangun ulang dari data benar.
- Pencegahan: `scripts/05_preprocess.py` kini berhenti dengan pesan jelas bila format `msg_ts` bukan ISO (tanda disimpan ulang Excel). Aturan tim: **jangan membuka lalu menyimpan CSV data dari Excel**; lihat saja, atau gunakan "Simpan sebagai" ke berkas lain.
- Juga ditambahkan `requirements.txt` yang lengkap dan terkunci versinya (sebelumnya tidak memuat tabulate, streamlit, scipy, dll.) dan `requirements-dokumen.txt`.
