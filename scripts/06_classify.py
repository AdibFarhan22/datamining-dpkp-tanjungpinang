"""Tahap 6: klasifikasi risiko keterlambatan respons (>15 menit).
Validasi berurutan waktu: 80% awal = latih/CV (TimeSeriesSplit), 20% akhir = uji. Tanpa kebocoran label."""
import sys
import warnings

import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings('ignore')
sys.path.insert(0, 'scripts')
from model_cfg import CAT, NUM, FEATURES, FORBIDDEN

assert not (set(FEATURES) & FORBIDDEN)
SEED = 42
df = pd.read_csv('data/siap_mining/klasifikasi.csv', parse_dates=['dt_diterima']).sort_values('dt_diterima').reset_index(drop=True)
df['jam_sin'] = np.sin(2 * np.pi * df.jam / 24)
df['jam_cos'] = np.cos(2 * np.pi * df.jam / 24)
df['hari'] = df.hari.astype(int).astype(str)
y = df.label_usulan.astype(int)
cut = int(len(df) * 0.8)
tr, te = df.iloc[:cut], df.iloc[cut:]
print(f'latih={len(tr)} ({tr.dt_diterima.min().date()}..{tr.dt_diterima.max().date()}) | uji={len(te)} ({te.dt_diterima.min().date()}..{te.dt_diterima.max().date()})')
print(f'prevalensi terlambat: latih={y.iloc[:cut].mean():.3f} uji={y.iloc[cut:].mean():.3f} ({int(y.iloc[cut:].sum())} positif di uji)')
out = ['# Hasil Klasifikasi Risiko Keterlambatan (scripts/06_classify.py)\n',
       f'- Latih/CV: {len(tr)} event ({tr.dt_diterima.min().date()} s/d {tr.dt_diterima.max().date()}); Uji (periode terakhir): {len(te)} event ({te.dt_diterima.min().date()} s/d {te.dt_diterima.max().date()}).',
       f'- Prevalensi terlambat: latih {y.iloc[:cut].mean():.1%}; uji {y.iloc[cut:].mean():.1%} ({int(y.iloc[cut:].sum())} kasus positif). **Dengan positif sesedikit ini, selang kepercayaan lebar.**\n']


def make_pre(cat, num):
    return ColumnTransformer([('c', OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=5), cat),
                              ('n', StandardScaler(), num)])


def models(cat=CAT, num=NUM):
    pre = lambda: make_pre(cat, num)
    return {
        'Baseline (prevalensi)': Pipeline([('p', pre()), ('m', DummyClassifier(strategy='prior'))]),
        'Regresi Logistik': Pipeline([('p', pre()), ('m', LogisticRegression(C=0.3, class_weight='balanced', max_iter=2000))]),
        'Random Forest': Pipeline([('p', pre()), ('m', RandomForestClassifier(n_estimators=400, min_samples_leaf=5, class_weight='balanced_subsample', random_state=SEED, n_jobs=-1))]),
        'Gradient Boosting': Pipeline([('p', pre()), ('m', GradientBoostingClassifier(n_estimators=150, max_depth=2, learning_rate=0.05, subsample=0.8, random_state=SEED))]),
    }


def metrics(yt, p, thr):
    pred = (p >= thr).astype(int)
    return dict(PR_AUC=average_precision_score(yt, p), ROC_AUC=roc_auc_score(yt, p), Precision=precision_score(yt, pred, zero_division=0),
                Recall=recall_score(yt, pred), F1=f1_score(yt, pred, zero_division=0))


# ---- CV berurutan waktu pada data latih
tscv = TimeSeriesSplit(n_splits=5)
cvrows, oof = [], {}
for name, mdl in models().items():
    pr, ro, pp = [], [], np.full(len(tr), np.nan)
    for a, b in tscv.split(tr):
        if y.iloc[a].nunique() < 2 or y.iloc[b].nunique() < 2:
            continue
        mdl.fit(tr.iloc[a][FEATURES], y.iloc[a])
        p = mdl.predict_proba(tr.iloc[b][FEATURES])[:, 1]
        pp[b] = p
        pr.append(average_precision_score(y.iloc[b], p)); ro.append(roc_auc_score(y.iloc[b], p))
    oof[name] = pp
    cvrows.append(dict(Model=name, CV_PR_AUC=np.mean(pr), SD_PR=np.std(pr), CV_ROC_AUC=np.mean(ro), lipatan=len(pr)))
