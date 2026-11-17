"""Tahap 2: tautkan pin WhatsApp ke event. Keluaran PRIVAT: data/raw_private/pins.csv, events_geo.csv."""
import sys, re
import numpy as np, pandas as pd
sys.path.insert(0, 'scripts')
from common import read_messages
from link_lib import extract_pins, link_pins

pins = extract_pins(read_messages())
ev = pd.read_csv('data/raw_private/events_raw.csv', parse_dates=['dt_diterima'])
pins.to_csv('data/raw_private/pins.csv', index=False)
print('pin total', len(pins), '| event', len(ev))
for w in (5, 10, 30):
    print(f'jendela ±{w} menit: tertaut', len(link_pins(ev, pins, w)), 'event')
geo = link_pins(ev, pins, 10.0)
geo.to_csv('data/raw_private/events_geo.csv', index=False)
print('PILIHAN: ±10 menit ->', len(geo), 'event bertitik =', round(len(geo) / len(ev) * 100, 1), '% dari event unik')
print('median |selisih| menit', geo.pin_gap_min.abs().median(), '| pin pengirim Hotline:',
      pins.set_index('pin_id').loc[geo.pin_id, 'sender'].str.startswith('Hotline').mean().round(2))
# validasi: kohesi spasial per kelurahan (teks laporan) vs acak
m = geo.merge(ev[['event_id', 'kel_raw']], on='event_id')
m['kel'] = m.kel_raw.fillna('').str.lower().str.replace(r'[^a-z ]', '', regex=True).str.strip()
top = m.kel.value_counts(); top = top[(top >= 6) & (top.index != '')].index
s = m[m.kel.isin(top)].copy()
def hav(la1, lo1, la2, lo2):
    p = np.pi / 180; a = np.sin((la2 - la1) * p / 2) ** 2 + np.cos(la1 * p) * np.cos(la2 * p) * np.sin((lo2 - lo1) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(a))
c = s.groupby('kel')[['lat', 'lon']].transform('median')
own = hav(s.lat, s.lon, c.lat, c.lon)
rng = np.random.default_rng(0); sh = s.kel.sample(frac=1, random_state=0).values
s['kel_sh'] = sh; c2 = s.groupby('kel_sh')[['lat', 'lon']].transform('median')
rnd = hav(s.lat, s.lon, c2.lat, c2.lon)
print(f'validasi kohesi: n={len(s)} event dari {len(top)} kelurahan; median jarak ke median kelurahan sendiri={own.median():.2f} km vs label diacak={rnd.median():.2f} km')
