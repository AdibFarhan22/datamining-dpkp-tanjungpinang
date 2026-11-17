"""Tahap 9: bangun reports/FinPD_2401020051.pdf dari Markdown (Markdown -> HTML -> PDF lewat Edge headless).
Langkah: sisipkan bahan tambahan (reports/extras), beri nomor judul tabel, buat Daftar Isi/Tabel/Gambar, beri nomor halaman.
Keluaran antara untuk Word: reports/_FinPD_2401020051_expanded.md (dipakai scripts/10_build_docx.js)."""
import html as htmllib
import os
import re
import subprocess

import markdown
import pandas as pd

NIM = '2401020051'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
md = open(f'reports/FinPD_{NIM}.md', encoding='utf-8').read()

# 1. bahan tambahan dan cuplikan data
cols = ['event_id', 'tanggal', 'dt_diterima', 'dt_tiba', 'response_minutes', 'petugas_kode', 'pelapor_kode', 'alamat_anon', 'jenis_raw', 'pos']
cup = pd.read_csv('data/mentah_anonim/events_mentah_anon.csv')[cols].dropna(subset=['dt_tiba']).head(6)
md = md.replace('{{CUPLIKAN}}', cup.to_markdown(index=False))


def extra(m):
    p = f'reports/extras/{m.group(1)}.md'
    assert os.path.exists(p), f'bahan tambahan tidak ada: {p} (jalankan scripts/14_report_extras.py)'
    return open(p, encoding='utf-8').read().strip()


md = re.sub(r'\{\{EXTRA:([a-z0-9_]+)\}\}', extra, md)

# 2. judul tabel bernomor: baris "Tabel: Judul" -> "**Tabel N.** Judul"
tables, n = [], 0
out_lines = []
for line in md.split('\n'):
    m = re.match(r'^Tabel: (.+)$', line)
    if m:
        n += 1
        tables.append(m.group(1).strip())
        out_lines.append(f'**Tabel {n}.** {m.group(1).strip()}')
    else:
        out_lines.append(line)
md = '\n'.join(out_lines)
assert '{{' not in md.replace('{{DAFTAR_ISI}}', ''), 'masih ada placeholder yang belum terisi'

# 3. daftar judul bab dan sub-bab (tanpa sampul)
body_after_cover = md.split('<div class="pagebreak"></div>', 1)[1]
heads = [(len(m.group(1)), m.group(2).strip()) for m in re.finditer(r'^(#{1,2}) (.+)$', body_after_cover, re.M)]
figs = re.findall(r'^!\[(.*?)\]\(.*?\)\s*$', md, re.M)

# keluaran untuk Word (tanpa penanda daftar isi; Word membuat sendiri)
open(f'reports/_FinPD_{NIM}_expanded.md', 'w', encoding='utf-8').write(md.replace('{{DAFTAR_ISI}}', ''))

# 4. HTML
body = markdown.markdown(md.replace('{{DAFTAR_ISI}}', '<!--TOC-->'), extensions=['tables', 'md_in_html', 'sane_lists'])
fig_n = [0]


def figrepl(m):
    fig_n[0] += 1
    return f'<span class="fig"><img alt="{m.group(1)}" src="{m.group(2)}" /><span class="cap">Gambar {fig_n[0]}. {m.group(1)}</span></span>'


body = re.sub(r'<img alt="([^"]*)" src="([^"]*)" ?/?>', figrepl, body)
esc = htmllib.escape
toc_items = ''.join(f'<li class="l{lvl}">{esc(t)}</li>' for lvl, t in heads)
toc_html = (f'<h1 class="toch">DAFTAR ISI</h1><ul class="toc">{toc_items}</ul>'
            f'<h1>DAFTAR TABEL</h1><ul class="lst">' + ''.join(f'<li>Tabel {i}. {esc(t)}</li>' for i, t in enumerate(tables, 1)) + '</ul>'
            f'<h1>DAFTAR GAMBAR</h1><ul class="lst">' + ''.join(f'<li>Gambar {i}. {esc(t)}</li>' for i, t in enumerate(figs, 1)) + '</ul>')
body = body.replace('<!--TOC-->', toc_html)
css = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; @bottom-center { content: counter(page); font: 9pt 'Segoe UI', Arial; color: #666; } }
@page :first { @bottom-center { content: ''; } }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #111; }
h1 { font-size: 17pt; page-break-before: always; border-bottom: 2px solid #2E6F95; padding-bottom: 4px; }
h2 { font-size: 13pt; margin-top: 18px; color: #1d4e6b; page-break-after: avoid; } h3 { font-size: 11.5pt; page-break-after: avoid; }
table { border-collapse: collapse; margin: 6px 0 12px; font-size: 9pt; width: auto; max-width: 100%; page-break-inside: avoid; }
th, td { border: 1px solid #999; padding: 3px 7px; vertical-align: top; } th { background: #e8f0f5; }
p strong:first-child { }
.fig { display: block; text-align: center; margin: 8px 0 12px; page-break-inside: avoid; }
.fig img { max-width: 100%; max-height: 100mm; display: block; margin: 0 auto 3px; }
.cap { display: block; font-size: 9pt; font-style: italic; color: #333; }
blockquote { border-left: 4px solid #2E6F95; margin: 8px 0; padding: 4px 12px; background: #f4f8fb; }
code { font-family: Consolas, monospace; font-size: 9pt; background: #f1f4f6; padding: 0 2px; }
ul.toc, ul.lst { list-style: none; padding-left: 0; } ul.toc li.l1 { font-weight: 700; margin-top: 7px; } ul.toc li.l2 { margin-left: 18px; font-size: 9.6pt; }
ul.lst li { font-size: 9.6pt; margin: 2px 0; }
.cover { text-align: center; padding-top: 50mm; } .cover h1 { border: none; page-break-before: avoid; font-size: 20pt; }
.cover h2 { font-size: 15pt; color: #111; } .pagebreak { page-break-after: always; } .toch { page-break-before: auto; }
"""
html = f'<!doctype html><html lang="id"><head><meta charset="utf-8"><title>FinPD_{NIM}</title><style>{css}</style></head><body>{body}</body></html>'
with open(f'reports/FinPD_{NIM}.html', 'w', encoding='utf-8') as f:
    f.write(html)
src = 'file:///' + os.path.abspath(f'reports/FinPD_{NIM}.html').replace('\\', '/')
out = os.path.abspath(f'reports/FinPD_{NIM}.pdf')
subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={out}', src], check=True, capture_output=True, timeout=180)
print(f'PDF: {out} {os.path.getsize(out) // 1024} KB; {len(tables)} tabel, {len(figs)} gambar')
