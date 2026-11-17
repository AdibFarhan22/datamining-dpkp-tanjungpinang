"""Pengelompokan jenis kejadian dari teks bebas (197+ variasi ejaan) ke kategori terkontrol."""
import re

RULES = [  # urutan penting: aturan lebih spesifik lebih dulu ('ular cincin emas' adalah ular, bukan cincin)
    ('Evakuasi Ular', r'\b(ular|sanca|kobra|cobra|koros|weling|piton|python|ukar)\b'),
    ('Evakuasi Tawon/Lebah', r'(tawon|lebah|tabuan|vespa)'),
    ('Evakuasi Benda/Cincin', r'(cincin|kunci|gelang|terkunci|terjebak di jari|kurungan)'),
    ('Kebakaran Lahan', r'(lahan|semak|rumput|hutan|sampah|ilalang|kebun)'),
    ('Kebakaran Kendaraan', r'(kebakaran|terbakar).*(mobil|motor|kendaraan|kapal|truk|speed|pompong)'),
    ('Kebakaran Bangunan', r'(kebakaran|terbakar).*(rumah|ruko|gedung|bangunan|toko|kios|gudang|kantor|dapur|kos|warung|pasar|sekolah|hotel)'),
    ('Kebakaran Lainnya', r'(kebakaran|terbakar|api|korsleting|kompor)'),
    ('Evakuasi Hewan Lain', r'(biawak|monyet|kucing|anjing|buaya|burung|musang|kelelawar|hewan|kadal|ayam|sapi|kambing|babi|elang|landak|berang|tikus|kura)'),
    ('Penyelamatan Lainnya', r'(evakuasi|penyelamatan|rescue|tenggelam|pohon|tumbang|banjir|orang|korban|kecelakaan|longsor)'),
]
BESAR = {'Evakuasi Ular': 'Penyelamatan Hewan', 'Evakuasi Tawon/Lebah': 'Penyelamatan Hewan', 'Evakuasi Hewan Lain': 'Penyelamatan Hewan',
         'Evakuasi Benda/Cincin': 'Penyelamatan Lainnya', 'Penyelamatan Lainnya': 'Penyelamatan Lainnya',
         'Kebakaran Lahan': 'Kebakaran', 'Kebakaran Kendaraan': 'Kebakaran', 'Kebakaran Bangunan': 'Kebakaran', 'Kebakaran Lainnya': 'Kebakaran'}


def jenis_group(raw):
    """Return (kategori, kelompok_besar). Teks kosong/tak dikenal -> ('Tidak Diketahui', 'Tidak Diketahui')."""
    if raw is None or (isinstance(raw, float) and raw != raw):
        return 'Tidak Diketahui', 'Tidak Diketahui'
    t = re.sub(r'\s+', ' ', str(raw).lower())
    for name, pat in RULES:
        if re.search(pat, t):
            return name, BESAR[name]
    return 'Tidak Diketahui', 'Tidak Diketahui'
