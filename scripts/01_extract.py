"""Tahap 1: ekstraksi pesan 'LAPORAN KEJADIAN' -> data/raw_private/events_raw.csv (PRIVAT, memuat nama/HP)."""
import re, sys, datetime as dt
import pandas as pd
sys.path.insert(0, 'scripts')
from common import read_messages
from extract_lib import parse_report

msgs = read_messages()
rows = []
for m in msgs:
    if not re.search(r'LAPORAN\s+KEJADIAN', m['text'], re.I):
        continue
    d = dt.date.fromisoformat(m['ts'][:10])
    r = parse_report(m['text'], d)
    r.update(msg_idx=m['idx'], msg_ts=m['ts'], sender=m['sender'], text=m['text'])
    rows.append(r)
df = pd.DataFrame(rows)
n0 = len(df)
# buang templat kosong/ajakan: tidak punya terima laporan DAN tidak punya jenis
df['has_core'] = df['dt_diterima'].notna() | df['jenis_raw'].notna()
tmpl = df[~df['has_core']]
df = df[df['has_core']].copy()
# dedup repost: kunci = tanggal + jam terima + 120 karakter alfanumerik pertama setelah 'LAPORAN KEJADIAN'
df['key'] = df['tanggal'] + '|' + df['dt_diterima'].astype(str) + '|' + df['text'].str.replace(r'\W', '', regex=True).str[60:180]
dup = df.duplicated('key', keep='first')
df = df[~dup].drop(columns=['has_core', 'key'])
df.insert(0, 'event_id', range(1, len(df) + 1))
df.to_csv('data/raw_private/events_raw.csv', index=False, encoding='utf-8-sig')
v = df['response_minutes'].notna()
print(f"pesan laporan={n0} templat_kosong={len(tmpl)} duplikat={dup.sum()} event_unik={len(df)}")
print(f"response valid={v.sum()} NULL={(~v).sum()} tanggal dari pesan(bukan teks)={(df.sumber_tanggal!='teks').sum()}")
print(df['response_minutes'].describe().round(1).to_string())
print('terlambat>15:', (df.response_minutes > 15).sum(), round((df.response_minutes > 15).sum() / v.sum() * 100, 1), '%')
print('terima NULL', df.dt_diterima.isna().sum(), '| tiba NULL', df.dt_tiba.isna().sum(), '| selesai NULL', df.dt_selesai.isna().sum())
