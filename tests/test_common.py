import sys, tempfile, os
sys.path.insert(0, 'scripts')
from common import read_messages

def _read(txt):
    f = tempfile.NamedTemporaryFile('w', delete=False, suffix='.txt', encoding='utf-8'); f.write(txt); f.close()
    try: return read_messages(f.name)
    finally: os.unlink(f.name)

def test_lrm_prefixed_and_empty_text_lines_start_new_message():
    txt = ("[26/04/25, 18.40.00] A: LAPORAN KEJADIAN\nbaris dua\n"
           "[26/04/25, 18.51.29] Petugas Contoh:\n"
           "\u200e[26/04/25, 18.51.30] Petugas Contoh: \u200eimage omitted\n"
           "[26/04/25, 19.29.42] B: halo\n")
    m = _read(txt)
    assert [x['sender'] for x in m] == ['A', 'Petugas Contoh', 'Petugas Contoh', 'B']
    assert 'Petugas Contoh' not in m[0]['text'] and 'baris dua' in m[0]['text']
