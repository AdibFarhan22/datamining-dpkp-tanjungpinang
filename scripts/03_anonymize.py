"""Tahap 3: anonimisasi -> data/mentah_anonim/events_mentah_anon.csv (boleh publik).
Peta pseudonim ke nama asli disimpan PRIVAT di data/raw_private/pseudonym_map.csv."""
import collections
import re
import sys

import pandas as pd

sys.path.insert(0, 'scripts')
from anon_lib import Pseudonymizer, name_tokens, scrub_text, leak_scan, norm_key

ev = pd.read_csv('data/raw_private/events_raw.csv')
geo = pd.read_csv('data/raw_private/events_geo.csv')
ev = ev.merge(geo[['event_id', 'lat', 'lon', 'pin_gap_min']], on='event_id', how='left')

is_hotline = ev.sender.str.lower().str.startswith('hotline')
sender_p, pelapor_p, alamat_p = Pseudonymizer('PTG', 3), Pseudonymizer('PLP'), Pseudonymizer('ALM')
ev['petugas_kode'] = [('AKUN_HOTLINE' if h else sender_p.code(s)) for s, h in zip(ev.sender, is_hotline)]
ev['pelapor_kode'] = ev.pelapor.map(pelapor_p.code)
ev['alamat_kode'] = ev.alamat.map(alamat_p.code)

# kata umum dan geografis tidak boleh dianggap nama orang
FREE = ['dampak', 'korban', 'kerugian', 'luas', 'armada', 'jenis_raw', 'kel_raw', 'kec_raw']
vocab = collections.Counter(w for c in FREE for v in ev[c].dropna() for w in set(norm_key(v).split()))
stop = {w for w, n in vocab.items() if n >= 5}
stop |= {'lurah', 'camat', 'bapak', 'ibu', 'pelapor', 'dinas', 'kota', 'tanjungpinang', 'pinang', 'kampung',
         'sungai', 'bukit', 'batu', 'air', 'raja', 'dompak', 'senggarang', 'penyengat', 'kemboja', 'kamboja'}
def is_generic(name):
    """Label generik ('Warga Sekitar', 'Pemilik Rumah'): seluruh katanya kosakata umum, bukan identitas orang."""
    ws = norm_key(name).split()
    return bool(ws) and all(w in stop for w in ws)


person_strings = [p for p in ev.pelapor.dropna().unique() if not is_generic(p)] + \
    list(ev.loc[~is_hotline, 'sender'].dropna().unique())
print('pelapor generik dikecualikan:', sorted({p for p in ev.pelapor.dropna().unique() if is_generic(p)})[:8])
tokens = name_tokens(person_strings, stop)
print('token nama yang dihapus dari teks bebas:', len(tokens))

redactions = 0
for c in FREE:
    res = ev[c].map(lambda x: scrub_text(x, tokens))
    ev[c] = res.map(lambda t: t[0])
    redactions += int(res.map(lambda t: t[1]).sum())
print('total redaksi pada teks bebas:', redactions)

ev['lat_r'] = ev.lat.round(3)
ev['lon_r'] = ev.lon.round(3)
ev['alamat_anon'] = ev.alamat_kode.fillna('ALM_NA') + ', ' + ev.kec_raw.fillna('-')
out_cols = ['event_id', 'msg_ts', 'tanggal', 'sumber_tanggal', 'dt_diterima', 'dt_tiba', 'dt_selesai', 'response_minutes',
            'petugas_kode', 'pelapor_kode', 'alamat_kode', 'alamat_anon', 'jenis_raw', 'kel_raw', 'kec_raw',
            'armada', 'regu', 'pos', 'dampak', 'korban', 'kerugian', 'luas', 'lat_r', 'lon_r', 'pin_gap_min']
pub = ev[out_cols].copy()
pub['pin_gap_min'] = pub.pin_gap_min.round(2)

# pemindai kebocoran sebelum menulis berkas publik
findings = leak_scan(pub, person_strings)
tok_hits = []
tokpat = re.compile(r'\b(?:' + '|'.join(re.escape(t) for t in tokens) + r')\b', re.I)
for c in FREE + ['alamat_anon']:      # kolom bebas-ketik; kolom lain berisi kode/kategori hasil parser
    tok_hits += [(c, i) for i, v in pub[c].dropna().items() if tokpat.search(str(v))]
print('temuan kebocoran pola/nama lengkap:', len(findings), '| temuan token nama:', len(tok_hits))
if findings or tok_hits:
    print(findings[:10], tok_hits[:10])
    sys.exit('GAGAL: masih ada data pribadi, berkas publik TIDAK ditulis')

pub.to_csv('data/mentah_anonim/events_mentah_anon.csv', index=False, encoding='utf-8-sig')
rows = []
for kind, p in (('petugas', sender_p), ('pelapor', pelapor_p), ('alamat', alamat_p)):
    rows += [(kind, p.originals[k], code) for k, code in p.map.items()]
pd.DataFrame(rows, columns=['jenis', 'asli', 'kode']).to_csv('data/raw_private/pseudonym_map.csv', index=False, encoding='utf-8-sig')
print(f'tertulis: {len(pub)} baris | petugas={len(sender_p.map)} pelapor={len(pelapor_p.map)} alamat={len(alamat_p.map)}')
print('event dengan titik (koordinat dibulatkan 3 desimal):', pub.lat_r.notna().sum())
