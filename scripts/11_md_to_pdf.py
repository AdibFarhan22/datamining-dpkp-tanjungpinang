"""Ubah satu berkas Markdown menjadi PDF (Markdown -> HTML -> Edge headless).
Pemakaian: python scripts/11_md_to_pdf.py docs/SKRIP_VIDEO_PER_ANGGOTA.md"""
import os
import subprocess
import sys

import markdown

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
src = sys.argv[1]
base = os.path.splitext(src)[0]
body = markdown.markdown(open(src, encoding='utf-8').read(), extensions=['tables', 'fenced_code', 'sane_lists'])
css = """
@page { size: A4; margin: 16mm 15mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.3pt; line-height: 1.5; color: #111; }
h1 { font-size: 17pt; color: #1d4e6b; border-bottom: 2px solid #2E6F95; padding-bottom: 4px; }
h2 { font-size: 13pt; color: #1d4e6b; margin-top: 20px; border-bottom: 1px solid #c5d6e0; padding-bottom: 2px; page-break-after: avoid; }
h3 { font-size: 11pt; } hr { border: 0; border-top: 1px solid #ccc; margin: 14px 0; }
table { border-collapse: collapse; margin: 8px 0; font-size: 9.3pt; page-break-inside: avoid; }
th, td { border: 1px solid #999; padding: 3px 8px; } th { background: #e8f0f5; }
pre { background: #f4f6f8; border: 1px solid #d5dde3; padding: 8px 10px; font-size: 9pt; white-space: pre-wrap; page-break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 9.2pt; background: #f1f4f6; padding: 0 3px; }
pre code { background: none; padding: 0; }
p { margin: 5px 0; } li { margin: 2px 0; }
"""
html = f'<!doctype html><html lang="id"><head><meta charset="utf-8"><style>{css}</style></head><body>{body}</body></html>'
open(base + '.html', 'w', encoding='utf-8').write(html)
out = os.path.abspath(base + '.pdf')
subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={out}',
                'file:///' + os.path.abspath(base + '.html').replace('\\', '/')], check=True, capture_output=True, timeout=120)
os.remove(base + '.html')
print('PDF:', out, os.path.getsize(out) // 1024, 'KB')
