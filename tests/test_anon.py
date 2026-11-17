import sys
sys.path.insert(0, 'scripts')
import pandas as pd
from anon_lib import Pseudonymizer, scrub_text, name_tokens, leak_scan


def test_same_entity_same_code_across_spellings():
    p = Pseudonymizer('PLP')
    a = p.code('Siti  Contoh')
    assert a == p.code('siti contoh') == p.code('SITI CONTOH.') and a == 'PLP0001'
    assert p.code('Budi Santoso') == 'PLP0002'
    assert p.code(None) is None and p.code('  ') is None


def test_scrub_removes_phone_email_rtrw_and_names():
    toks = name_tokens(['Budi Santoso'], stop=set())
    out, n = scrub_text('Hubungi Budi Santoso 0852-6413-9623 rt 004/002 budi@mail.com', toks)
    assert '0852' not in out and 'mail.com' not in out and 'Budi' not in out and '004' not in out and n >= 4


def test_stopwords_keep_place_names():
    toks = name_tokens(['Lurah Dompak Adriansyah'], stop={'dompak', 'lurah'})
    assert toks == {'adriansyah'}


def test_leak_scan_flags_name_and_phone_only_when_present():
    df = pd.DataFrame({'a': ['aman', 'telp 081234567890', 'rumah budi santoso']})
    f = leak_scan(df, ['Budi Santoso'])
    assert {x[1] for x in f} == {1, 2}
    assert leak_scan(pd.DataFrame({'a': ['aman', 'ALM0001, Batu IX']}), ['Budi Santoso']) == []
