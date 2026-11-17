"""Tahap 4: Exploratory Data Analysis. Hanya membaca data/mentah_anonim (reproducible dari GitHub).
Keluaran: figures/eda_*.png dan reports/eda_ringkasan.md."""
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, 'scripts')
from geo_norm import resolve
from jenis_norm import jenis_group

SRC = 'data/mentah_anonim/events_mentah_anon.csv'
ev = pd.read_csv(SRC, parse_dates=['dt_diterima', 'dt_tiba', 'dt_selesai'])
r = ev.apply(lambda x: resolve(x.kel_raw, x.kec_raw), axis=1, result_type='expand')
ev['kel'], ev['kec'] = r[0], r[1]
g = ev.jenis_raw.map(jenis_group)
ev['jenis'], ev['kelompok'] = g.map(lambda t: t[0]), g.map(lambda t: t[1])
ev['late'] = np.where(ev.response_minutes.isna(), np.nan, (ev.response_minutes > 15).astype(float))
ev['bulan'] = ev.dt_diterima.dt.to_period('M').astype(str)
ev['jam'] = ev.dt_diterima.dt.hour
ev['hari'] = ev.dt_diterima.dt.dayofweek
ev['durasi_tangani'] = (ev.dt_selesai - ev.dt_tiba).dt.total_seconds() / 60
v = ev[ev.response_minutes.notna()]
out = []
P = out.append
P('# Ringkasan EDA (otomatis dari scripts/04_eda.py)\n')
P(f'- Event unik: **{len(ev)}**; rentang terima: {ev.dt_diterima.min()} s/d {ev.dt_diterima.max()}')
P(f'- Event dengan respons valid: **{len(v)}** ({len(v) / len(ev):.1%}); NULL: {len(ev) - len(v)}')
P(f'- Label terlambat (>15 menit): **{int(v.late.sum())}** ({v.late.mean():.1%}) ; tepat waktu {int((1 - v.late).sum())}')
P(f'- Event bertitik (pin): {ev.lat_r.notna().sum()} ({ev.lat_r.notna().mean():.1%})\n')
P('## Statistik waktu respons (menit)\n')
P(v.response_minutes.describe(percentiles=[.25, .5, .75, .9, .95, .99]).round(2).to_frame('nilai').to_markdown())
P(f'\n- Respons 0 menit: {(v.response_minutes == 0).sum()} | >60: {(v.response_minutes > 60).sum()} | >180: {(v.response_minutes > 180).sum()}')
P(f'- Skewness: {v.response_minutes.skew():.2f}; skewness log1p: {np.log1p(v.response_minutes).skew():.2f}\n')
P('## Missing value per kolom (persen)\n')
P((ev[['dt_diterima', 'dt_tiba', 'dt_selesai', 'response_minutes', 'jenis_raw', 'kel', 'kec', 'pos', 'regu', 'armada', 'lat_r']]
   .isna().mean() * 100).round(1).to_frame('%NULL').to_markdown())
P('\n## Jenis kejadian (kategori)\n')
P(ev.jenis.value_counts().to_frame('n').assign(persen=lambda d: (d.n / d.n.sum() * 100).round(1)).to_markdown())
P('\n## Terlambat per kelompok jenis\n')
P(v.groupby('kelompok').agg(n=('late', 'size'), terlambat=('late', 'sum'), persen=('late', 'mean'), median_menit=('response_minutes', 'median')).round(3).to_markdown())
P('\n## Terlambat per pos jaga\n')
P(v.assign(pos=v.pos.fillna('Tidak disebut')).groupby('pos').agg(n=('late', 'size'), persen=('late', 'mean'), median_menit=('response_minutes', 'median')).round(3).to_markdown())
P('\n## Terlambat per kecamatan\n')
P(v.assign(kec=v.kec.fillna('Tidak diketahui')).groupby('kec').agg(n=('late', 'size'), persen=('late', 'mean'), median_menit=('response_minutes', 'median')).round(3).to_markdown())
P('\n## Terlambat per jam terima (blok)\n')
v = v.assign(blok=pd.cut(v.jam, [-1, 5, 11, 17, 23], labels=['00-05', '06-11', '12-17', '18-23']))
P(v.groupby('blok', observed=True).agg(n=('late', 'size'), persen=('late', 'mean'), median_menit=('response_minutes', 'median')).round(3).to_markdown())
P('\n## Laporan per bulan\n')
P(ev.bulan.value_counts().sort_index().to_frame('n').to_markdown())
open('reports/eda_ringkasan.md', 'w', encoding='utf-8').write('\n'.join(out))


def save(name):
    plt.tight_layout()
    plt.savefig(f'figures/eda_{name}.png', dpi=130)
    plt.close()


