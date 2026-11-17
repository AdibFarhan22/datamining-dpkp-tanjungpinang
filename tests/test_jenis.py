import sys
sys.path.insert(0, 'scripts')
from jenis_norm import jenis_group


def test_species_before_object_rule():
    assert jenis_group('Evakuasi ular cincin emas')[0] == 'Evakuasi Ular'
    assert jenis_group('Evakuasi pelepasan cincin')[0] == 'Evakuasi Benda/Cincin'


def test_fire_subtypes():
    assert jenis_group('Kebakaran lahan yang di duga dari pembakaran sampah')[0] == 'Kebakaran Lahan'
    assert jenis_group('Kebakaran ruko jl raja haji')[0] == 'Kebakaran Bangunan'
    assert jenis_group('Kebakaran mobil')[0] == 'Kebakaran Kendaraan'
    assert jenis_group('Kebakaran')[1] == 'Kebakaran'


def test_animals_and_unknown():
    assert jenis_group('Evakuasi tawon vespa') == ('Evakuasi Tawon/Lebah', 'Penyelamatan Hewan')
    assert jenis_group('Evakuasi Kucing di dalam sumur')[1] == 'Penyelamatan Hewan'
    assert jenis_group(None) == ('Tidak Diketahui', 'Tidak Diketahui')