cv = pd.DataFrame(cvrows).set_index('Model').round(3)
print(cv)
out += ['## 1. Validasi silang berurutan waktu (TimeSeriesSplit, 5 lipatan, hanya data latih)\n', cv.to_markdown(), '']
best = cv.drop('Baseline (prevalensi)').CV_PR_AUC.idxmax()
print('model terbaik menurut CV PR-AUC:', best)

# ---- ambang dari prediksi out-of-fold (BUKAN dari data uji)
m_ok = ~np.isnan(oof[best])
pr_, rc_, th_ = precision_recall_curve(y.iloc[:cut][m_ok], oof[best][m_ok])
f1s = 2 * pr_[:-1] * rc_[:-1] / np.maximum(pr_[:-1] + rc_[:-1], 1e-9)
thr = float(th_[f1s.argmax()])
print(f'ambang (maks F1 pada OOF) = {thr:.3f}')

# ---- evaluasi pada data uji
rows, probs = [], {}
for name, mdl in models().items():
    mdl.fit(tr[FEATURES], y.iloc[:cut])
    p = mdl.predict_proba(te[FEATURES])[:, 1]
    probs[name] = p
    t = thr if name == best else 0.5
    rows.append(dict(Model=name, **metrics(y.iloc[cut:], p, t)))
res = pd.DataFrame(rows).set_index('Model').round(3)
res.loc['Baseline (prevalensi)', ['ROC_AUC']] = 0.5
print(res)
prev = float(y.iloc[cut:].mean())
out += [f'## 2. Hasil pada data uji (periode terakhir)\n', f'Ambang untuk model terbaik ({best}) = {thr:.3f}, dipilih dari prediksi out-of-fold data latih. Model lain dievaluasi pada ambang 0,5 (hanya PR-AUC/ROC-AUC yang bebas ambang). PR-AUC baseline acak = prevalensi = {prev:.3f}.\n', res.to_markdown(), '']

# bootstrap
rng = np.random.default_rng(SEED)
yt = y.iloc[cut:].values
pb = probs[best]
boots = []
for _ in range(1000):
    i = rng.integers(0, len(yt), len(yt))
    if yt[i].sum() == 0:
        continue
    boots.append((average_precision_score(yt[i], pb[i]), roc_auc_score(yt[i], pb[i]), recall_score(yt[i], (pb[i] >= thr).astype(int))))
bt = np.array(boots)
ci = lambda k: f'{np.percentile(bt[:, k], 2.5):.3f} - {np.percentile(bt[:, k], 97.5):.3f}'
out += [f'**Selang kepercayaan 95% bootstrap ({best}, uji):** PR-AUC {ci(0)}; ROC-AUC {ci(1)}; Recall {ci(2)}. Lebar selang menunjukkan data uji kecil.\n']
cm = confusion_matrix(yt, (pb >= thr).astype(int))
out += ['Matriks konfusi (baris=aktual tepat waktu/terlambat, kolom=prediksi):\n', pd.DataFrame(cm, index=['aktual tepat', 'aktual terlambat'], columns=['prediksi tepat', 'prediksi terlambat']).to_markdown(), '']

# ---- permutation importance per variabel mentah (uji)
fitted = models()[best].fit(tr[FEATURES], y.iloc[:cut])
base = average_precision_score(yt, fitted.predict_proba(te[FEATURES])[:, 1])
imp = {}
for col in CAT + ['jam_sin', 'akhir_pekan']:
    d = []
    for _ in range(30):
        x = te[FEATURES].copy()
        if col == 'jam_sin':
            idx = rng.permutation(len(x)); x[['jam_sin', 'jam_cos']] = x[['jam_sin', 'jam_cos']].values[idx]
        else:
            x[col] = rng.permutation(x[col].values)
        d.append(base - average_precision_score(yt, fitted.predict_proba(x)[:, 1]))
    imp['jam (sin/cos)' if col == 'jam_sin' else col] = (np.mean(d), np.std(d))
imp = pd.DataFrame(imp, index=['turun_PR_AUC', 'sd']).T.sort_values('turun_PR_AUC', ascending=False).round(4)
out += ['## 3. Pentingnya variabel (permutation importance pada data uji; turunnya PR-AUC saat variabel diacak)\n', imp.to_markdown(),
        '\nCatatan: ini ukuran asosiasi prediktif, **bukan** sebab-akibat.\n']

