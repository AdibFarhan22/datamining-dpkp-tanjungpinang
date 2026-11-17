import sys
sys.path.insert(0, 'scripts')
import pandas as pd
from prep_lib import fix_dates, armada_group, jam_blok, make_label


def test_label_boundary_and_null():
    assert make_label(15) == 0.0 and make_label(15.5) == 1.0 and make_label(0) == 0.0
    assert make_label(float('nan')) != make_label(float('nan'))      # NaN tetap NaN, bukan 0
    assert make_label(None) != 0.0


def test_fix_dates_year_typo_shifts_all_times():
    df = pd.DataFrame(dict(msg_ts=['2025-05-01 10:02:25', '2025-05-01 10:00:00'], tanggal=['2024-05-01', '2025-05-01'],
                           dt_diterima=['2024-05-01 09:00', '2025-05-01 09:00'], dt_tiba=['2024-05-01 09:10', None],
                           dt_selesai=[None, None]))
    out, n = fix_dates(df)
    assert n == 1 and out.dt_diterima.iloc[0] == pd.Timestamp('2025-05-01 09:00') and out.dt_tiba.iloc[0] == pd.Timestamp('2025-05-01 09:10')
    assert out.tanggal_dikoreksi.tolist() == [1, 0] and pd.isna(out.dt_tiba.iloc[1])


def test_armada_and_blok():
    assert armada_group('Mobil rescue') == 'Mobil Rescue'
    assert armada_group('Armada BP 9124 A') == 'Armada Dinas (BP)'
    assert armada_group('3 unit sepeda motor pribadi') == 'Kendaraan Pribadi'
    assert armada_group('mobil rescue dan motor pribadi') == 'Campuran'
    assert armada_group(None) == 'Tidak disebut'
    assert [jam_blok(h) for h in (0, 6, 12, 23)] == ['Dini hari', 'Pagi', 'Siang', 'Malam']
    assert jam_blok(float('nan')) == 'Tidak diketahui'
