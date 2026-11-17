"""Normalisasi kelurahan/kecamatan Kota Tanjungpinang dari teks laporan yang tidak konsisten."""
import re
import difflib

# kelurahan kanonik -> kecamatan (hirarki administrasi; diverifikasi dengan tabel silang data di LOG.md)
KEL2KEC = {
    'Batu IX': 'Tanjungpinang Timur', 'Pinang Kencana': 'Tanjungpinang Timur', 'Air Raja': 'Tanjungpinang Timur',
    'Melayu Kota Piring': 'Tanjungpinang Timur', 'Kampung Bulang': 'Tanjungpinang Timur',
    'Tanjung Ayun Sakti': 'Bukit Bestari', 'Dompak': 'Bukit Bestari', 'Tanjung Unggat': 'Bukit Bestari', 'Sei Jang': 'Bukit Bestari',
    'Senggarang': 'Tanjungpinang Kota', 'Kampung Bugis': 'Tanjungpinang Kota', 'Penyengat': 'Tanjungpinang Kota',
    'Tanjungpinang Kota': 'Tanjungpinang Kota',
    'Kampung Baru': 'Tanjungpinang Barat', 'Kemboja': 'Tanjungpinang Barat', 'Bukit Cermin': 'Tanjungpinang Barat',
    'Tanjungpinang Barat': 'Tanjungpinang Barat',
}
ALIAS = {
    'Batu IX': ['batu ix', 'batu 9', 'bt 9', 'bt ix', 'bt 1x', 'btu ix', 'bt9', 'baru ix', 'batu xl', 'batu xi', 'bt xi', 'batu lx', 'bt l9', 'ix', 'bt 10'],
    'Pinang Kencana': ['pinang kencana', 'pinangkencana', 'tanjungpinang kencana', 'tanjungpinang kencena'],
    'Air Raja': ['air raja'],
    'Melayu Kota Piring': ['melayu kota piring', 'kota piring', 'melau kota piring', 'melayu kita piring', 'melatu kota piring', 'mkp'],
    'Kampung Bulang': ['kampung bulang', 'kampung bolang', 'kp bulang', 'kamp bulang', 'kampung bolanga'],
    'Tanjung Ayun Sakti': ['tanjung ayun sakti', 'tanjung ayu sakti', 'tg ayun sakti', 'tanjung ayunsakti', 'tanjun ayun sakti', 'tanjung ayum sakti'],
    'Dompak': ['dompak'],
    'Tanjung Unggat': ['tanjung unggat', 'tg unggat', 'tanjungunggat'],
    'Sei Jang': ['sei jang', 'seijang', 'sungai jang', 'sei ajang', 'sel jang', 'sei ijang'],
    'Senggarang': ['senggarang'],
    'Kampung Bugis': ['kampung bugis', 'kp bugis'],
    'Penyengat': ['penyengat'],
    'Tanjungpinang Kota': ['tanjungpinang kota', 'tanjung pinang kota', 'tg pinang kota', 'tpi kota'],
    'Kampung Baru': ['kampung baru', 'kp baru', 'kampungbaru', 'kapnyng baru'],
    'Kemboja': ['kemboja', 'kamboja'],
    'Bukit Cermin': ['bukit cermin', 'bukit cetmin'],
    'Tanjungpinang Barat': ['tanjungpinang barat', 'tanjung pinang barat', 'tpi barat', 'tanjungpinangbarat', 'tg pinang barat'],
}
_A2K = {a: k for k, v in ALIAS.items() for a in v}
KEC_ONLY = {'tanjungpinang timur', 'tanjung pinang timur', 'tanjung pinang tinur', 'tanjung piang timur', 'kecamatan tanjungpinang timur',
            'kec tanjungpinang timur', 'bukit bestari', 'tpi timur'}
LUAR = 'Luar Kota/Lainnya'


def _n(s):
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', str(s).lower())).strip()


def normalize_kel(raw):
    """Return nama kelurahan kanonik, LUAR (di luar 17 kelurahan/tidak dikenal), atau None (kosong/ambigu)."""
    if raw is None or (isinstance(raw, float)):
        return None
    v = _n(raw)
    v = re.sub(r'^(kelurahan|kel)\s+', '', v)
    if not v or v in ('kecamatan', 'kondisi terkini'):
        return None
    if len(v) > 40:                       # kalimat kronologis salah masuk kolom
        return None
    if v in KEC_ONLY:
        return None                       # itu nama kecamatan, kelurahan tidak diketahui
    if v in _A2K:
        return _A2K[v]
    hits = {k for a, k in _A2K.items() if len(a) >= 5 and re.search(r'\b' + re.escape(a) + r'\b', v)}
    if len(hits) == 1:
        return hits.pop()
    if len(hits) > 1:
        return None                       # ambigu (mis. dua kelurahan disebut sekaligus)
    m = difflib.get_close_matches(v, list(_A2K), n=1, cutoff=0.82)
    return _A2K[m[0]] if m else LUAR


def normalize_kec(raw):
    """Return salah satu dari 4 kecamatan kota, LUAR, atau None."""
    if raw is None or isinstance(raw, float):
        return None
    v = _n(raw)
    v = re.sub(r'^(kecamatan|kec)\s+', '', v)
    if not v or v in ('waktu kejadian', 'lokasi kejadian', 'kecamatan'):
        return None
    if 'bintan' in v or 'toapaya' in v or v in ('karimun', 'patumbak', 'batu aji', 'lae parira', 'banguran batubi', 'buru'):
        return LUAR
    if 'bestari' in v or 'bukit' in v:
        return 'Bukit Bestari'
    if re.search(r'\bt(imur|inur)\b', v) or v.endswith('timur'):
        return 'Tanjungpinang Timur'
    if v.endswith('barat') or 'barat' in v:
        return 'Tanjungpinang Barat'
    if 'kota' in v and 'piring' not in v:
        return 'Tanjungpinang Kota'
    if 'melayu kota piring' in v:
        return 'Tanjungpinang Timur'
    return None


def resolve(kel_raw, kec_raw):
    """Return (kelurahan, kecamatan, sumber_kec). Kecamatan dilengkapi dari hirarki kelurahan bila teks kosong."""
    kel, kec = normalize_kel(kel_raw), normalize_kec(kec_raw)
    if kel in KEL2KEC:
        if kec is None:
            return kel, KEL2KEC[kel], 'turunan_kelurahan'
        if kec != KEL2KEC[kel]:           # konflik teks vs hirarki administrasi: hirarki dipakai, ditandai
            return kel, KEL2KEC[kel], 'koreksi_hirarki'
    return kel, kec, ('teks' if kec else 'kosong')
