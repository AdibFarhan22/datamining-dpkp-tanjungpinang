# Kamus Data Siap Mining

Dibuat oleh `scripts/05_preprocess.py` dari `data/mentah_anonim/events_mentah_anon.csv` dan diperkaya oleh `scripts/07_cluster.py`.

## klasifikasi.csv (1.135 baris: event dengan waktu respons valid, urut waktu)
| Kolom | Peran | Arti |
|---|---|---|
| event_id | kunci | |
| dt_diterima | pemisah waktu | bukan fitur |
| label_usulan | **target** | 1 = terlambat (respons > 15 menit), 0 = tepat waktu (<= 15). Dihitung otomatis. |
| label_final | target resmi | **kosong**; diisi setelah tim memeriksa event unik |
| response_minutes | hasil | **dilarang jadi fitur** (kebocoran label); hanya untuk analisis sensitivitas |
| outlier_respons | penanda | 1 bila respons > 180 menit (dipertahankan, ditandai) |
| jenis, kelompok | fitur | kategori jenis kejadian (10) dan kelompok besar |
| kecamatan, kelurahan | fitur | hasil normalisasi; "Tidak diketahui" bila tidak terbaca |
| pos, regu, armada_grup | fitur | pos jaga, nomor regu, kelompok armada; "Tidak disebut" bila kosong |
| jam, blok_jam, hari, akhir_pekan | fitur | dari waktu laporan diterima (hari: 0 = Senin) |

Aturan: waktu tiba/terima tidak valid -> label NULL -> baris dikeluarkan dari file ini; tidak pernah diisi 0.

## titik_geo.csv (207 baris) dan hasil_klaster_titik.csv
Event dengan pin lokasi tertaut. lat_r/lon_r dibulatkan 3 desimal. `hasil_klaster_titik.csv` menambah `klaster_kmeans` (k = 3) dan `klaster_dbscan` (-1 = noise).

## kelurahan_profil.csv (17 baris) dan hasil_klaster_kelurahan.csv (16 baris)
Per kelurahan: n_event, n_valid, share_kebakaran, share_hewan, share_malam (18:00-05:59), median_respons, pct_terlambat, median_tangani, event_per_bulan, layak_klaster (n_event >= 10 dan n_valid >= 8). `hasil_klaster_kelurahan.csv` menambah `terlambat_susut` (persen terlambat disusutkan ke rata-rata global, bobot 10) dan `klaster` (0-3).

## events_bersih.csv (1.280 baris)
Seluruh event setelah praproses, termasuk yang label/waktunya NULL.
