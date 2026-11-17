"""Tahap 14: hitung bahan tambahan laporan (statistik, uji, contoh sebelum-sesudah, perhitungan model) dari data asli.
Keluaran: reports/extras/*.md (tabel siap sisip) dan figures/model_tree_ilustrasi.png. Semua angka berasal dari data, bukan ditulis tangan."""
import os
import re
import sys
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans, DBSCAN
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, silhouette_samples
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

warnings.filterwarnings('ignore')
sys.path.insert(0, 'scripts')
from geo_norm import resolve
from jenis_norm import jenis_group
from model_cfg import CAT, NUM, FEATURES

SEED = 42
OUT = 'reports/extras'
os.makedirs(OUT, exist_ok=True)


def comma(s):
    return re.sub(r'(?<=\d)\.(?=\d)', ',', s)


def th(n):
    """Pemisah ribuan titik: 1030 -> 1.030."""
    return f'{n:,}'.replace(',', '§')       # '§' diganti titik saat disimpan (agar tidak ikut diubah menjadi koma desimal)


def save(name, text):
    open(f'{OUT}/{name}.md', 'w', encoding='utf-8').write(text.strip().replace('§', '.') + '\n')


def tab(df, dec=1, **kw):
    """Markdown tabel dengan koma desimal. Bilangan bulat tetap bulat; desimal mengikuti floatfmt (mis. '.3f') atau dec."""
    fm = kw.pop('floatfmt', None)
    if fm:
        dec = int(re.search(r'\.(\d)f', fm)[1])
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: '' if pd.isna(x) else f'{x:.{dec}f}')
        elif pd.api.types.is_integer_dtype(d[c]):
            d[c] = d[c].astype(str)
    return comma(d.to_markdown(disable_numparse=True, **kw))


ev = pd.read_csv('data/siap_mining/events_bersih.csv', parse_dates=['dt_diterima', 'dt_tiba', 'dt_selesai'])
kl = pd.read_csv('data/siap_mining/klasifikasi.csv', parse_dates=['dt_diterima'])
v = ev[ev.label_usulan.notna()].copy()

# ---------- (a) ringkasan atribut ----------
rows = []
spec = [('dt_diterima', 'waktu'), ('dt_tiba', 'waktu'), ('dt_selesai', 'waktu'), ('response_minutes', 'numerik'), ('durasi_tangani', 'numerik'),
        ('jenis', 'kategorikal'), ('kelompok', 'kategorikal'), ('kelurahan', 'kategorikal'), ('kecamatan', 'kategorikal'), ('pos', 'kategorikal'),
        ('regu', 'kategorikal'), ('armada_grup', 'kategorikal'), ('jam', 'numerik'), ('hari', 'numerik'), ('lat_r', 'numerik'), ('lon_r', 'numerik'),
        ('label_usulan', 'biner')]
for c, t in spec:
    s = ev[c]
    n = int(s.notna().sum())
    if t == 'numerik':
        ring = f'min {s.min():.4g}; median {s.median():.4g}; maks {s.max():.4g}'
    elif t == 'waktu':
        ring = f'{s.min():%Y-%m-%d} s/d {s.max():%Y-%m-%d}'
    elif t == 'biner':
        ring = f'1 = {int((s == 1).sum())}; 0 = {int((s == 0).sum())}'
    else:
        vc = s.value_counts()
        ring = f'modus "{vc.index[0]}" ({vc.iloc[0]})'
    rows.append(dict(Atribut=c, Tipe=t, **{'Terisi': n, '% terisi': round(n / len(ev) * 100, 1), 'Nilai unik': int(s.nunique()), 'Ringkasan': ring}))
save('atribut', tab(pd.DataFrame(rows), index=False))

# ---------- (b) tabel statistik ----------
def grp(col, minn=1):
    g = v.groupby(col).agg(n=('label_usulan', 'size'), terlambat=('label_usulan', 'sum'), persen=('label_usulan', 'mean'),
                            median=('response_minutes', 'median'), p90=('response_minutes', lambda s: s.quantile(.9)))
    g['persen'] = (g.persen * 100).round(1)
    g['terlambat'] = g.terlambat.astype(int)
    g = g[g.n >= minn].sort_values('n', ascending=False).reset_index()
    g.columns = [col.capitalize(), 'n berlabel', 'Terlambat', '% terlambat', 'Median (menit)', 'P90 (menit)']
    return g


