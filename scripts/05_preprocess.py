"""Tahap 5: praproses -> data/siap_mining/*. Hanya membaca data/mentah_anonim."""
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, 'scripts')
from geo_norm import resolve, KEL2KEC
from jenis_norm import jenis_group
from prep_lib import fix_dates, armada_group, jam_blok, make_label, BATAS_MENIT

LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


ev = pd.read_csv('data/mentah_anonim/events_mentah_anon.csv')
log(f'input: {len(ev)} event')
if not ev.msg_ts.astype(str).str.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$').all():
    sys.exit('GAGAL: kolom msg_ts pada data/mentah_anonim/events_mentah_anon.csv tidak berformat YYYY-MM-DD HH:MM:SS. '
             'Berkas kemungkinan dibuka dan disimpan ulang di Excel (format tanggal berubah dan detik hilang). '
             'Ambil ulang berkas asli dari repositori (git checkout -- data/mentah_anonim) dan JANGAN menyimpannya dari Excel.')

# 1. koreksi tanggal salah ketik
ev, n_fix = fix_dates(ev)
log(f'koreksi tanggal (selisih >3 hari dari tanggal pesan): {n_fix} event')

# 2. waktu respons dihitung ulang dari datetime yang sudah dikoreksi; NULL tetap NULL
ev['response_minutes'] = (ev.dt_tiba - ev.dt_diterima).dt.total_seconds() / 60
neg = (ev.response_minutes < 0).sum()
ev.loc[ev.response_minutes < 0, 'response_minutes'] = np.nan
log(f'respons negatif dijadikan NULL: {neg}; respons valid: {ev.response_minutes.notna().sum()}')
ev['durasi_tangani'] = (ev.dt_selesai - ev.dt_tiba).dt.total_seconds() / 60
ev.loc[ev.durasi_tangani < 0, 'durasi_tangani'] = np.nan

# 3. normalisasi lokasi dan jenis
r = ev.apply(lambda x: resolve(x.kel_raw, x.kec_raw), axis=1, result_type='expand')
ev['kelurahan'], ev['kecamatan'], ev['sumber_kec'] = r[0], r[1], r[2]
ev['kelurahan'] = ev.kelurahan.fillna('Tidak diketahui')
ev['kecamatan'] = ev.kecamatan.fillna('Tidak diketahui')
log(f"kelurahan kanonik: {ev.kelurahan.isin(KEL2KEC).sum()} event | luar kota: {(ev.kelurahan == 'Luar Kota/Lainnya').sum()} | tidak diketahui: {(ev.kelurahan == 'Tidak diketahui').sum()}")
g = ev.jenis_raw.map(jenis_group)
ev['jenis'], ev['kelompok'] = g.map(lambda t: t[0]), g.map(lambda t: t[1])

# 4. fitur yang diketahui saat laporan masuk (TIDAK memakai dt_tiba/dt_selesai/response/durasi)
ev['pos'] = ev.pos.fillna('Tidak disebut')
ev['regu'] = ev.regu.map(lambda x: 'Tidak disebut' if pd.isna(x) else f'Regu {int(x)}')
ev['armada_grup'] = ev.armada.map(armada_group)
ev['jam'] = ev.dt_diterima.dt.hour
ev['blok_jam'] = ev.jam.map(jam_blok)
ev['hari'] = ev.dt_diterima.dt.dayofweek
ev['akhir_pekan'] = (ev.hari >= 5).astype(float).where(ev.dt_diterima.notna())

# 5. label (usulan otomatis; label_final dikosongkan menunggu pemeriksaan tim)
ev['label_usulan'] = ev.response_minutes.map(lambda x: make_label(x, BATAS_MENIT))
ev['label_final'] = np.nan
ev['outlier_respons'] = (ev.response_minutes > 180).astype(int)
log(f'label_usulan: 1={int((ev.label_usulan == 1).sum())} 0={int((ev.label_usulan == 0).sum())} NULL={int(ev.label_usulan.isna().sum())}; outlier >180 menit: {int(ev.outlier_respons.sum())}')
log(f'respons tepat 15 menit (dihitung tepat waktu): {int((ev.response_minutes == 15).sum())}')

FEATURES = ['jenis', 'kelompok', 'kecamatan', 'kelurahan', 'pos', 'regu', 'armada_grup', 'jam', 'blok_jam', 'hari', 'akhir_pekan']
kl = ev[ev.label_usulan.notna()].sort_values('dt_diterima').copy()
kl = kl[['event_id', 'dt_diterima', 'label_usulan', 'label_final', 'response_minutes', 'outlier_respons'] + FEATURES]
kl.to_csv('data/siap_mining/klasifikasi.csv', index=False, encoding='utf-8-sig')
log(f'klasifikasi.csv: {len(kl)} baris (event tanpa label valid dikeluarkan dari model, bukan diisi 0)')

# 6. titik spasial
gp = ev[ev.lat_r.notna()][['event_id', 'lat_r', 'lon_r', 'jenis', 'kelompok', 'blok_jam', 'kelurahan', 'kecamatan', 'response_minutes', 'label_usulan']]
gp.to_csv('data/siap_mining/titik_geo.csv', index=False, encoding='utf-8-sig')
log(f'titik_geo.csv: {len(gp)} baris, di antaranya berlabel: {int(gp.label_usulan.notna().sum())}')

# 7. profil kelurahan untuk klaster
k = ev[ev.kelurahan.isin(KEL2KEC)].copy()
k['malam'] = k.jam.isin(list(range(18, 24)) + list(range(0, 6))).astype(float).where(k.jam.notna())
span_bulan = max((ev.dt_diterima.max() - ev.dt_diterima[ev.dt_diterima >= '2025-04-01'].min()).days / 30.4, 1)
prof = k.groupby('kelurahan').agg(
    n_event=('event_id', 'size'), n_valid=('label_usulan', 'count'),
    share_kebakaran=('kelompok', lambda s: (s == 'Kebakaran').mean()),
    share_hewan=('kelompok', lambda s: (s == 'Penyelamatan Hewan').mean()),
    share_malam=('malam', 'mean'),
    median_respons=('response_minutes', 'median'),
    pct_terlambat=('label_usulan', 'mean'),
    median_tangani=('durasi_tangani', 'median')).reset_index()
prof['event_per_bulan'] = prof.n_event / span_bulan
prof['kecamatan'] = prof.kelurahan.map(KEL2KEC)
prof['layak_klaster'] = ((prof.n_event >= 10) & (prof.n_valid >= 8)).astype(int)
prof.round(4).to_csv('data/siap_mining/kelurahan_profil.csv', index=False, encoding='utf-8-sig')
log(f'kelurahan_profil.csv: {len(prof)} kelurahan, layak klaster (n_event>=10 dan n_valid>=8): {int(prof.layak_klaster.sum())}')

# 8. lampiran: seluruh event terproses (untuk EDA pasca-praproses)
ev.drop(columns=['kel_raw', 'kec_raw']).to_csv('data/siap_mining/events_bersih.csv', index=False, encoding='utf-8-sig')
open('reports/preprocess_log.txt', 'w', encoding='utf-8').write('\n'.join(LOG))
