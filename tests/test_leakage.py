import sys
sys.path.insert(0, 'scripts')
import pandas as pd
from model_cfg import FEATURES, FORBIDDEN


def test_no_outcome_columns_used_as_features():
    assert not (set(FEATURES) & FORBIDDEN)


def test_label_is_binary_with_no_null_in_training_file():
    df = pd.read_csv('data/siap_mining/klasifikasi.csv')
    assert set(df.label_usulan.unique()) <= {0.0, 1.0} and df.label_usulan.notna().all()
    assert df.label_final.isna().all()                 # label_final menunggu pemeriksaan tim, tidak diisi otomatis
    assert df.dt_diterima.is_monotonic_increasing is True or df.dt_diterima.astype(str).is_monotonic_increasing


def test_label_matches_rule():
    df = pd.read_csv('data/siap_mining/klasifikasi.csv')
    assert ((df.response_minutes > 15).astype(float) == df.label_usulan).all()