save('per_jenis', tab(grp('jenis'), index=False, floatfmt='.1f'))
save('per_kecamatan', tab(grp('kecamatan'), index=False, floatfmt='.1f'))
save('per_regu', tab(grp('regu'), index=False, floatfmt='.1f'))
save('per_armada', tab(grp('armada_grup'), index=False, floatfmt='.1f'))
d = ev.durasi_tangani.dropna()
ds = d.describe(percentiles=[.25, .5, .75, .9, .99])
dtab = pd.DataFrame({'Statistik': ds.index, 'Menit': [f'{int(x)}' if i == 'count' else f'{x:.1f}' for i, x in ds.items()]})
save('durasi', tab(dtab, index=False))
v['bulan'] = v.dt_diterima.dt.to_period('M').astype(str)
bm = v.groupby('bulan').agg(n=('label_usulan', 'size'), persen=('label_usulan', 'mean'), median=('response_minutes', 'median'))
bm = bm[bm.n >= 15]
bm['persen'] = (bm.persen * 100).round(1)
bm = bm.reset_index(); bm.columns = ['Bulan', 'n berlabel', '% terlambat', 'Median (menit)']
save('per_bulan', tab(bm, index=False, floatfmt='.1f'))

# ---------- (c) uji asosiasi chi-kuadrat ----------
res = []
for f in ['jenis', 'kelompok', 'pos', 'regu', 'armada_grup', 'blok_jam', 'kecamatan', 'kelurahan', 'hari']:
    s = kl[f].astype(str)
    s = s.where(s.map(s.value_counts()) >= 10, 'Lain-lain')
    ct = pd.crosstab(s, kl.label_usulan)
    chi, p, dof, _ = chi2_contingency(ct)
    cv = np.sqrt(chi / (ct.values.sum() * (min(ct.shape) - 1)))
    res.append(dict(Variabel=f, **{'chi-kuadrat': chi, 'db': dof, 'p-value': p, "Cramer's V": cv}))
r = pd.DataFrame(res).sort_values('p-value')
r['Signifikan (Bonferroni 0,0056)'] = np.where(r['p-value'] < 0.05 / len(r), 'ya', 'tidak')
r['p-value'] = r['p-value'].map(lambda x: f'{x:.4f}' if x >= 0.0001 else '< 0,0001')
r['chi-kuadrat'] = r['chi-kuadrat'].map(lambda x: f'{x:.1f}')
r["Cramer's V"] = r["Cramer's V"].map(lambda x: f'{x:.3f}')
save('chi2', tab(r, index=False))

# ---------- (e) contoh sebelum-sesudah ----------
mn = pd.read_csv('data/mentah_anonim/events_mentah_anon.csv')
rk = mn.kel_raw.dropna().map(lambda s: re.sub(r'\s+', ' ', s.strip()))
canon = rk.map(lambda s: resolve(s, None)[0])
t = pd.DataFrame({'raw': rk, 'kel': canon}).dropna()
t = t[t.kel.isin(['Batu IX', 'Pinang Kencana', 'Air Raja', 'Tanjung Ayun Sakti', 'Dompak', 'Senggarang', 'Sei Jang', 'Kampung Baru', 'Kemboja'])]
ex = t.groupby('kel').raw.agg(lambda s: s.str.lower().value_counts()).reset_index() if False else None
rows = []
for k, g in t.groupby('kel'):
    vc = g.raw.str.lower().value_counts()
    rows.append({'Kelurahan resmi': k, 'Jumlah ejaan berbeda': int(len(vc)), 'Contoh ejaan mentah (jumlah)': '; '.join(f'{a} ({b})' for a, b in vc.head(6).items())})
