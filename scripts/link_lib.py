"""Penautan pin lokasi WhatsApp ke event laporan (satu pin untuk satu event)."""
import re
import numpy as np
import pandas as pd

PIN = re.compile(r'maps\.google\.com/\?q=(-?\d+\.\d+),(-?\d+\.\d+)')


def extract_pins(msgs):
    rows = []
    for m in msgs:
        p = PIN.search(m['text'])
        if p:
            rows.append(dict(pin_id=len(rows) + 1, msg_idx=m['idx'], ts=pd.Timestamp(m['ts']), sender=m['sender'],
                             lat=float(p[1]), lon=float(p[2]), has_label='Location:' not in m['text']))
    return pd.DataFrame(rows)


def link_pins(events, pins, window_min=10.0):
    """events: kolom event_id, dt_diterima. pins: kolom pin_id, ts, lat, lon.
    Pasangan (event, pin) dengan |dt_diterima - ts| <= window_min; urut selisih terkecil, tiap event dan pin dipakai sekali.
    Return DataFrame event_id, pin_id, lat, lon, pin_gap_min (event.terima - pin.ts, menit)."""
    ev = events.dropna(subset=['dt_diterima'])
    cand = []
    pt = pins['ts'].values
    for e in ev.itertuples():
        gaps = (np.datetime64(e.dt_diterima) - pt) / np.timedelta64(1, 'm')
        for j in np.where(np.abs(gaps) <= window_min)[0]:
            cand.append((abs(gaps[j]), e.event_id, pins.iloc[j].pin_id, gaps[j]))
    cand.sort()
    used_e, used_p, out = set(), set(), []
    pidx = pins.set_index('pin_id')
    for _, eid, pid, g in cand:
        if eid in used_e or pid in used_p:
            continue
        used_e.add(eid); used_p.add(pid)
        out.append(dict(event_id=eid, pin_id=pid, lat=pidx.loc[pid, 'lat'], lon=pidx.loc[pid, 'lon'], pin_gap_min=g))
    return pd.DataFrame(out, columns=['event_id', 'pin_id', 'lat', 'lon', 'pin_gap_min'])
