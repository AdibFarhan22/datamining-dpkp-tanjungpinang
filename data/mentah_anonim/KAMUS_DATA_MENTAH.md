# Kamus Data Mentah Terdigitalisasi (anonim)

Sumber: laporan "LAPORAN KEJADIAN" pada grup WhatsApp resmi DPKP Kota Tanjungpinang (April 2025 - September 2026), diekstraksi otomatis dari teks bebas oleh `scripts/01_extract.py`. Satu baris = satu event unik (setelah penghapusan 22 duplikat dan 6 templat kosong). Data pribadi disamarkan dengan kode konsisten (lihat `scripts/03_anonymize.py`). Teks kronologis laporan **tidak** disertakan.

Berkas: `events_mentah_anon.csv` (1.280 baris, 25 kolom).

| Kolom | Arti | Catatan |
|---|---|---|
| event_id | nomor urut event | kunci |
| msg_ts | waktu pesan dikirim di grup | waktu server chat |
| tanggal | tanggal kejadian menurut teks laporan | bisa salah ketik; dikoreksi di praproses |
| sumber_tanggal | `teks` atau `tanggal_pesan` | `tanggal_pesan` = baris tanggal tidak ada |
| dt_diterima | waktu laporan diterima | kosong bila tidak tertulis/valid |
| dt_tiba | waktu regu tiba di lokasi | kosong bila tidak tertulis/valid |
| dt_selesai | waktu selesai | kosong bila tidak tertulis |
| response_minutes | dt_tiba - dt_diterima (menit) | kosong (NULL), bukan 0, bila salah satu waktu tidak valid |
| petugas_kode | PTG### = pengirim pesan (petugas); AKUN_HOTLINE = akun institusi | disamarkan |
| pelapor_kode | PLP#### = pelapor warga | disamarkan |
| alamat_kode | ALM#### = alamat kejadian | disamarkan; nomor rumah dan RT/RW tidak ada |
| alamat_anon | kode alamat + kecamatan seperti diketik | format sesuai panduan penyamaran |
| jenis_raw | jenis kejadian seperti diketik | ejaan beragam |
| kel_raw, kec_raw | kelurahan/kecamatan seperti diketik | tidak dinormalisasi |
| armada, regu, pos | armada yang digunakan, nomor regu, pos jaga | hasil parser |
| dampak, korban, kerugian, luas | isian bebas | telepon, nama, RT/RW dihapus |
| lat_r, lon_r | koordinat pin yang ditautkan, dibulatkan 3 desimal (~110 m) | hanya 207 event |
| pin_gap_min | selisih menit jam terima laporan dan waktu pin | kecil = tautan kuat |

Konsistensi samaran: entitas yang sama (nama/alamat sama setelah dirapikan huruf dan spasi) selalu mendapat kode yang sama. Peta kode ke nama asli disimpan privat dan tidak dipublikasikan.