save('contoh_kelurahan', tab(pd.DataFrame(rows).sort_values('Jumlah ejaan berbeda', ascending=False), index=False))
sp = []
for raw in ['Tanjung Pinang Timur', 'Kampung Bugis dan Pinang Kencana', 'Sungai Panas', 'Kecamatan', 'Bt IX', 'tg unggat']:
    kel = resolve(raw, None)[0]
    sp.append({'Isi kolom kelurahan (mentah)': raw, 'Hasil': kel if kel else 'NULL'})
save('contoh_kelurahan_khusus', tab(pd.DataFrame(sp), index=False))
mn['kategori'] = mn.jenis_raw.map(lambda x: jenis_group(x)[0])
rows = []
for k, g in mn.groupby('kategori'):
    vc = g.jenis_raw.dropna().str.strip().str.lower().value_counts()
    rows.append({'Kategori': k, 'Jumlah ejaan mentah': int(len(vc)), 'Contoh isian mentah': '; '.join(vc.index[:3])})
save('contoh_jenis', tab(pd.DataFrame(rows).sort_values('Jumlah ejaan mentah', ascending=False), index=False))
fx = ev[ev.tanggal_dikoreksi == 1][['tanggal', 'msg_ts']].head(5).copy()
fx['tanggal terkoreksi'] = fx.msg_ts.str[:10]
fx['msg_ts'] = fx.msg_ts.str[:10]
fx.columns = ['Tanggal di teks laporan', 'Tanggal pesan dikirim', 'Tanggal terkoreksi']
save('contoh_tanggal', tab(fx, index=False))

# ---------- model (replikasi 06_classify) ----------
df = kl.sort_values('dt_diterima').reset_index(drop=True)
df['jam_sin'] = np.sin(2 * np.pi * df.jam / 24)
df['jam_cos'] = np.cos(2 * np.pi * df.jam / 24)
df['hari'] = df.hari.astype(int).astype(str)
y = df.label_usulan.astype(int)
cut = int(len(df) * 0.8)
tr, te = df.iloc[:cut], df.iloc[cut:]
ytr, yte = y.iloc[:cut], y.iloc[cut:]


def pre():
    return ColumnTransformer([('c', OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=5), CAT), ('n', StandardScaler(), NUM)])


def models():
    return {
        'Baseline': Pipeline([('p', pre()), ('m', DummyClassifier(strategy='prior'))]),
        'Regresi Logistik': Pipeline([('p', pre()), ('m', LogisticRegression(C=0.3, class_weight='balanced', max_iter=2000))]),
        'Random Forest': Pipeline([('p', pre()), ('m', RandomForestClassifier(n_estimators=400, min_samples_leaf=5, class_weight='balanced_subsample', random_state=SEED, n_jobs=-1))]),
        'Gradient Boosting': Pipeline([('p', pre()), ('m', GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=SEED))]),
    }


# (l) CV per lipatan
rows = []
for k, (a, b) in enumerate(TimeSeriesSplit(n_splits=5).split(tr), 1):
    row = {'Lipatan': k, 'n latih': len(a), 'n nilai': len(b), 'Prevalensi nilai (%)': f'{ytr.iloc[b].mean() * 100:.1f}'}
    for nm, m in models().items():
        m.fit(tr.iloc[a][FEATURES], ytr.iloc[a])
        row[nm] = round(average_precision_score(ytr.iloc[b], m.predict_proba(tr.iloc[b][FEATURES])[:, 1]), 3)
    rows.append(row)
save('cv_lipatan', tab(pd.DataFrame(rows), index=False, floatfmt='.3f'))

