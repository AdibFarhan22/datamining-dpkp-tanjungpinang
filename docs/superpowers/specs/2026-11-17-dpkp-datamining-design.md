# Desain Proyek: Prediksi Risiko Keterlambatan Respons dan Klasterisasi Profil Risiko Wilayah, DPKP Kota Tanjungpinang

Tanggal: 17 November 2026. Status: **menunggu persetujuan tim**. Tenggat unggah: Jumat 20 November 2026 (PANDUAN UNGGAH LAPORAN AKHIR; RTM menulis 14 November, dianggap digantikan panduan).
Tim: 2401020051 Abdul Hafidz (ketua), 2401020011 Bayu Adhandika, 2401020090 Adib Farhan Sihombing, 2401020058 Muhammad Rahman Afrialdi, 2401020084 Vito Hendriansyah.

## 1. Tujuan dan alasan
Mitra (DPKP, narasumber Kasi Peningkatan Kapasitas Aparatur) mencatat kejadian lewat grup WhatsApp. Belum ada gambaran terstruktur tentang kejadian yang berisiko terlambat dan wilayah yang perlu perhatian. Proyek menghasilkan (a) model klasifikasi risiko keterlambatan dan (b) klaster profil risiko wilayah. Nilai ditentukan rubrik RTM: EDA (visual dan statistik), deteksi masalah data, pra-proses, solusi mendekati ideal, uraian runut, argumen logis. Kejujuran dan kerunutan lebih bernilai daripada angka akurasi yang bagus.

## 2. Pertanyaan utama: apakah data memenuhi syarat?
Klasifikasi butuh label kelas. Klasterisasi spasial butuh titik spasial. Dua hal berbeda, dan hasil audit (skrip: `scripts/audit/`, dijalankan 17 Nov 2026 pada `_chat.txt`):

| Kebutuhan | Temuan | Verdict |
|---|---|---|
| Sumber | 9.671 pesan, Apr 2025 sampai Sep 2026; 1.309 kemunculan "LAPORAN KEJADIAN", sekitar 1.217 pesan laporan | Cukup |
| Label (waktu terima dan tiba) | Terima ada di 1.199; tiba ada di sekitar 1.077 pasangan valid setelah variasi "Sampai/Hadir" ditangani; 130 laporan tidak bisa dihitung | **Memenuhi**, dengan syarat |
| Distribusi label (batas 15 menit) | sekitar 15,3% terlambat (tidak seimbang); median 10 menit; p99 sekitar 398 menit (ada outlier atau salah ketik) | Perlu penanganan imbalance dan outlier |
| Titik spasial | 0 tautan gmaps, hanya 22 koordinat di dalam teks laporan; 502 pin WhatsApp terkirim sebagai pesan terpisah | **Belum memenuhi sampai pin berhasil ditautkan** |
| Kelurahan | 105 ejaan mentah untuk sekitar 18 kelurahan | Perlu normalisasi |

Catatan jujur tentang label: label adalah **turunan** dari catatan jam yang diketik manual, bukan pengukuran sensor. Jam bisa salah, terbulatkan, atau diisi belakangan. `label_usulan` dihitung otomatis; `label_final` baru ada setelah tim memeriksa event unik. Rekaman `.ogg` tidak ada di folder, jadi dasar aturan 15 menit saat ini hanya teks yang diketik pengguna dan tidak bisa kami klaim terverifikasi dari audio.

## 3. Keputusan yang sudah diambil pengguna
1. Klaster spasial: pin lokasi ditautkan ke laporan lewat kedekatan waktu dan pengirim, divalidasi dengan kelurahan di teks, lalu DBSCAN/K-Means pada titik. Ditambah klaster profil per kelurahan.
2. Laporan dengan waktu tiba atau terima tidak valid: `NULL`, dikeluarkan dari model, tetap dipakai untuk EDA. Tidak ada imputasi.
3. Cakupan pekerjaan saya: seluruh pipeline, dokumentasi, data, laporan, naskah video. Pengguna melakukan rekam video, `git push`, dan unggah form.

## 4. Pendekatan (dua alternatif ditolak)
- **Dipilih:** CRISP-DM penuh, skrip Python berurutan yang bisa dijalankan ulang, setiap tahap menulis keluaran ke folder dan log.
- Ditolak: notebook tunggal (sulit diaudit dan di-diff di GitHub).
- Ditolak: klaster kelurahan saja (hanya sekitar 18 baris, lemah di rubrik "solusi mendekati ideal"). Tetap dipakai sebagai pelengkap.

## 5. Rancangan teknis (pilihan saya, bukan kesepakatan)
- Bahasa Python 3.10; pandas ada, scikit-learn dan matplotlib akan dipasang.
- Struktur folder: `data/raw_private/` (jangan di-push), `data/mentah_anonim/`, `data/siap_mining/`, `scripts/` (01 ekstraksi, 02 anonimisasi, 03 EDA, 04 preprocess, 05 klasifikasi, 06 klaster, 07 evaluasi), `reports/`, `figures/`, `docs/`, `LOG.md`.
- Anonimisasi konsisten (kode `X001`): nama pelapor dan personil, nomor HP, alamat dan nomor rumah, RT/RW. Kelurahan dan kecamatan dipertahankan. Koordinat dibulatkan atau digeser konsisten agar rumah tidak teridentifikasi.
- **`_chat.txt` mentah memuat nomor HP warga dan nama pegawai; tidak boleh masuk GitHub publik.** Saya buat `.gitignore`.
- Klasifikasi: fitur hanya yang diketahui saat laporan masuk (jenis, kelurahan, jam, hari, regu, armada). **Waktu tiba dan selesai tidak boleh jadi fitur** (kebocoran label). Pembanding: baseline mayoritas, Regresi Logistik, Random Forest, Gradient Boosting. Validasi dengan pemisahan **berurutan waktu**, bukan acak; metrik utama PR-AUC, recall kelas terlambat, F1, bukan akurasi saja.
- Klaster: normalisasi, pilih k dengan silhouette dan Davies-Bouldin, bandingkan K-Means dan DBSCAN; laporkan stabilitas dan jumlah titik yang berhasil ditautkan.
- Keluaran akhir: laporan `FinPD_2401020051` (bab I sampai VI sesuai RTM), `Mentah_2401020051.7z`, `SiapMining_2401020051.7z`, aplikasi sederhana (skor risiko dan peta klaster), naskah video dengan penanda segmen.

## 6. Non-tujuan dan anti-tujuan
- Bukan evaluasi kinerja individu regu; temuan tidak boleh dipakai menyalahkan orang.
- Bukan klaim kausal ("regu X lambat karena Y").
- Anti-tujuan: angka bagus karena kebocoran label, pembulatan yang disembunyikan, atau data pribadi yang bocor ke GitHub publik.

## 7. Risiko
| Risiko | Penanganan |
|---|---|
| Penautan pin gagal untuk sebagian besar laporan | Laporkan persentase tertaut apa adanya; jika terlalu sedikit, klaster spasial dilaporkan sebagai eksploratif |
| Waktu 3 hari | Urutan kerja: ekstraksi, anonimisasi, EDA, label, model dasar dulu; tahap hias belakangan |
| Label tidak seimbang dan jam tidak akurat | Stratifikasi, `class_weight`, analisis sensitivitas batas 10/15/20 menit |

## 8. Persetujuan
Dokumen ini harus disetujui sebelum kode ditulis. Pemeriksaan oleh subagent pembaca tidak dijalankan karena tenggat 3 hari; dokumen dibaca ulang sendiri.