# ---- ablasi
abl = []
for nm, drop in [('Semua fitur', []), ('Tanpa pos & regu', ['pos', 'regu']), ('Tanpa lokasi (kelurahan, kecamatan)', ['kelurahan', 'kecamatan']),
                 ('Tanpa armada', ['armada_grup']), ('Hanya jenis + waktu', ['kelurahan', 'kecamatan', 'pos', 'regu', 'armada_grup'])]:
    cat = [c for c in CAT if c not in drop]
    mm = models(cat, NUM)[best].fit(tr[cat + NUM], y.iloc[:cut])
    abl.append(dict(Skenario=nm, PR_AUC_uji=average_precision_score(yt, mm.predict_proba(te[cat + NUM])[:, 1])))
abl = pd.DataFrame(abl).set_index('Skenario').round(3)
out += ['## 4. Ablasi fitur (PR-AUC uji)\n', abl.to_markdown(), '']

# ---- sensitivitas batas label
raw = df.response_minutes
sens = []
for nm, lab in [('> 10 menit', raw > 10), ('> 15 menit (utama)', raw > 15), ('>= 15 menit (SPM dibaca "<15")', raw >= 15), ('> 20 menit', raw > 20),
                ('> 15, tanpa outlier >180', raw > 15)]:
    msk = (df.outlier_respons == 0) if 'outlier' in nm else pd.Series(True, index=df.index)
    d2, yy = df[msk], lab[msk].astype(int)
    c2 = int(len(d2) * 0.8)
    if yy.iloc[c2:].sum() == 0:
        continue
    mm = models()[best].fit(d2.iloc[:c2][FEATURES], yy.iloc[:c2])
    p2 = mm.predict_proba(d2.iloc[c2:][FEATURES])[:, 1]
    pv = yy.iloc[c2:].mean()
    sens.append(dict(Definisi=nm, prevalensi_uji=pv, PR_AUC=average_precision_score(yy.iloc[c2:], p2), lift_vs_acak=average_precision_score(yy.iloc[c2:], p2) / pv))
sens = pd.DataFrame(sens).set_index('Definisi').round(3)
out += ['## 5. Sensitivitas terhadap definisi label\n', sens.to_markdown(),
        '\n"Lift" = PR-AUC / prevalensi (1,0 = sama dengan menebak acak).\n']
print(sens)

# ---- gambar
plt.figure(figsize=(6.5, 5))
for name, p in probs.items():
    a, b, _ = precision_recall_curve(yt, p); plt.plot(b, a, label=f'{name} (AP={average_precision_score(yt, p):.2f})')
plt.axhline(prev, color='gray', ls=':', label=f'acak ({prev:.2f})'); plt.xlabel('Recall'); plt.ylabel('Precision'); plt.legend(fontsize=8)
plt.title('Kurva Precision-Recall (data uji)'); plt.tight_layout(); plt.savefig('figures/model_pr_curve.png', dpi=130); plt.close()
plt.figure(figsize=(7, 4)); plt.barh(imp.index[::-1], imp.turun_PR_AUC.values[::-1], xerr=imp.sd.values[::-1], color='#2E6F95')
plt.xlabel('turunnya PR-AUC saat diacak'); plt.title('Permutation importance'); plt.tight_layout(); plt.savefig('figures/model_importance.png', dpi=130); plt.close()
plt.figure(figsize=(4.5, 4)); plt.imshow(cm, cmap='Blues')
for (i, j), v in np.ndenumerate(cm): plt.text(j, i, v, ha='center', va='center', color='black')
plt.xticks([0, 1], ['tepat', 'terlambat']); plt.yticks([0, 1], ['tepat', 'terlambat']); plt.xlabel('prediksi'); plt.ylabel('aktual'); plt.title(best)
plt.tight_layout(); plt.savefig('figures/model_confusion.png', dpi=130); plt.close()

# ---- model akhir untuk aplikasi: dilatih pada seluruh data (latih+uji), ambang dari OOF
final = models()[best].fit(df[FEATURES], y)
joblib.dump(dict(model=final, threshold=thr, features=FEATURES, name=best, n_train=len(df)), 'models/model_terlambat.joblib')
out.append(f'\nModel akhir untuk aplikasi: {best}, dilatih pada seluruh {len(df)} event berlabel; ambang {thr:.3f} (dari OOF). Tidak ada estimasi performa independen untuk model akhir selain hasil bagian 2.')
open('reports/klasifikasi_hasil.md', 'w', encoding='utf-8').write('\n'.join(out))
print('selesai')