# (f) regresi logistik: koefisien dan contoh perhitungan
lr = models()['Regresi Logistik'].fit(tr[FEATURES], ytr)
names = lr.named_steps['p'].get_feature_names_out()
coef = pd.Series(lr.named_steps['m'].coef_[0], index=names)
clean = lambda s: s.replace('c__', '').replace('n__', '').replace('_', ' = ', 1) if s.startswith('c__') else s.replace('n__', '')
top = pd.concat([coef.sort_values(ascending=False).head(7), coef.sort_values().head(7)])
tk = pd.DataFrame({'Fitur': [clean(i) for i in top.index], 'Koefisien': top.values.round(3), 'Arah': ['naik' if x > 0 else 'turun' for x in top.values]})
save('lr_koefisien', tab(tk, index=False, floatfmt='.3f'))
x0 = te.iloc[[0]][FEATURES]
xt = lr.named_steps['p'].transform(x0)
xt = xt.toarray() if hasattr(xt, 'toarray') else xt
contrib = pd.Series(xt[0] * coef.values, index=names)
cz = lr.named_steps['m'].intercept_[0] + contrib.sum()
pz = 1 / (1 + np.exp(-cz))
assert abs(pz - lr.predict_proba(x0)[0, 1]) < 1e-9
nz = contrib[xt[0] != 0]
nz = nz.reindex(nz.abs().sort_values(ascending=False).index).head(8)
row0 = te.iloc[0]
ct = pd.DataFrame({'Fitur aktif': [clean(i) for i in nz.index], 'Nilai x': xt[0][[list(names).index(i) for i in nz.index]].round(3), 'Koefisien': coef[nz.index].values.round(3), 'x kali koefisien': nz.values.round(3)})
head = (f'Contoh kejadian uji pertama: jenis "{row0.jenis}", pos "{row0.pos}", {row0.regu}, jam {int(row0.jam)}.\n\n'
        'Tabel: Kontribusi fitur aktif pada perhitungan skor satu kejadian (regresi logistik)\n\n' +
        tab(ct, index=False, floatfmt='.3f') +
        f'\n\nJumlah seluruh kontribusi ditambah intersep ({lr.named_steps["m"].intercept_[0]:.3f}) menghasilkan z = {cz:.3f}; ' +
        f'skor = 1 / (1 + e^(-z)) = **{pz:.3f}** (cocok dengan keluaran model).')
save('lr_contoh', comma(head))

# (g) pohon keputusan ilustrasi + Gini
P = pre().fit(tr[FEATURES])
Xtr = P.transform(tr[FEATURES]); Xtr = Xtr.toarray() if hasattr(Xtr, 'toarray') else Xtr
fn = [clean(i) for i in P.get_feature_names_out()]
dt = DecisionTreeClassifier(max_depth=3, min_samples_leaf=30, random_state=SEED).fit(Xtr, ytr)
fig = plt.figure(figsize=(19, 7.5))
plot_tree(dt, feature_names=fn, class_names=['tepat', 'terlambat'], filled=True, rounded=True, fontsize=8, impurity=True, proportion=False)
plt.title('Pohon keputusan ilustrasi (kedalaman 3), bukan model akhir')
plt.tight_layout(); plt.savefig('figures/model_tree_ilustrasi.png', dpi=110); plt.close()
tr_ = dt.tree_


def counts(i):
    val = tr_.value[i][0]
    return np.round(val * tr_.n_node_samples[i]) if abs(val.sum() - 1) < 1e-6 else val


g0 = lambda c: 1 - (c[0] / c.sum()) ** 2 - (c[1] / c.sum()) ** 2
r0, l0, rr0 = counts(0), counts(tr_.children_left[0]), counts(tr_.children_right[0])
wg = (l0.sum() * g0(l0) + rr0.sum() * g0(rr0)) / r0.sum()
gtxt = (f'Simpul akar berisi {int(r0.sum())} kejadian latih: {int(r0[1])} terlambat dan {int(r0[0])} tepat waktu. '
        f'Gini = 1 - ({int(r0[1])}/{int(r0.sum())})^2 - ({int(r0[0])}/{int(r0.sum())})^2 = **{g0(r0):.3f}**.\n\n'
        f'Pembelahan pertama memakai pertanyaan "{fn[tr_.feature[0]]} <= {tr_.threshold[0]:.2f}?" '
        f'(untuk kolom satu-nol: 0 berarti kategori itu tidak ada). Cabang ya: {int(l0.sum())} kejadian ({int(l0[1])} terlambat), Gini {g0(l0):.3f}. '
        f'Cabang tidak: {int(rr0.sum())} kejadian ({int(rr0[1])} terlambat), Gini {g0(rr0):.3f}.\n\n'
        f'Gini tertimbang setelah belah = ({int(l0.sum())} x {g0(l0):.3f} + {int(rr0.sum())} x {g0(rr0):.3f}) / {int(r0.sum())} = **{wg:.3f}**, '
        f'turun {g0(r0) - wg:.3f} dari {g0(r0):.3f}. Pohon memilih pertanyaan dengan penurunan Gini terbesar.')
