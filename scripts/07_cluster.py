"""Tahap 7: klasterisasi. (A) titik spasial 207 event bertitik; (B) profil 16 kelurahan. Eksploratif, tanpa label."""
import sys
import warnings

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.stats import chi2_contingency
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')
SEED = 42
out = ['# Hasil Klasterisasi (scripts/07_cluster.py)\n']
P = out.append

# =============== A. KLASTER TITIK SPASIAL ===============
g = pd.read_csv('data/siap_mining/titik_geo.csv')
lat0, lon0 = g.lat_r.median(), g.lon_r.median()
g['x_km'] = (g.lon_r - lon0) * 111.32 * np.cos(np.radians(lat0))
g['y_km'] = (g.lat_r - lat0) * 110.57
X = g[['x_km', 'y_km']].values
P(f'## A. Klaster titik spasial\n\nJumlah titik: **{len(g)}** dari 1.280 event unik (16,2%). Koordinat dibulatkan 3 desimal (~110 m). Hasil hanya mewakili event yang pinnya berhasil ditautkan, bukan seluruh kejadian.\n')

rows = []
for k in range(2, 9):
    km = KMeans(k, n_init=20, random_state=SEED).fit(X)
    rows.append(dict(k=k, silhouette=silhouette_score(X, km.labels_), davies_bouldin=davies_bouldin_score(X, km.labels_), inersia=km.inertia_))
kmt = pd.DataFrame(rows).set_index('k').round(3)
P('### A1. K-Means: pemilihan k\n'); P(kmt.to_markdown()); P('')
kbest = int(kmt.silhouette.idxmax())
km = KMeans(kbest, n_init=20, random_state=SEED).fit(X)
g['klaster_kmeans'] = km.labels_
# stabilitas: ARI antar bootstrap
rng = np.random.default_rng(SEED)
aris = []
for _ in range(50):
    i = rng.integers(0, len(X), len(X))
    kb = KMeans(kbest, n_init=10, random_state=int(rng.integers(1e6))).fit(X[i])
    aris.append(adjusted_rand_score(km.labels_, kb.predict(X)))
P(f'k terpilih (silhouette tertinggi) = **{kbest}**; stabilitas bootstrap (ARI rata-rata, 1 = sangat stabil) = **{np.mean(aris):.2f}**.\n')

rows = []
for eps in (0.5, 0.75, 1.0, 1.5, 2.0):
    for ms in (4, 6, 8):
        lab = DBSCAN(eps=eps, min_samples=ms).fit_predict(X)
        nc = len(set(lab)) - (1 if -1 in lab else 0)
        sil = silhouette_score(X[lab != -1], lab[lab != -1]) if nc >= 2 and (lab != -1).sum() > nc else np.nan
        rows.append(dict(eps_km=eps, min_samples=ms, n_klaster=nc, noise_persen=(lab == -1).mean() * 100, silhouette=sil))
dbt = pd.DataFrame(rows).round(3)
P('### A2. DBSCAN: grid parameter\n'); P(dbt.to_markdown(index=False)); P('')
ok = dbt[(dbt.n_klaster >= 2) & (dbt.noise_persen <= 30)]
if len(ok):
    b = ok.sort_values('silhouette', ascending=False).iloc[0]
    g['klaster_dbscan'] = DBSCAN(eps=b.eps_km, min_samples=int(b.min_samples)).fit_predict(X)
    P(f'DBSCAN terpilih (silhouette tertinggi, noise <= 30%): eps={b.eps_km} km, min_samples={int(b.min_samples)} -> {int(b.n_klaster)} klaster, noise {b.noise_persen:.1f}%.\n')
else:
    g['klaster_dbscan'] = -1
    P('Tidak ada konfigurasi DBSCAN dengan >=2 klaster dan noise <= 30%: titik tidak membentuk kepadatan yang terpisah jelas.\n')


def prof(col):
    d = g.copy()
    r = d.groupby(col).agg(n=('event_id', 'size'), n_berlabel=('label_usulan', 'count'), pct_terlambat=('label_usulan', 'mean'),
                           median_respons=('response_minutes', 'median'),
                           pct_kebakaran=('kelompok', lambda s: (s == 'Kebakaran').mean()),
                           kelurahan_dominan=('kelurahan', lambda s: s.value_counts().index[0])).round(3)
    return r


