import sys
sys.path.insert(0, 'scripts')
import pandas as pd
from link_lib import link_pins

def _pins(*ts):
    return pd.DataFrame(dict(pin_id=range(1, len(ts) + 1), ts=pd.to_datetime(ts), lat=[0.9] * len(ts), lon=[104.5] * len(ts)))

def _ev(*dts):
    return pd.DataFrame(dict(event_id=range(1, len(dts) + 1), dt_diterima=pd.to_datetime(dts)))

def test_close_pin_linked_far_pin_not():
    r = link_pins(_ev('2025-05-01 10:00'), _pins('2025-05-01 09:57', '2025-05-03 10:00'))
    assert list(r.pin_id) == [1] and r.pin_gap_min.iloc[0] == 3

def test_one_pin_one_event():
    r = link_pins(_ev('2025-05-01 10:00', '2025-05-01 10:05'), _pins('2025-05-01 10:04'))
    assert len(r) == 1 and r.event_id.iloc[0] == 2   # selisih 1 menit menang atas 4 menit

def test_null_event_time_never_linked():
    assert link_pins(_ev(None), _pins('2025-05-01 10:00')).empty
