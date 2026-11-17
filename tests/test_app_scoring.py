import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))
from scoring import load_model, score, build_row, JENIS, KELURAHAN, POS, REGU, ARMADA


def test_row_matches_training_columns():
    b = load_model()
    row = build_row('Evakuasi Ular', 'Batu IX', 'Pos Dompak', 'Regu 6', 'Mobil Rescue', 14, 2)
    assert set(b['features']) <= set(row.columns) and row.kecamatan.iloc[0] == 'Tanjungpinang Timur'


def test_score_in_unit_interval_for_all_categories():
    b = load_model()
    for j in JENIS:
        r = score(b, jenis=j, kelurahan=KELURAHAN[0], pos=POS[0], regu=REGU[0], armada_grup=ARMADA[0], jam=3, hari=6)
        assert 0.0 <= r['prob'] <= 1.0


def test_tingkat_boundaries():
    from scoring import tingkat
    assert tingkat(0.60, 0.431) == 'tinggi' and tingkat(0.599, 0.431) == 'perhatian'
    assert tingkat(0.431, 0.431) == 'perhatian' and tingkat(0.4309, 0.431) == 'rendah' and tingkat(0.0, 0.431) == 'rendah'


def test_demo_scenarios_cover_three_levels():
    b = load_model()
    base = dict(jenis='Evakuasi Ular', kelurahan='Batu IX', armada_grup='Mobil Rescue', hari=2)
    tinggi = score(b, pos='Pos Dompak', regu='Regu 6', jam=14, **base)
    perhatian = score(b, pos='Pos Dompak', regu='Regu 4', jam=14, **base)
    rendah = score(b, pos='Mako SKB', regu='Regu 2', jam=3, **base)
    assert (tinggi['tingkat'], perhatian['tingkat'], rendah['tingkat']) == ('tinggi', 'perhatian', 'rendah')
    assert round(tinggi['prob'] * 100) == 60 and round(perhatian['prob'] * 100) == 50 and round(rendah['prob'] * 100) == 12


def test_unseen_combination_does_not_crash():
    r = score(load_model(), jenis='Kebakaran Kendaraan', kelurahan='Penyengat', pos='Pos Senggarang', regu='Regu 12', armada_grup='Lainnya', jam=23, hari=0)
    assert 0.0 <= r['prob'] <= 1.0
