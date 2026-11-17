Contoh kejadian uji pertama: jenis "Evakuasi Hewan Lain", pos "Pos Bintan Centre", Regu 7, jam 1.

Tabel: Kontribusi fitur aktif pada perhitungan skor satu kejadian (regresi logistik)

| Fitur aktif                     | Nilai x   | Koefisien   | x kali koefisien   |
|:--------------------------------|:----------|:------------|:-------------------|
| regu = Regu 7                   | 1,000     | 0,797       | 0,797              |
| blok = jam_Dini hari            | 1,000     | -0,702      | -0,702             |
| kelompok = Penyelamatan Hewan   | 1,000     | 0,446       | 0,446              |
| pos = Pos Bintan Centre         | 1,000     | 0,348       | 0,348              |
| jenis = Evakuasi Hewan Lain     | 1,000     | -0,168      | -0,168             |
| jam_sin                         | 0,570     | 0,152       | 0,087              |
| kelurahan = Batu IX             | 1,000     | 0,080       | 0,080              |
| armada = grup_Armada Dinas (BP) | 1,000     | 0,074       | 0,074              |

Jumlah seluruh kontribusi ditambah intersep (-0,613) menghasilkan z = 0,180; skor = 1 / (1 + e^(-z)) = **0,545** (cocok dengan keluaran model).
