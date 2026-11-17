"""Util bersama: parser pesan WhatsApp dan parser waktu."""
import re

CHAT = r'D:\data-mining-dpkp\_chat.txt'
# Baris pesan bisa diawali karakter tak terlihat (LRM U+200E) dan teksnya boleh kosong setelah ':'
HDR = re.compile(r'^[\u200e\u200f\ufeff]*\[(\d\d)/(\d\d)/(\d\d), (\d\d)\.(\d\d)\.(\d\d)\] ([^:\n]+):[ \t]?')


def read_messages(path=CHAT):
    """Baca chat WA -> list dict(idx, ts 'YYYY-MM-DD HH:MM:SS', sender, text). Pesan multi-baris digabung."""
    msgs, cur = [], None
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = HDR.match(line)
            if m:
                cur = dict(idx=len(msgs), ts=f"20{m[3]}-{m[2]}-{m[1]} {m[4]}:{m[5]}:{m[6]}",
                           sender=m[7].strip(), text=line[m.end():])
                msgs.append(cur)
            elif cur is not None:
                cur['text'] += line
    return msgs


def parse_time(text, label_regex):
    """Ambil jam setelah label (menit sejak 00:00) atau None bila kosong/tidak valid."""
    m = re.search(label_regex + r'[^\n\d]{0,30}?(\d{1,2})\s*[.:;,]?\s*(\d{2})', text, re.I)
    if not m:
        return None
    h, mi = int(m[1]), int(m[2])
    return h * 60 + mi if h < 24 and mi < 60 else None