P('### A3. Profil klaster K-Means\n'); pk = prof('klaster_kmeans'); P(pk.to_markdown()); P('')
lab = g.dropna(subset=['label_usulan'])
chi_p = chi2_contingency(pd.crosstab(lab.klaster_kmeans, lab.label_usulan))[1]
P(f'Uji chi-kuadrat proporsi terlambat antar klaster K-Means: p = **{chi_p:.3f}** ' + ('(ada perbedaan signifikan pada alpha 5%).\n' if chi_p < .05 else '(tidak signifikan pada alpha 5%: tidak ada bukti bahwa klaster spasial berbeda tingkat keterlambatannya).\n'))
if g.klaster_dbscan.nunique() > 1:
    P('### A4. Profil klaster DBSCAN (-1 = noise)\n'); P(prof('klaster_dbscan').to_markdown()); P('')

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
sc = ax[0].scatter(g.lon_r, g.lat_r, c=g.klaster_kmeans, cmap='tab10', s=18); ax[0].set_title(f'K-Means (k={kbest})')
ax[1].scatter(g.lon_r, g.lat_r, c=g.klaster_dbscan, cmap='tab10', s=18); ax[1].set_title('DBSCAN (ungu/biru tua = noise -1)')
for a in ax: a.set_xlabel('longitude'); a.set_ylabel('latitude')
plt.tight_layout(); plt.savefig('figures/cluster_titik.png', dpi=130); plt.close()
g.drop(columns=['x_km', 'y_km']).to_csv('data/siap_mining/hasil_klaster_titik.csv', index=False, encoding='utf-8-sig')

# =============== B. KLASTER PROFIL KELURAHAN ===============
p = pd.read_csv('data/siap_mining/kelurahan_profil.csv')
p = p[p.layak_klaster == 1].reset_index(drop=True)
M = 10   # penyusutan empiris: kelurahan n kecil ditarik ke rata-rata global agar tidak noisy
glob = (p.pct_terlambat * p.n_valid).sum() / p.n_valid.sum()
p['terlambat_susut'] = (p.pct_terlambat * p.n_valid + glob * M) / (p.n_valid + M)
p['log_volume'] = np.log1p(p.event_per_bulan)
FT = ['log_volume', 'share_kebakaran', 'share_malam', 'median_respons', 'terlambat_susut', 'median_tangani']
Z = StandardScaler().fit_transform(p[FT])
P(f'\n## B. Klaster profil kelurahan\n\n{len(p)} kelurahan layak (n_event>=10; Penyengat dikeluarkan: 1 event). Fitur: {", ".join(FT)} (distandardisasi). Persentase terlambat disusutkan ke rata-rata global ({glob:.3f}) dengan bobot {M} agar kelurahan kecil tidak terlalu berisik. **Hanya 16 baris: temuan eksploratif.**\n')
rows = []
for k in range(2, 6):
    km2 = KMeans(k, n_init=50, random_state=SEED).fit(Z)
    hc = fcluster(linkage(Z, 'ward'), k, 'maxclust')
    rows.append(dict(k=k, silhouette_kmeans=silhouette_score(Z, km2.labels_), DB=davies_bouldin_score(Z, km2.labels_),
                     silhouette_ward=silhouette_score(Z, hc), ARI_kmeans_vs_ward=adjusted_rand_score(km2.labels_, hc)))
bt = pd.DataFrame(rows).set_index('k').round(3)
P('### B1. Pemilihan k\n'); P(bt.to_markdown()); P('')
kb = int(bt.silhouette_kmeans.idxmax())
km2 = KMeans(kb, n_init=50, random_state=SEED).fit(Z)
p['klaster'] = km2.labels_
aris = []
for _ in range(100):
    i = rng.choice(len(Z), len(Z), replace=True)
    if len(set(i)) < kb + 1:
        continue
    kk = KMeans(kb, n_init=10, random_state=int(rng.integers(1e6))).fit(Z[i])
    aris.append(adjusted_rand_score(km2.labels_, kk.predict(Z)))
P(f'k terpilih = **{kb}**; stabilitas bootstrap ARI = **{np.mean(aris):.2f}**.\n')
cp = p.groupby('klaster').agg(n_kelurahan=('kelurahan', 'size'), event_per_bulan=('event_per_bulan', 'mean'), share_kebakaran=('share_kebakaran', 'mean'),
                              share_malam=('share_malam', 'mean'), median_respons=('median_respons', 'mean'), pct_terlambat=('pct_terlambat', 'mean'),
                              median_tangani=('median_tangani', 'mean'), anggota=('kelurahan', lambda s: ', '.join(s))).round(3)
P('### B2. Profil klaster kelurahan\n'); P(cp.to_markdown()); P('')
p.round(4).to_csv('data/siap_mining/hasil_klaster_kelurahan.csv', index=False, encoding='utf-8-sig')

plt.figure(figsize=(9, 4.5)); dendrogram(linkage(Z, 'ward'), labels=p.kelurahan.values, leaf_rotation=70); plt.title('Dendrogram Ward (profil kelurahan)')
plt.tight_layout(); plt.savefig('figures/cluster_dendrogram.png', dpi=130); plt.close()
plt.figure(figsize=(7, 5.5)); plt.scatter(p.event_per_bulan, p.terlambat_susut * 100, c=p.klaster, cmap='tab10', s=70)
for _, r in p.iterrows(): plt.annotate(r.kelurahan, (r.event_per_bulan, r.terlambat_susut * 100), fontsize=7, xytext=(3, 3), textcoords='offset points')
plt.xlabel('event per bulan'); plt.ylabel('% terlambat (disusutkan)'); plt.title('Profil kelurahan: volume vs keterlambatan'); plt.tight_layout()
plt.savefig('figures/cluster_kelurahan.png', dpi=130); plt.close()
open('reports/klaster_hasil.md', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
