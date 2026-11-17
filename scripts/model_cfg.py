"""Konfigurasi fitur klasifikasi. Hanya informasi yang diketahui SAAT laporan diterima."""
CAT = ['jenis', 'kelompok', 'kecamatan', 'kelurahan', 'pos', 'regu', 'armada_grup', 'blok_jam', 'hari']
NUM = ['jam_sin', 'jam_cos', 'akhir_pekan']
FEATURES = CAT + NUM
# kolom hasil/akibat kejadian: dilarang jadi fitur (kebocoran label)
FORBIDDEN = {'dt_tiba', 'dt_selesai', 'response_minutes', 'durasi_tangani', 'label_usulan', 'label_final', 'outlier_respons'}
