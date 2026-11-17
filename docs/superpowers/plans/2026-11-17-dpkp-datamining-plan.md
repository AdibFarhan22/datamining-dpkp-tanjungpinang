# DPKP Data Mining Implementation Plan

> **For agentic workers:** Eksekusi native (satu sesi) per tugas, centang `- [ ]` saat selesai. Pengguna sudah menyetujui desain dan meminta langsung dikerjakan karena tenggat 20 Nov 2026.

**Goal:** Pipeline CRISP-DM dari `_chat.txt` sampai model klasifikasi keterlambatan, klaster wilayah, data anonim, laporan, dan naskah video.

**Architecture:** Skrip Python bernomor di `scripts/`, tiap skrip membaca keluaran sebelumnya dan menulis CSV/gambar ke folder tetap; `LOG.md` mencatat setiap tahap dan temuan jujur. Tes kecil per modul di `tests/` memakai pytest.

**Tech Stack:** Python 3.10, pandas 2.3, scikit-learn, matplotlib, pytest, py7zr atau 7z.

**Spec:** `docs/superpowers/specs/2026-11-17-dpkp-datamining-design.md`

## Global Constraints
- Batas terlambat: `response_minutes > 15`; tidak valid: `NULL`, tidak pernah 0 atau imputasi.
- Label model = `label_usulan`; `label_final` terpisah dan kosong sampai diperiksa tim.
- Waktu tiba/selesai dilarang jadi fitur; validasi pemisahan berurutan waktu.
- `data/raw_private/` dan `_chat.txt` tidak boleh masuk GitHub (.gitignore).
- Anonimisasi konsisten: kode samaran sama untuk entitas sama; Kelurahan/Kecamatan dipertahankan.
- Nama berkas akhir: `FinPD_2401020051.pdf`, `Mentah_2401020051.7z`, `SiapMining_2401020051.7z`.

## Review Focus
- Laporan tanpa waktu tiba atau dengan jam lewat tengah malam: `NULL` atau hitung lintas hari, diuji.
- Pesan laporan ganda (repost): dideduplikasi, diuji.
- Pin lokasi tanpa laporan terdekat: tidak ditautkan, bukan ditebak.
- Nomor HP/nama bocor ke keluaran anonim: tes pemindai regex gagal bila ada.
- Fitur kebocoran (tiba/selesai) masuk matriks fitur: tes gagal.

## File Structure
- `scripts/common.py` parser pesan WA dan util. `scripts/01_extract.py`, `02_link_pins.py`, `03_anonymize.py`, `04_eda.py`, `05_preprocess.py`, `06_classify.py`, `07_cluster.py`, `08_package.py`.
- `tests/test_*.py`. Keluaran: `data/`, `figures/`, `reports/`. `LOG.md`.

### Task 1: Setup
- [ ] Buat folder, `.gitignore`, `requirements.txt`, `LOG.md`; `pip install scikit-learn matplotlib pytest py7zr`.
- [ ] Verifikasi: `python -c "import sklearn,matplotlib,pytest"` tanpa error.

### Task 2: Ekstraksi (`01_extract.py`)
**Produces:** `data/raw_private/events_raw.csv` kolom `msg_id,ts,sender,jenis,pelapor,alamat,kel,kec,terima,tiba,selesai,armada,regu,korban,kerugian,luas,text`; fungsi `parse_time(text, label_regex) -> int|None` di `common.py`.
- [ ] Tes: `parse_time("Terima Laporan : 00.30 WIB","terima")==30`; "Regu Sampai di Lokasi : 19.28WIB" terbaca; "Tiba di Lokasi : WIB" -> None.
- [ ] Implementasi dengan regex toleran variasi; dedup repost; jalankan, catat hitungan di LOG.

### Task 3: Tautkan pin (`02_link_pins.py`)
**Consumes:** events_raw.csv, pin `maps.google.com/?q=lat,lon` dari chat. **Produces:** `events_geo.csv` dengan `lat,lon,pin_gap_min,pin_method`.
- [ ] Tes: pin dari pengirim sama dalam ±30 menit ditautkan; pin tanpa laporan dekat tidak.
- [ ] Implementasi; validasi pin vs kelurahan di teks; laporkan % tertaut dan akurasi pada sampel manual.

### Task 4: Anonimisasi (`03_anonymize.py`)
**Produces:** `data/mentah_anonim/events_anon.csv`; `data/raw_private/pseudonym_map.csv` (privat).
- [ ] Tes: tidak ada pola HP `0[0-9]{9,12}`, nama pelapor, RT/RW di keluaran; kode konsisten antar-pemanggilan.
- [ ] Implementasi; koordinat dibulatkan 3 desimal.

### Task 5: EDA (`04_eda.py`)
- [ ] Statistik ringkas, missing, outlier, distribusi jenis/kelurahan/jam/respons, label; simpan ≥8 gambar di `figures/`; catat di LOG.

### Task 6: Preprocess (`05_preprocess.py`)
**Produces:** `data/siap_mining/klasifikasi.csv`, `kelurahan_profil.csv`, `titik_geo.csv`.
- [ ] Normalisasi kelurahan (kamus ejaan), kelompok jenis kejadian, outlier respons (>180 menit ditandai, tidak dihapus diam-diam), fitur waktu.
- [ ] Tes kebocoran: kolom terlarang tidak ada di fitur.

### Task 7: Klasifikasi (`06_classify.py`)
- [ ] Baseline mayoritas, LogReg, RF, GradientBoosting; split berurutan waktu; metrik PR-AUC, recall, F1; sensitivitas batas 10/15/20; simpan hasil dan gambar.

### Task 8: Klaster (`07_cluster.py`)
- [ ] K-Means dan DBSCAN pada titik; K-Means pada profil kelurahan; silhouette/DB; peta sebaran.

### Task 9: Paket dan dokumen (`08_package.py`, reports)
- [ ] Buat 7z Mentah dan SiapMining; `README.md`; laporan bab I-VI (`reports/FinPD_2401020051.md` + PDF); naskah video dengan penanda segmen; panduan `git push`.
