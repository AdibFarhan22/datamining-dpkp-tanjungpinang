"""Parser satu pesan 'LAPORAN KEJADIAN' -> dict field terstruktur."""
import re
from datetime import datetime, timedelta
from common import parse_time

BULAN = {'januari': 1, 'februari': 2, 'maret': 3, 'april': 4, 'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
         'september': 9, 'oktober': 10, 'november': 11, 'desember': 12, 'agu': 8, 'agt': 8, 'sept': 9, 'okt': 10,
         'des': 12, 'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'nov': 11, 'peb': 2, 'nop': 11,
         'agust': 8, 'febuari': 2, 'pebruari': 2, 'nopember': 11, 'ags': 8}
TERIMA = r'terima\s+laporan'
TIBA = r'(?:regu\s+)?(?:tiba|sampai|hadir)(?:\s+di)?(?:\s+lokasi|\s+tkp)?'
SELESAI = r'selesai(?:\s+(?:evakuasi|pemadaman|penanganan|kegiatan))?'

ROMAN = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10, 'xi': 11, 'xii': 12}
HEADS = (r'(?:armada|dampak|korban|kerugian|luas|penyebab|kronologis|personil|anggota\s+tambahan|tindakan|'
         r'kondisi|pemilik|sekian|diinformasikan|pelapor|lokasi|waktu|nomor)')


def section(text, head_pat):
    """Isi satu bagian laporan (setelah judul bagian sampai judul berikutnya); None bila kosong atau hanya '-'."""
    m = re.search(r'^[ \t*]*' + head_pat + r'(?P<rest>[^\n]*)', text, re.I | re.M)
    if not m:
        return None
    rest = m['rest']
    first = re.sub(r'^[^:*]*[*:]', '', rest, count=1) if re.search(r'[*:]', rest) else ''
    lines = [first]
    for line in text[m.end():].split('\n')[1:]:
        if re.match(r'^[ \t]*\*?[ \t]*' + HEADS + r'\b', line, re.I) or re.match(r'^[ \t]*\*[A-Za-z]', line):
            break
        lines.append(line)
    out = ' '.join(x.strip(' *:-\t_') for x in lines if x.strip(' *:-\t_')).strip()
    return out or None


def parse_regu_pos(text):
    """Regu (1-12) dan pos jaga dari 'Diinformasikan oleh: Regu ... Pos ...' atau blok PERSONIL PIKET."""
    m = (re.search(r'diinformasikan\s+oleh\**\s*:?\**\s*_?([^\n]*)', text, re.I)
         or re.search(r'PERSONIL\s+PIKET\**\s*\n([^\n]*\n?[^\n]*)', text, re.I))
    if not m:
        return None, None
    seg = m[1].lower()
    r = re.search(r'regu\s*0*(\d{1,2}|[ivx]{1,4})\b', seg)
    regu = None
    if r:
        regu = int(r[1]) if r[1].isdigit() else ROMAN.get(r[1])
        if regu is not None and not 1 <= regu <= 12:
            regu = None
    if re.search(r'suka\s*berenang|skb|mako', seg):
        pos = 'Mako SKB'
    elif re.search(r'bintan\s*cent', seg):
        pos = 'Pos Bintan Centre'
    elif 'dompak' in seg:
        pos = 'Pos Dompak'
    elif 'senggarang' in seg:
        pos = 'Pos Senggarang'
    else:
        pos = None
    return regu, pos


def parse_date(text, fallback):
    """Tanggal laporan dari 'Hari/Tanggal : kamis/ 7 Agustus 2025'; fallback ke tanggal pesan (date)."""
    m = re.search(r'tanggal\s*:?[^\d]{0,40}?(\d{1,2})\s*[-/ ]?\s*([A-Za-z]+)\.?\s*[-/ ]?\s*(\d{4})', text, re.I)
    if m:
        mon = BULAN.get(m[2].lower())
        try:
            if mon:
                return datetime(int(m[3]), mon, int(m[1])).date(), 'teks'
        except ValueError:
            pass
    return fallback, 'tanggal_pesan'


def _field(block, pat):
    m = re.search(pat + r'\s*\**\s*[:.]\s*\**\s*([^\n]*)', block, re.I)
    v = m[1].strip(' *\t') if m else ''
    return v or None


def parse_report(text, msg_date):
    """text: isi pesan. msg_date: datetime.date pesan. Waktu tidak valid -> None (bukan 0)."""
    jm = re.search(r'LAPORAN\s+KEJADIAN[^\n]*\n+\s*\**([^\n]+)', text, re.I)
    jenis = jm[1].strip(' *') if jm else None
    if jenis and re.match(r'(?i)^(pelapor|nama|alamat)\b', jenis):
        jenis = None                      # judul tanpa baris jenis: baris berikutnya sudah bagian Pelapor
    parts = re.split(r'LOKASI\s+KEJADIAN', text, maxsplit=1, flags=re.I)
    pel_block = parts[0]
    lok_block = re.split(r'waktu\s+kejadian', parts[1], maxsplit=1, flags=re.I)[0] if len(parts) > 1 else ''
    alamat = _field(lok_block, r'alamat')
    if not alamat and lok_block:
        first = [x.strip(' *:-\t') for x in lok_block.split('\n') if x.strip(' *:-\t')]
        alamat = first[0] if first else None
    kel = _field(lok_block, r'kel(?:urahan)?(?:/desa)?') or _field(text, r'kel(?:urahan)?(?:/desa)?')
    kec = _field(lok_block, r'kec(?:amatan)?') or _field(text, r'kec(?:amatan)?')
    d, dsrc = parse_date(text, msg_date)
    t_terima, t_tiba = parse_time(text, TERIMA), parse_time(text, TIBA)
    t_selesai = parse_time(text, SELESAI)

    def dt(minutes, base):
        return None if minutes is None else datetime.combine(base, datetime.min.time()) + timedelta(minutes=minutes)

    dt_terima = dt(t_terima, d)
    dt_tiba = dt(t_tiba, d)
    if dt_terima and dt_tiba and (dt_tiba - dt_terima).total_seconds() < -12 * 3600:
        dt_tiba += timedelta(days=1)          # lewat tengah malam
    dt_selesai = dt(t_selesai, d)
    if dt_tiba and dt_selesai and dt_selesai < dt_tiba and (dt_tiba - dt_selesai).total_seconds() > 12 * 3600:
        dt_selesai += timedelta(days=1)
    resp = None
    if dt_terima and dt_tiba:
        r = (dt_tiba - dt_terima).total_seconds() / 60
        resp = r if r >= 0 else None          # negatif = data salah -> NULL
    regu, pos = parse_regu_pos(text)
    return dict(jenis_raw=jenis, pelapor=_field(pel_block, r'nama'), alamat=alamat, kel_raw=kel, kec_raw=kec,
                tanggal=d.isoformat(), sumber_tanggal=dsrc, dt_diterima=dt_terima, dt_tiba=dt_tiba,
                dt_selesai=dt_selesai, response_minutes=resp,
                armada=section(text, r'armada'), regu=regu, pos=pos, dampak=section(text, r'dampak'),
                korban=section(text, r'korban'), kerugian=section(text, r'kerugian'), luas=section(text, r'luas'))