save('gini', comma(gtxt))

# (j) kalibrasi dan (k) analisis kesalahan (Random Forest, ambang 0,431)
rf = models()['Random Forest'].fit(tr[FEATURES], ytr)
pr = rf.predict_proba(te[FEATURES])[:, 1]
print('cek PR-AUC uji RF:', round(average_precision_score(yte, pr), 3))
bins = pd.cut(pr, [0, .2, .4, .6, 1.0001], right=False, labels=['0,0-0,2', '0,2-0,4', '0,4-0,6', '0,6-1,0'])
cal = pd.DataFrame({'bin': bins, 'p': pr, 'y': yte.values}).groupby('bin', observed=True).agg(n=('y', 'size'), prediksi=('p', 'mean'), aktual=('y', 'mean')).reset_index()
cal.columns = ['Rentang skor', 'n uji', 'Rata-rata skor', 'Proporsi terlambat sebenarnya']
save('kalibrasi', tab(cal.round(3), index=False, floatfmt='.3f'))
thr = 0.431
tt = te.assign(p=pr, y=yte.values)
tt['pred'] = (tt.p >= thr).astype(int)
def err(col):
    g = tt.groupby(col).apply(lambda d: pd.Series({'n': len(d), 'Terlambat': int(d.y.sum()), 'Tertangkap (TP)': int(((d.pred == 1) & (d.y == 1)).sum()),
                                                   'Alarm palsu (FP)': int(((d.pred == 1) & (d.y == 0)).sum()), 'Terlewat (FN)': int(((d.pred == 0) & (d.y == 1)).sum())}))
    g['n'] = g.n.astype(int)
    g['Recall (%)'] = (g['Tertangkap (TP)'] / g['Terlambat'].replace(0, np.nan) * 100).round(0)
    g['Precision (%)'] = (g['Tertangkap (TP)'] / (g['Tertangkap (TP)'] + g['Alarm palsu (FP)']).replace(0, np.nan) * 100).round(0)
    return g.sort_values('n', ascending=False).reset_index().rename(columns={col: col.capitalize()})
save('kesalahan_pos', tab(err('pos'), index=False))
save('kesalahan_kelompok', tab(err('kelompok'), index=False))

# ---------- (m) evakuasi tawon/lebah: pola waktu dan sensitivitas model ----------
tw = v[v.jenis == 'Evakuasi Tawon/Lebah']
buck = pd.DataFrame({'Rentang respons': ['<= 15 menit', '16-60 menit', '61-180 menit', '> 180 menit'],
                     'Jumlah': [int((tw.response_minutes <= 15).sum()), int(((tw.response_minutes > 15) & (tw.response_minutes <= 60)).sum()),
                                int(((tw.response_minutes > 60) & (tw.response_minutes <= 180)).sum()), int((tw.response_minutes > 180).sum())]})
save('tawon_rentang', tab(buck, index=False))
late_tw = tw[tw.response_minutes > 60]
hr = late_tw.dt_tiba.dt.hour.value_counts().sort_index()
save('tawon_jam_tiba', tab(pd.DataFrame({'Jam tiba': [f'{h:02d}:00-{h:02d}:59' for h in hr.index], 'Jumlah': hr.values.astype(int)}), index=False))
out_all = v[v.outlier_respons == 1]
save('outlier_jenis', tab(out_all.jenis.value_counts().rename_axis('Jenis').reset_index(name='Jumlah'), index=False))
save('tawon_fakta', comma(f'Dari {len(tw)} evakuasi tawon/lebah berlabel, {int(tw.label_usulan.sum())} ({tw.label_usulan.mean() * 100:.1f}%) terlambat; '
                          f'median jam laporan diterima untuk yang responsnya > 60 menit adalah pukul {late_tw.dt_diterima.dt.hour.median():.0f}:00. '
                          f'Tanpa tawon/lebah, tingkat terlambat seluruh data turun menjadi {v[v.jenis != "Evakuasi Tawon/Lebah"].label_usulan.mean() * 100:.1f}% '
                          f'({th(len(v[v.jenis != "Evakuasi Tawon/Lebah"]))} kejadian). Tawon/lebah menyumbang {tw.label_usulan.sum() / v.label_usulan.sum() * 100:.1f}% dari seluruh kejadian terlambat.'))
