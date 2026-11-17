import sys, datetime as dt
sys.path.insert(0, 'scripts')
from extract_lib import parse_report
D = dt.date(2025, 4, 16)

def rep(terima, tiba, selesai='01.05'):
    return f"LAPORAN KEJADIAN\nEvakuasi ular sanca\nLOKASI KEJADIAN\nAlamat : Jl. A\nKel: Batu IX\nKec: Tanjungpinang Timur\nWaktu kejadian:\nHari / Tanggal : Rabu / 16 April 2025\nTerima Laporan : {terima} WIB\n{tiba}\nSelesai : {selesai} WIB\n"

def test_tiba_variants():
    assert parse_report(rep('00.30', 'Regu Sampai di Lokasi : 00.40 WIB'), D)['response_minutes'] == 10
    assert parse_report(rep('19:15', 'Regu Tiba di Lokasi : 19.28WIB'), D)['response_minutes'] == 13
    assert parse_report(rep('08.00', 'Hadir : 08.20'), D)['response_minutes'] == 20

def test_tiba_missing_is_null_not_zero():
    r = parse_report(rep('20.44', 'Regu Tiba di Lokasi : WIB'), D)
    assert r['response_minutes'] is None and r['dt_tiba'] is None

def test_midnight_crossing():
    assert parse_report(rep('23.55', 'Tiba di Lokasi : 00.05'), D)['response_minutes'] == 10

def test_invalid_clock_is_null():
    assert parse_report(rep('10.00', 'Tiba di Lokasi : 27.99'), D)['response_minutes'] is None

def test_fields():
    r = parse_report(rep('10.00', 'Tiba di Lokasi : 10.05'), D)
    assert r['kel_raw'] == 'Batu IX' and r['kec_raw'] == 'Tanjungpinang Timur' and r['tanggal'] == '2025-04-16'

def test_date_on_next_line_and_misspelling():
    from extract_lib import parse_date
    assert parse_date("Hari / Tanggal : Rabu,\n 16 April 2025", None)[0] == dt.date(2025, 4, 16)
    assert parse_date("Hari / Tanggal : minggu 09 febuari 2026", None)[0] == dt.date(2026, 2, 9)
    assert parse_date("tidak ada tanggal", D) == (D, 'tanggal_pesan')


SEC = ("*Armada yang digunakan* : \n- Mobil rescue \n\n*Dampak*\nMengganggu warga\n\n*Korban Jiwa*\n- \n\n"
       "*Kerugian Materi*\nNihil\n\n*Kronologis* \nPelapor menelepon\n\n*PERSONIL PIKET*\nRegu 3 ( Mako SKB) \n"
       "*Diinformasikan oleh:* _REGU XI Pos Senggarang\n")


def test_sections_do_not_bleed_into_next_heading():
    from extract_lib import section
    assert section(SEC, r'armada') == 'Mobil rescue'
    assert section(SEC, r'dampak') == 'Mengganggu warga'
    assert section(SEC, r'korban') is None            # hanya '-'
    assert section(SEC, r'kerugian') == 'Nihil'


def test_jenis_after_long_title_line():
    from extract_lib import parse_report
    t = "LAPORAN KEJADIAN EVAKUASI DAN PENYELAMATAN*\n\nEvakuasi kunci mobil yg tertinggal\n\nPelapor*\nNama : x\n"
    assert parse_report(t, D)['jenis_raw'] == 'Evakuasi kunci mobil yg tertinggal'
    assert parse_report("LAPORAN KEJADIAN\nPelapor*\nNama : x\n", D)['jenis_raw'] is None


def test_regu_roman_and_pos():
    from extract_lib import parse_regu_pos
    assert parse_regu_pos(SEC) == (11, 'Pos Senggarang')
    assert parse_regu_pos("*Diinformasikan oleh:* Regu 8 Pos Bintan Centre") == (8, 'Pos Bintan Centre')
    assert parse_regu_pos("*Diinformasikan oleh:* Regu 2 Mako Suka Berenang") == (2, 'Mako SKB')
    assert parse_regu_pos("*Diinformasikan oleh:* Dinas Pemadam") == (None, None)
