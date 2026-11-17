"""Logika skor risiko keterlambatan (terpisah dari UI agar bisa diuji)."""
import os
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from geo_norm import KEL2KEC          # noqa: E402
from jenis_norm import BESAR          # noqa: E402
from prep_lib import jam_blok         # noqa: E402

JENIS = list(BESAR) + ['Tidak Diketahui']
POS = ['Mako SKB', 'Pos Bintan Centre', 'Pos Dompak', 'Pos Senggarang', 'Tidak disebut']
ARMADA = ['Mobil Rescue', 'Armada Dinas (BP)', 'Kendaraan Pribadi', 'Campuran', 'Tidak disebut', 'Lainnya']
REGU = [f'Regu {i}' for i in range(1, 13)] + ['Tidak disebut']
KELURAHAN = sorted(KEL2KEC) + ['Tidak diketahui']


def load_model(path=None):
    return joblib.load(path or os.path.join(ROOT, 'models', 'model_terlambat.joblib'))


def build_row(jenis, kelurahan, pos, regu, armada_grup, jam, hari):
    """Satu baris fitur persis seperti saat pelatihan. hari: 0=Senin..6=Minggu."""
    return pd.DataFrame([dict(
        jenis=jenis, kelompok=BESAR.get(jenis, 'Tidak Diketahui'), kecamatan=KEL2KEC.get(kelurahan, 'Tidak diketahui'),
        kelurahan=kelurahan, pos=pos, regu=regu, armada_grup=armada_grup, blok_jam=jam_blok(jam), hari=str(int(hari)),
        jam_sin=float(np.sin(2 * np.pi * jam / 24)), jam_cos=float(np.cos(2 * np.pi * jam / 24)), akhir_pekan=float(hari >= 5))])


TINGGI = 0.60   # skor >= 0,60: pada data uji 70% kejadian benar-benar terlambat (n = 20); skor 0,2-0,6 hanya 15-17% (reports Bab V.3)


def tingkat(p, ambang):
    """Tingkat risiko dari skor: 'tinggi' (>= 0,60), 'perhatian' (ambang model sampai < 0,60), 'rendah' (< ambang)."""
    if p >= TINGGI:
        return 'tinggi'
    return 'perhatian' if p >= ambang else 'rendah'


def score(bundle, **kw):
    """Return dict(prob, tingkat, flag_berisiko, ambang). prob = skor relatif, bukan probabilitas terkalibrasi."""
    x = build_row(**kw)[bundle['features']]
    p = float(bundle['model'].predict_proba(x)[0, 1])
    amb = bundle['threshold']
    return dict(prob=p, tingkat=tingkat(p, amb), flag_berisiko=p >= amb, ambang=amb)
