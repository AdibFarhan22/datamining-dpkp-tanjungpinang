"""Tahap 13: gabungkan docs/ebook/*.md menjadi docs/EBOOK_Panduan_Belajar_DPKP.pdf (sampul, daftar isi, nomor halaman)."""
import glob
import os
import subprocess

import markdown

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
parts = sorted(glob.glob('docs/ebook/*.md'))
body_md = '\n\n'.join(open(p, encoding='utf-8').read() for p in parts)
md = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists', 'toc'], extension_configs={'toc': {'toc_depth': '1-2'}})
content = md.convert(body_md)
toc = md.toc
cover = """
<section class="cover">
  <div class="kicker">PANDUAN BELAJAR UNTUK PEMULA</div>
  <h1 class="ctitle">Dari Chat WhatsApp ke Model Prediksi</h1>
  <div class="csub">Memahami project data mining DPKP Kota Tanjungpinang dari awal sampai akhir:<br>proses, hasil nyata, dan keterbatasannya</div>
  <div class="cteam">Tim Project Penambangan Data<br>2401020051 Abdul Hafidz (ketua) · 2401020011 Bayu Adhandika · 2401020090 Adib Farhan Sihombing<br>2401020058 Muhammad Rahman Afrialdi · 2401020084 Vito Hendriansyah</div>
  <div class="cfoot">Teknik Informatika · Universitas Maritim Raja Ali Haji · Ganjil 2026–2027</div>
</section>
<section class="tocpage"><h1 class="toch">Daftar Isi</h1>""" + toc + "</section>"
css = """
@page { size: A4; margin: 18mm 17mm 20mm 17mm; @bottom-center { content: counter(page); font: 9pt 'Segoe UI', Arial; color: #666; } }
@page :first { @bottom-center { content: ''; } }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.6pt; line-height: 1.55; color: #1a1a1a; }
h1 { font-size: 20pt; color: #1d4e6b; border-bottom: 3px solid #2E6F95; padding-bottom: 6px; page-break-before: always; margin-top: 0; }
h2 { font-size: 14pt; color: #1d4e6b; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 11.8pt; color: #333; margin-top: 16px; page-break-after: avoid; }
p { margin: 6px 0; text-align: left; } li { margin: 3px 0; }
table { border-collapse: collapse; margin: 10px 0; font-size: 9.4pt; width: 100%; page-break-inside: avoid; }
th, td { border: 1px solid #aab; padding: 4px 8px; vertical-align: top; } th { background: #e6eff5; text-align: left; }
pre { background: #f3f6f9; border: 1px solid #d3dce3; border-radius: 4px; padding: 8px 10px; font-size: 8.8pt; line-height: 1.35; white-space: pre-wrap; page-break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 9.3pt; background: #eef2f5; padding: 0 3px; border-radius: 3px; }
pre code { background: none; padding: 0; }
blockquote { margin: 10px 0; padding: 7px 14px; background: #f1f7fb; border-left: 5px solid #2E6F95; page-break-inside: avoid; }
blockquote p { margin: 4px 0; }
img { display: block; max-width: 100%; max-height: 96mm; margin: 10px auto; }
.cover { height: 250mm; text-align: center; page-break-after: always; display: flex; flex-direction: column; justify-content: center; }
.kicker { letter-spacing: 3px; color: #2E6F95; font-weight: 600; font-size: 11pt; }
.ctitle { font-size: 31pt; border: none; page-break-before: avoid; color: #12384f; margin: 18px 0 10px; line-height: 1.15; }
.csub { font-size: 13pt; color: #333; margin: 6px 40px 40px; }
.cteam { font-size: 10.5pt; color: #333; line-height: 1.7; } .cfoot { margin-top: 36px; color: #666; font-size: 10pt; }
.tocpage { page-break-after: always; } .toch { page-break-before: auto; }
.toc ul { list-style: none; padding-left: 0; } .toc ul ul { padding-left: 18px; font-size: 9.6pt; } .toc a { color: #1a1a1a; text-decoration: none; }
.toc > ul > li { margin-top: 7px; font-weight: 600; } .toc > ul > li > ul > li { font-weight: 400; }
"""
html = f'<!doctype html><html lang="id"><head><meta charset="utf-8"><title>E-book Panduan Belajar DPKP</title><style>{css}</style></head><body>{cover}{content}</body></html>'
tmp = 'docs/ebook/_ebook.html'
open(tmp, 'w', encoding='utf-8').write(html)
out = os.path.abspath('docs/EBOOK_Panduan_Belajar_DPKP.pdf')
subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={out}',
                'file:///' + os.path.abspath(tmp).replace('\\', '/')], check=True, capture_output=True, timeout=180)
os.remove(tmp)
print('PDF:', out, os.path.getsize(out) // 1024, 'KB;', len(parts), 'bab')