C = '#2E6F95'
# 1 per bulan
m = ev.bulan.value_counts().sort_index()
plt.figure(figsize=(10, 4)); plt.bar(m.index, m.values, color=C); plt.xticks(rotation=60); plt.ylabel('jumlah event')
plt.title('Jumlah laporan kejadian per bulan'); save('01_per_bulan')
# 2 jenis
j = ev.jenis.value_counts()
plt.figure(figsize=(8, 5)); plt.barh(j.index[::-1], j.values[::-1], color=C); plt.xlabel('jumlah event'); plt.title('Kategori jenis kejadian'); save('02_jenis')
# 3 histogram respons
plt.figure(figsize=(9, 4)); x = v.response_minutes.clip(upper=90)
plt.hist(x, bins=np.arange(0, 92, 2), color=C); plt.axvline(15, color='crimson', ls='--', label='batas SPM 15 menit')
plt.xlabel('waktu respons (menit, dipotong di 90)'); plt.ylabel('event'); plt.legend(); plt.title('Distribusi waktu respons (miring ke kanan)'); save('03_hist_respons')
# 4 boxplot per kelompok jenis (log)
fig, ax = plt.subplots(figsize=(9, 4.5)); grp = [d.response_minutes.clip(lower=0.5).values for _, d in v.groupby('jenis') if len(d) >= 15]
lab = [k for k, d in v.groupby('jenis') if len(d) >= 15]
ax.boxplot(grp, vert=False, labels=lab); ax.set_xscale('log'); ax.axvline(15, color='crimson', ls='--'); ax.set_xlabel('menit (skala log)')
ax.set_title('Waktu respons per kategori jenis'); save('04_box_jenis')
# 5 persen terlambat per pos
p = v.assign(pos=v.pos.fillna('Tidak disebut')).groupby('pos').late.agg(['mean', 'size'])
plt.figure(figsize=(7, 4)); plt.bar(p.index, p['mean'] * 100, color=C)
for i, (a, n) in enumerate(zip(p['mean'] * 100, p['size'])): plt.text(i, a + .5, f'n={n}', ha='center', fontsize=8)
plt.ylabel('% terlambat'); plt.xticks(rotation=20); plt.title('Persentase terlambat per pos jaga'); save('05_terlambat_pos')
# 6 heatmap jam x hari
h = ev.dropna(subset=['dt_diterima']).pivot_table(index='hari', columns='jam', values='event_id', aggfunc='count').reindex(range(7)).reindex(columns=range(24)).fillna(0)
plt.figure(figsize=(10, 3.6)); plt.imshow(h.values, aspect='auto', cmap='Blues'); plt.colorbar(label='event')
plt.yticks(range(7), ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']); plt.xticks(range(24)); plt.xlabel('jam terima'); plt.title('Event per hari x jam'); save('06_heatmap_jam_hari')
# 7 kelurahan teratas
k = ev.kel.value_counts().head(17)
plt.figure(figsize=(8, 5)); plt.barh(k.index[::-1], k.values[::-1], color=C); plt.xlabel('event'); plt.title('Event per kelurahan (setelah normalisasi)'); save('07_kelurahan')
# 8 missing
ms = (ev[['dt_diterima', 'dt_tiba', 'dt_selesai', 'jenis_raw', 'kel', 'kec', 'pos', 'regu', 'armada', 'lat_r']].isna().mean() * 100).sort_values()
plt.figure(figsize=(8, 4)); plt.barh(ms.index, ms.values, color='#C0504D'); plt.xlabel('% NULL'); plt.title('Missing value per kolom'); save('08_missing')
# 9 respons vs durasi penanganan (outlier)
d = ev.dropna(subset=['response_minutes', 'durasi_tangani']); d = d[(d.durasi_tangani >= 0)]
plt.figure(figsize=(6, 5)); plt.scatter(d.response_minutes.clip(lower=.5), d.durasi_tangani.clip(lower=.5), s=8, alpha=.4, color=C)
plt.xscale('log'); plt.yscale('log'); plt.axvline(15, color='crimson', ls='--'); plt.xlabel('respons (menit)'); plt.ylabel('durasi tangani (menit)')
plt.title('Respons vs durasi penanganan'); save('09_respons_vs_durasi')
# 10 peta titik
gp = ev.dropna(subset=['lat_r', 'response_minutes'])
plt.figure(figsize=(6.5, 6)); col = np.where(gp.late == 1, 'crimson', C)
plt.scatter(gp.lon_r, gp.lat_r, c=col, s=14, alpha=.7); plt.xlabel('longitude'); plt.ylabel('latitude')
plt.title(f'Titik kejadian tertaut pin (n={len(gp)}); merah = terlambat'); save('10_peta_titik')
# 11 terlambat per bulan
tb = v.groupby('bulan').late.agg(['mean', 'size'])
plt.figure(figsize=(10, 4)); plt.plot(tb.index, tb['mean'] * 100, marker='o', color='crimson'); plt.xticks(rotation=60)
plt.ylabel('% terlambat'); plt.title('Tren persentase terlambat per bulan'); save('11_tren_terlambat')
print('selesai; ringkasan di reports/eda_ringkasan.md; gambar:', len(__import__('glob').glob('figures/eda_*.png')))
