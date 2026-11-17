Simpul akar berisi 908 kejadian latih: 126 terlambat dan 782 tepat waktu. Gini = 1 - (126/908)^2 - (782/908)^2 = **0,239**.

Pembelahan pertama memakai pertanyaan "jenis = Evakuasi Tawon/Lebah <= 0,50?" (untuk kolom satu-nol: 0 berarti kategori itu tidak ada). Cabang ya: 825 kejadian (95 terlambat), Gini 0,204. Cabang tidak: 83 kejadian (31 terlambat), Gini 0,468.

Gini tertimbang setelah belah = (825 x 0,204 + 83 x 0,468) / 908 = **0,228**, turun 0,011 dari 0,239. Pohon memilih pertanyaan dengan penurunan Gini terbesar.
