"""Anonimisasi: pseudonim konsisten, pembersih teks bebas, dan pemindai kebocoran."""
import re

PHONE = re.compile(r'(?<!\d)(?:\+?62|0)[\s.\-]?\d{2,4}[\s.\-]?\d{3,4}[\s.\-]?\d{2,5}(?!\d)')
LONGDIGITS = re.compile(r'(?<!\d)\d{9,}(?!\d)')
EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.]+')
RTRW = re.compile(r'\b(?:rt|rw)\s*[./:]?\s*\d+(?:\s*/\s*(?:rt|rw)?\s*\d+)?', re.I)


def norm_key(s):
    """Kunci kanonik entitas: huruf kecil, hanya huruf/angka, spasi dirapikan."""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 ]', ' ', str(s).lower())).strip()


class Pseudonymizer:
    """Kode samaran konsisten: entitas sama (kunci kanonik sama) selalu mendapat kode yang sama."""

    def __init__(self, prefix, width=4):
        self.prefix, self.width, self.map = prefix, width, {}
        self.originals = {}

    def code(self, value):
        if value is None or (isinstance(value, float) and value != value):
            return None
        k = norm_key(value)
        if not k:
            return None
        if k not in self.map:
            self.map[k] = f"{self.prefix}{len(self.map) + 1:0{self.width}d}"
            self.originals[k] = str(value)
        return self.map[k]


def name_tokens(names, stop):
    """Token nama (>=4 huruf) yang aman dihapus dari teks bebas; kata umum/geografis (stop) dikecualikan."""
    toks = set()
    for n in names:
        for t in norm_key(n).split():
            if len(t) >= 4 and t.isalpha() and t not in stop:
                toks.add(t)
    return toks


def scrub_text(s, tokens):
    """Hapus telepon, email, RT/RW, dan token nama dari teks bebas. Return (teks_bersih, jumlah_redaksi)."""
    if s is None or (isinstance(s, float) and s != s):
        return None, 0
    out, n = str(s), 0
    for pat, rep in ((EMAIL, '[EMAIL]'), (PHONE, '[HP]'), (LONGDIGITS, '[ANGKA]'), (RTRW, '[RTRW]')):
        out, k = pat.subn(rep, out)
        n += k
    if tokens:
        pat = re.compile(r'\b(?:' + '|'.join(re.escape(t) for t in sorted(tokens, key=len, reverse=True)) + r')\b', re.I)
        out, k = pat.subn('[NAMA]', out)
        n += k
    return out, n


def leak_scan(df, full_names):
    """Pindai seluruh sel string: telepon/email/RT-RW, dan nama lengkap asli. Return daftar temuan (kosong = bersih)."""
    findings = []
    names = {norm_key(n) for n in full_names if len(norm_key(n).split()) >= 2}
    for col in df.columns:
        if df[col].dtype != object:
            continue
        for i, v in df[col].dropna().items():
            sv = str(v)
            if PHONE.search(sv) or LONGDIGITS.search(sv) or EMAIL.search(sv) or RTRW.search(sv):
                findings.append((col, i, 'pola_pribadi'))
                continue
            nk = norm_key(sv)
            for nm in names:
                if nm in nk:
                    findings.append((col, i, 'nama_asli'))
                    break
    return findings
