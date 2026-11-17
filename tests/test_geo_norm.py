import sys
sys.path.insert(0, 'scripts')
from geo_norm import normalize_kel, normalize_kec, resolve, LUAR


def test_variants_map_to_canonical():
    assert normalize_kel('Batu 9') == normalize_kel('Bt IX') == normalize_kel('Kelurahan Batu IX') == 'Batu IX'
    assert normalize_kel('Seijang') == normalize_kel('Sungai Jang') == 'Sei Jang'
    assert normalize_kel('Tg. Ayun Sakti') == 'Tanjung Ayun Sakti'
    assert normalize_kel('Kamboja') == 'Kemboja'


def test_kecamatan_in_kelurahan_field_is_null_not_guess():
    assert normalize_kel('Tanjung Pinang Timur') is None
    assert normalize_kel('Kampung Bugis dan Pinang Kencana') is None     # ambigu


def test_sentence_and_out_of_city():
    assert normalize_kel('dengan membawa mesin robin dan 3 gulung selang ukuran 1 dan nozel ukuran 1 selanjutnya') is None
    assert normalize_kel('Sungai Panas') == LUAR
    assert normalize_kec('Bintan Timur') == LUAR


def test_kecamatan_variants_and_hierarchy_fill():
    assert normalize_kec('Tg.Pinang Timur') == 'Tanjungpinang Timur'
    assert normalize_kec('Tanjungpinang Bukit Bestari') == 'Bukit Bestari'
    assert resolve('Air Raja', None) == ('Air Raja', 'Tanjungpinang Timur', 'turunan_kelurahan')
    assert resolve(None, None) == (None, None, 'kosong')
    assert resolve('Batu IX', 'Bukit Bestari') == ('Batu IX', 'Tanjungpinang Timur', 'koreksi_hirarki')
    assert resolve('Batu IX', 'Tanjungpinang Timur') == ('Batu IX', 'Tanjungpinang Timur', 'teks')
