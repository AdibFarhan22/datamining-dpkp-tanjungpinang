# Ringkasan EDA (otomatis dari scripts/04_eda.py)

- Event unik: **1280**; rentang terima: 2024-06-19 15:00:00 s/d 2026-09-18 13:46:00
- Event dengan respons valid: **1135** (88.7%); NULL: 145
- Label terlambat (>15 menit): **170** (15.0%) ; tepat waktu 965
- Event bertitik (pin): 207 (16.2%)

## Statistik waktu respons (menit)

|       |   nilai |
|:------|--------:|
| count | 1135    |
| mean  |   18.47 |
| std   |   57.28 |
| min   |    0    |
| 25%   |    5    |
| 50%   |   10    |
| 75%   |   15    |
| 90%   |   20    |
| 95%   |   30    |
| 99%   |  344.56 |
| max   |  827    |

- Respons 0 menit: 20 | >60: 33 | >180: 17
- Skewness: 8.80; skewness log1p: 1.25

## Missing value per kolom (persen)

|                  |   %NULL |
|:-----------------|--------:|
| dt_diterima      |     5.2 |
| dt_tiba          |     8.9 |
| dt_selesai       |     2.2 |
| response_minutes |    11.3 |
| jenis_raw        |     2.3 |
| kel              |    17.4 |
| kec              |     9.4 |
| pos              |    23.4 |
| regu             |     3.7 |
| armada           |    15.2 |
| lat_r            |    83.8 |

## Jenis kejadian (kategori)

| jenis                 |   n |   persen |
|:----------------------|----:|---------:|
| Evakuasi Ular         | 575 |     44.9 |
| Kebakaran Lahan       | 217 |     17   |
| Evakuasi Hewan Lain   | 149 |     11.6 |
| Evakuasi Tawon/Lebah  | 122 |      9.5 |
| Evakuasi Benda/Cincin |  73 |      5.7 |
| Tidak Diketahui       |  49 |      3.8 |
| Penyelamatan Lainnya  |  43 |      3.4 |
| Kebakaran Bangunan    |  27 |      2.1 |
| Kebakaran Lainnya     |  23 |      1.8 |
| Kebakaran Kendaraan   |   2 |      0.2 |

## Terlambat per kelompok jenis

| kelompok             |   n |   terlambat |   persen |   median_menit |
|:---------------------|----:|------------:|---------:|---------------:|
| Kebakaran            | 240 |          34 |    0.142 |             11 |
| Penyelamatan Hewan   | 765 |         121 |    0.158 |             10 |
| Penyelamatan Lainnya |  81 |           8 |    0.099 |             10 |
| Tidak Diketahui      |  49 |           7 |    0.143 |              7 |

## Terlambat per pos jaga

| pos               |   n |   persen |   median_menit |
|:------------------|----:|---------:|---------------:|
| Mako SKB          | 401 |    0.055 |            8   |
| Pos Bintan Centre | 252 |    0.167 |           12.5 |
| Pos Dompak        | 178 |    0.247 |           12   |
| Pos Senggarang    |  37 |    0.081 |            5   |
| Tidak disebut     | 267 |    0.221 |           10   |

## Terlambat per kecamatan

| kec                 |   n |   persen |   median_menit |
|:--------------------|----:|---------:|---------------:|
| Bukit Bestari       | 283 |    0.092 |            9   |
| Luar Kota/Lainnya   |  14 |    0.214 |            5   |
| Tanjungpinang Barat | 160 |    0.119 |            9   |
| Tanjungpinang Kota  | 120 |    0.133 |           10   |
| Tanjungpinang Timur | 444 |    0.185 |           10   |
| Tidak diketahui     | 114 |    0.211 |           11.5 |

## Terlambat per jam terima (blok)

| blok   |   n |   persen |   median_menit |
|:-------|----:|---------:|---------------:|
| 00-05  |  98 |    0.041 |              7 |
| 06-11  | 354 |    0.181 |             10 |
| 12-17  | 399 |    0.165 |             10 |
| 18-23  | 284 |    0.127 |             10 |

## Laporan per bulan

| bulan   |   n |
|:--------|----:|
| 2024-06 |   1 |
| 2025-01 |   2 |
| 2025-02 |   1 |
| 2025-03 |   2 |
| 2025-04 |  25 |
| 2025-05 |  48 |
| 2025-06 |  64 |
| 2025-07 |  69 |
| 2025-08 |  67 |
| 2025-09 |  64 |
| 2025-10 |  58 |
| 2025-11 |  58 |
| 2025-12 |  42 |
| 2026-01 |  93 |
| 2026-02 |  85 |
| 2026-03 | 103 |
| 2026-04 |  88 |
| 2026-05 |  62 |
| 2026-06 |  55 |
| 2026-07 |  59 |
| 2026-08 | 100 |
| 2026-09 |  67 |
| NaT     |  67 |