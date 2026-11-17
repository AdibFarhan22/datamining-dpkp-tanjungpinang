"""Fungsi praproses yang bisa diuji: koreksi tanggal, kelompok armada, blok jam."""
import re

import pandas as pd

BATAS_MENIT = 15          # SPM: maksimal 15 menit sejak laporan diterima sampai petugas tiba (konfirmasi narasumber)


def fix_dates(df, max_gap_days=3):
    """Jika tanggal di teks laporan beda > max_gap_days dari tanggal pesan, anggap salah ketik (mis. 2024 vs 2025):
    semua kolom dt_* digeser ke tanggal pesan. Return (df_baru, jumlah_dikoreksi). Kolom `tanggal_dikoreksi` ditambah."""
    out = df.copy()
    msg_date = pd.to_datetime(out.msg_ts.str[:10])
    txt_date = pd.to_datetime(out.tanggal)
    delta = (msg_date - txt_date).dt.days
    bad = delta.abs() > max_gap_days
    for c in ('dt_diterima', 'dt_tiba', 'dt_selesai'):
        out[c] = pd.to_datetime(out[c])
        out.loc[bad, c] = out.loc[bad, c] + pd.to_timedelta(delta[bad], unit='D')
    out['tanggal_dikoreksi'] = bad.astype(int)
    return out, int(bad.sum())


def armada_group(s):
    """Kelompok armada dari teks bebas: Mobil Rescue / Armada Dinas (BP) / Kendaraan Pribadi / Campuran / Tidak disebut."""
    if s is None or (isinstance(s, float) and s != s) or not str(s).strip():
        return 'Tidak disebut'
    t = str(s).lower()
    flags = [bool(re.search(r'rescue', t)),
             bool(re.search(r'\bbp\s*\d|armada|damkar|pmk|tangki|ambulan', t)),
             bool(re.search(r'pribadi|motor|klx|sepeda|roda', t))]
    if sum(flags) >= 2:
        return 'Campuran'
    if flags[0]:
        return 'Mobil Rescue'
    if flags[1]:
        return 'Armada Dinas (BP)'
    if flags[2]:
        return 'Kendaraan Pribadi'
    return 'Lainnya'


def jam_blok(h):
    """Blok jam terima: Dini hari 00-05, Pagi 06-11, Siang 12-17, Malam 18-23; NaN -> 'Tidak diketahui'."""
    if h is None or h != h:
        return 'Tidak diketahui'
    h = int(h)
    return 'Dini hari' if h < 6 else 'Pagi' if h < 12 else 'Siang' if h < 18 else 'Malam'


def make_label(resp_minutes, batas=BATAS_MENIT):
    """label_usulan: 1 terlambat (> batas), 0 tepat waktu (<= batas), NaN bila respons tidak valid. Tidak pernah mengisi 0 untuk NULL."""
    if resp_minutes is None or resp_minutes != resp_minutes:
        return float('nan')
    return 1.0 if resp_minutes > batas else 0.0
