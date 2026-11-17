# Hasil Klasifikasi Risiko Keterlambatan (scripts/06_classify.py)

- Latih/CV: 908 event (2025-04-16 s/d 2026-06-22); Uji (periode terakhir): 227 event (2026-06-24 s/d 2026-09-18).
- Prevalensi terlambat: latih 13.9%; uji 19.4% (44 kasus positif). **Dengan positif sesedikit ini, selang kepercayaan lebar.**

## 1. Validasi silang berurutan waktu (TimeSeriesSplit, 5 lipatan, hanya data latih)

| Model                 |   CV_PR_AUC |   SD_PR |   CV_ROC_AUC |   lipatan |
|:----------------------|------------:|--------:|-------------:|----------:|
| Baseline (prevalensi) |       0.148 |   0.036 |        0.5   |         5 |
| Regresi Logistik      |       0.296 |   0.054 |        0.7   |         5 |
| Random Forest         |       0.314 |   0.048 |        0.726 |         5 |
| Gradient Boosting     |       0.305 |   0.029 |        0.719 |         5 |

## 2. Hasil pada data uji (periode terakhir)

Ambang untuk model terbaik (Random Forest) = 0.431, dipilih dari prediksi out-of-fold data latih. Model lain dievaluasi pada ambang 0,5 (hanya PR-AUC/ROC-AUC yang bebas ambang). PR-AUC baseline acak = prevalensi = 0.194.

| Model                 |   PR_AUC |   ROC_AUC |   Precision |   Recall |    F1 |
|:----------------------|---------:|----------:|------------:|---------:|------:|
| Baseline (prevalensi) |    0.194 |     0.5   |       0     |    0     | 0     |
| Regresi Logistik      |    0.347 |     0.627 |       0.25  |    0.682 | 0.366 |
| Random Forest         |    0.471 |     0.658 |       0.265 |    0.591 | 0.366 |
| Gradient Boosting     |    0.406 |     0.671 |       0.5   |    0.068 | 0.12  |

**Selang kepercayaan 95% bootstrap (Random Forest, uji):** PR-AUC 0.328 - 0.610; ROC-AUC 0.562 - 0.754; Recall 0.439 - 0.739. Lebar selang menunjukkan data uji kecil.

Matriks konfusi (baris=aktual tepat waktu/terlambat, kolom=prediksi):

|                  |   prediksi tepat |   prediksi terlambat |
|:-----------------|-----------------:|---------------------:|
| aktual tepat     |              111 |                   72 |
| aktual terlambat |               18 |                   26 |

## 3. Pentingnya variabel (permutation importance pada data uji; turunnya PR-AUC saat variabel diacak)

|               |   turun_PR_AUC |     sd |
|:--------------|---------------:|-------:|
| jenis         |         0.1319 | 0.0356 |
| pos           |         0.1179 | 0.0351 |
| kelompok      |         0.078  | 0.0389 |
| regu          |         0.0692 | 0.0324 |
| jam (sin/cos) |         0.0599 | 0.0292 |
| armada_grup   |         0.0256 | 0.0138 |
| blok_jam      |         0.0179 | 0.0137 |
| kecamatan     |         0.0084 | 0.0134 |
| kelurahan     |         0.0063 | 0.0132 |
| hari          |         0.0023 | 0.0156 |
| akhir_pekan   |         0.0012 | 0.0028 |

Catatan: ini ukuran asosiasi prediktif, **bukan** sebab-akibat.

## 4. Ablasi fitur (PR-AUC uji)

| Skenario                            |   PR_AUC_uji |
|:------------------------------------|-------------:|
| Semua fitur                         |        0.471 |
| Tanpa pos & regu                    |        0.365 |
| Tanpa lokasi (kelurahan, kecamatan) |        0.469 |
| Tanpa armada                        |        0.442 |
| Hanya jenis + waktu                 |        0.333 |

## 5. Sensitivitas terhadap definisi label

| Definisi                       |   prevalensi_uji |   PR_AUC |   lift_vs_acak |
|:-------------------------------|-----------------:|---------:|---------------:|
| > 10 menit                     |            0.432 |    0.629 |          1.457 |
| > 15 menit (utama)             |            0.194 |    0.471 |          2.428 |
| >= 15 menit (SPM dibaca "<15") |            0.339 |    0.49  |          1.444 |
| > 20 menit                     |            0.119 |    0.377 |          3.168 |
| > 15, tanpa outlier >180       |            0.165 |    0.268 |          1.622 |

"Lift" = PR-AUC / prevalensi (1,0 = sama dengan menebak acak).


Model akhir untuk aplikasi: Random Forest, dilatih pada seluruh 1135 event berlabel; ambang 0.431 (dari OOF). Tidak ada estimasi performa independen untuk model akhir selain hasil bagian 2.