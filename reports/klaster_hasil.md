# Hasil Klasterisasi (scripts/07_cluster.py)

## A. Klaster titik spasial

Jumlah titik: **207** dari 1.280 event unik (16,2%). Koordinat dibulatkan 3 desimal (~110 m). Hasil hanya mewakili event yang pinnya berhasil ditautkan, bukan seluruh kejadian.

### A1. K-Means: pemilihan k

|   k |   silhouette |   davies_bouldin |   inersia |
|----:|-------------:|-----------------:|----------:|
|   2 |        0.392 |            1.029 |  1551.4   |
|   3 |        0.446 |            0.773 |   967.328 |
|   4 |        0.387 |            0.853 |   763.769 |
|   5 |        0.386 |            0.871 |   591.232 |
|   6 |        0.38  |            0.805 |   490.279 |
|   7 |        0.351 |            0.87  |   414.145 |
|   8 |        0.389 |            0.803 |   352.511 |

k terpilih (silhouette tertinggi) = **3**; stabilitas bootstrap (ARI rata-rata, 1 = sangat stabil) = **0.93**.

### A2. DBSCAN: grid parameter

|   eps_km |   min_samples |   n_klaster |   noise_persen |   silhouette |
|---------:|--------------:|------------:|---------------:|-------------:|
|     0.5  |             4 |           5 |         33.816 |        0.286 |
|     0.5  |             6 |           4 |         37.681 |        0.347 |
|     0.5  |             8 |           5 |         45.411 |        0.47  |
|     0.75 |             4 |           3 |         18.357 |        0.296 |
|     0.75 |             6 |           2 |         21.739 |        0.281 |
|     0.75 |             8 |           3 |         27.053 |        0.122 |
|     1    |             4 |           2 |         12.077 |        0.597 |
|     1    |             6 |           1 |         15.942 |      nan     |
|     1    |             8 |           1 |         16.908 |      nan     |
|     1.5  |             4 |           2 |          7.246 |        0.544 |
|     1.5  |             6 |           1 |         11.111 |      nan     |
|     1.5  |             8 |           1 |         12.56  |      nan     |
|     2    |             4 |           1 |          2.899 |      nan     |
|     2    |             6 |           2 |          3.865 |        0.527 |
|     2    |             8 |           1 |          8.696 |      nan     |

DBSCAN terpilih (silhouette tertinggi, noise <= 30%): eps=1.0 km, min_samples=4 -> 2 klaster, noise 12.1%.

### A3. Profil klaster K-Means

|   klaster_kmeans |   n |   n_berlabel |   pct_terlambat |   median_respons |   pct_kebakaran | kelurahan_dominan   |
|-----------------:|----:|-------------:|----------------:|-----------------:|----------------:|:--------------------|
|                0 |  96 |           91 |           0.253 |             12   |           0.188 | Batu IX             |
|                1 |  15 |           14 |           0.214 |              7.5 |           0.4   | Kampung Bugis       |
|                2 |  96 |           90 |           0.322 |             15   |           0.396 | Tidak diketahui     |

Uji chi-kuadrat proporsi terlambat antar klaster K-Means: p = **0.491** (tidak signifikan pada alpha 5%: tidak ada bukti bahwa klaster spasial berbeda tingkat keterlambatannya).

### A4. Profil klaster DBSCAN (-1 = noise)

|   klaster_dbscan |   n |   n_berlabel |   pct_terlambat |   median_respons |   pct_kebakaran | kelurahan_dominan   |
|-----------------:|----:|-------------:|----------------:|-----------------:|----------------:|:--------------------|
|               -1 |  25 |           24 |           0.25  |               10 |            0.48 | Kampung Bugis       |
|                0 | 178 |          168 |           0.292 |               13 |            0.27 | Batu IX             |
|                1 |   4 |            3 |           0     |                5 |            0.5  | Kampung Bugis       |


## B. Klaster profil kelurahan

16 kelurahan layak (n_event>=10; Penyengat dikeluarkan: 1 event). Fitur: log_volume, share_kebakaran, share_malam, median_respons, terlambat_susut, median_tangani (distandardisasi). Persentase terlambat disusutkan ke rata-rata global (0.144) dengan bobot 10 agar kelurahan kecil tidak terlalu berisik. **Hanya 16 baris: temuan eksploratif.**

### B1. Pemilihan k

|   k |   silhouette_kmeans |    DB |   silhouette_ward |   ARI_kmeans_vs_ward |
|----:|--------------------:|------:|------------------:|---------------------:|
|   2 |               0.328 | 1.162 |             0.328 |                    1 |
|   3 |               0.296 | 1.043 |             0.296 |                    1 |
|   4 |               0.342 | 0.909 |             0.342 |                    1 |
|   5 |               0.322 | 0.777 |             0.322 |                    1 |

k terpilih = **4**; stabilitas bootstrap ARI = **0.81**.

### B2. Profil klaster kelurahan

|   klaster |   n_kelurahan |   event_per_bulan |   share_kebakaran |   share_malam |   median_respons |   pct_terlambat |   median_tangani | anggota                                                                                        |
|----------:|--------------:|------------------:|------------------:|--------------:|-----------------:|----------------:|-----------------:|:-----------------------------------------------------------------------------------------------|
|         0 |             4 |             3.537 |             0.393 |         0.285 |             9.5  |           0.131 |           54.25  | Air Raja, Dompak, Kampung Bugis, Senggarang                                                    |
|         1 |             6 |             3.04  |             0.071 |         0.425 |             9    |           0.088 |           25     | Kampung Baru, Kampung Bulang, Kemboja, Tanjung Ayun Sakti, Tanjung Unggat, Tanjungpinang Barat |
|         2 |             4 |             2.207 |             0.082 |         0.289 |            10    |           0.182 |           34.375 | Bukit Cermin, Melayu Kota Piring, Sei Jang, Tanjungpinang Kota                                 |
|         3 |             2 |             9.266 |             0.243 |         0.33  |            13.25 |           0.18  |           47.5   | Batu IX, Pinang Kencana                                                                        |