df2 = df[df.jenis != 'Evakuasi Tawon/Lebah'].reset_index(drop=True)
y2 = df2.label_usulan.astype(int)
c2 = int(len(df2) * 0.8)
m2 = models()['Random Forest'].fit(df2.iloc[:c2][FEATURES], y2.iloc[:c2])
p2 = m2.predict_proba(df2.iloc[c2:][FEATURES])[:, 1]
pv2 = y2.iloc[c2:].mean()
ap2 = average_precision_score(y2.iloc[c2:], p2)
save('tanpa_tawon', comma(f'Random Forest dilatih ulang tanpa evakuasi tawon/lebah ({th(len(df2))} kejadian; latih {c2}, uji {len(df2) - c2}, {int(y2.iloc[c2:].sum())} kasus terlambat di uji): '
                          f'prevalensi uji {pv2 * 100:.1f}%, PR-AUC **{ap2:.3f}**, lift terhadap acak {ap2 / pv2:.2f}.'))
print('tanpa tawon:', round(ap2, 3), round(pv2, 3))

# ---------- (h) K-Means, silhouette, DBSCAN ----------
g = pd.read_csv('data/siap_mining/hasil_klaster_titik.csv')
lat0, lon0 = g.lat_r.median(), g.lon_r.median()
X = np.c_[(g.lon_r - lon0) * 111.32 * np.cos(np.radians(lat0)), (g.lat_r - lat0) * 110.57]
km = KMeans(3, n_init=20, random_state=SEED).fit(X)
assert (km.labels_ == g.klaster_kmeans.values).all(), 'klaster tidak cocok dengan 07_cluster'
cen = km.cluster_centers_
rows = []
for k in range(3):
    m = km.labels_ == k
    rows.append({'Klaster': k, 'n titik': int(m.sum()), 'Pusat lintang': f'{lat0 + cen[k][1] / 110.57:.4f}', 'Pusat bujur': f'{lon0 + cen[k][0] / (111.32 * np.cos(np.radians(lat0))):.4f}',
                 'Jarak rata-rata ke pusat (km)': f'{np.linalg.norm(X[m] - cen[k], axis=1).mean():.2f}'})
save('kmeans_pusat', tab(pd.DataFrame(rows), index=False, floatfmt='.4f'))
i = 0
own = km.labels_[i]
dist = np.linalg.norm(X - X[i], axis=1)
a = dist[(km.labels_ == own) & (np.arange(len(X)) != i)].mean()
bs = {k: dist[km.labels_ == k].mean() for k in range(3) if k != own}
b = min(bs.values())
s_i = (b - a) / max(a, b)
assert abs(s_i - silhouette_samples(X, km.labels_)[i]) < 1e-9
sil = (f'Contoh titik ke-1 (klaster {own}): jarak rata-rata ke titik lain dalam klaster **a = {a:.2f} km**; jarak rata-rata ke klaster terdekat lain **b = {b:.2f} km**. '
       f's = (b - a) / max(a, b) = ({b:.2f} - {a:.2f}) / {max(a, b):.2f} = **{s_i:.3f}**. Nilai rata-rata seluruh titik (k = 3) adalah 0,446.')
save('silhouette_contoh', comma(sil))
nb = int((dist <= 1.0).sum() - 1)
save('dbscan_contoh', comma(f'Contoh: titik ke-1 memiliki **{nb} tetangga** dalam radius 1 km. Karena {nb} >= minPts (4), titik itu adalah titik inti dan menjadi pusat satu klaster kepadatan.'))
print('selesai:', sorted(os.listdir(OUT)))
