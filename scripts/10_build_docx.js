// Tahap 10: Markdown laporan -> reports/FinPD_2401020051.docx (dapat diedit di Word).
// Jalankan: python scripts/09_build_report.py && node scripts/10_build_docx.js   (butuh: npm install docx)
const fs = require('fs');
const path = require('path');
const D = require('docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, HeadingLevel, AlignmentType, WidthType,
  ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber, TableOfContents } = D;

const NIM = '2401020051';
const SRC = `reports/_FinPD_${NIM}_expanded.md`;
const OUT = `reports/FinPD_${NIM}.docx`;
const lines = fs.readFileSync(SRC, 'utf8').split(/\r?\n/);
const FONT = 'Arial';
const CONTENT_W = 9638; // A4 11906 - 2*1134 (margin 2 cm), satuan DXA

// ---------- inline: **bold**, `code`, <sub>, <sup>, <br>, [ISI TIM] disorot ----------
function inline(text, base = {}) {
  const runs = [];
  const re = /(\*\*[^*]+\*\*|`[^`]+`|<sub>.*?<\/sub>|<sup>.*?<\/sup>|<br\s*\/?>)/g;
  let last = 0, m;
  const push = (t, extra = {}) => { if (t) runs.push(new TextRun({ text: t, font: FONT, ...base, ...extra })); };
  const plain = (t) => {  // *miring* sederhana
    const parts = t.split(/(\*[^*\s][^*]*\*)/g);
    parts.forEach((p) => (/^\*[^*]+\*$/.test(p) ? push(p.slice(1, -1), { italics: true }) : push(p)));
  };
  while ((m = re.exec(text))) {
    plain(text.slice(last, m.index));
    const tok = m[0];
    if (tok.startsWith('**')) {
      const inner = tok.slice(2, -2);
      push(inner, { bold: true, ...(inner.includes('ISI TIM') ? { highlight: 'yellow' } : {}) });
    } else if (tok.startsWith('`')) push(tok.slice(1, -1), { font: 'Consolas', size: (base.size || 21) - 2 });
    else if (tok.startsWith('<sub>')) push(tok.slice(5, -6), { subScript: true });
    else if (tok.startsWith('<sup>')) push(tok.slice(5, -6), { superScript: true });
    else runs.push(new TextRun({ break: 1, font: FONT }));
    last = m.index + tok.length;
  }
  plain(text.slice(last));
  return runs;
}

// ---------- ukuran PNG dari header ----------
function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }

// ---------- tabel ----------
function cellText(s) { return s.replace(/\\\|/g, '|').trim(); }
function buildTable(rows) {
  const header = rows[0].split('|').slice(1, -1).map(cellText);
  const aligns = rows[1].split('|').slice(1, -1).map((c) => (/^\s*:?-+:\s*$/.test(c) ? 'right' : 'left'));
  const body = rows.slice(2).map((r) => r.split('|').slice(1, -1).map(cellText));
  const n = header.length;
  const maxLen = header.map((h, i) => Math.max(h.length, ...body.map((r) => (r[i] || '').length)));
  const weights = maxLen.map((l) => Math.min(Math.max(l, 5), 38));
  const total = weights.reduce((a, b) => a + b, 0);
  let widths = weights.map((w) => Math.round((w / total) * CONTENT_W));
  widths[n - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: '999999' };
  const borders = { top: border, bottom: border, left: border, right: border };
  const mkCell = (t, i, head) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders,
    shading: head ? { fill: 'E8F0F5', type: ShadingType.CLEAR, color: 'auto' } : undefined,
    margins: { top: 50, bottom: 50, left: 90, right: 90 },
    children: [new Paragraph({ alignment: aligns[i] === 'right' && !head ? AlignmentType.RIGHT : AlignmentType.LEFT,
      children: inline(t, { size: 18, bold: head })})],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, cantSplit: true, children: header.map((t, i) => mkCell(t, i, true)) }),
      ...body.map((r) => new TableRow({ cantSplit: true, children: header.map((_, i) => mkCell(r[i] || '', i, false)) }))],
  });
}

// ---------- pass 1: daftar gambar ----------
const figs = [];
const tabs = [];
lines.forEach((l) => {
  const m = l.match(/^!\[(.*?)\]\((.*?)\)\s*$/); if (m) figs.push(m[1]);
  const t = l.match(/^\*\*Tabel (\d+)\.\*\* (.*)$/); if (t) tabs.push(`Tabel ${t[1]}. ${t[2]}`);
});

// ---------- pass 2: konversi ----------
const children = [];
const numbering = [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }];
let listCount = 0, inCover = false, figNo = 0, i = 0, skipToc = false, firstH1 = true;
const sp = (after = 100) => ({ spacing: { after, line: 300 } });

while (i < lines.length) {
  const raw = lines[i];
  const line = raw.trimEnd();
  if (!line.trim()) { i++; continue; }
  if (/^<div class="cover"/.test(line)) { inCover = true; i++; continue; }
  if (/^<\/div>/.test(line)) { inCover = false; i++; continue; }
  if (/class="pagebreak"/.test(line)) {
    children.push(new Paragraph({ children: [new PageBreak()] }));
    // setelah sampul: daftar isi dan daftar gambar
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: false, children: [new TextRun({ text: 'DAFTAR ISI', font: FONT })] }));
    children.push(new TableOfContents('Daftar Isi', { hyperlink: true, headingStyleRange: '1-2' }));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text: 'DAFTAR TABEL', font: FONT })] }));
    tabs.forEach((t) => children.push(new Paragraph({ ...sp(40), children: [new TextRun({ text: t, font: FONT, size: 20 })] })));
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text: 'DAFTAR GAMBAR', font: FONT })] }));
    figs.forEach((f, k) => children.push(new Paragraph({ ...sp(40), children: [new TextRun({ text: `Gambar ${k + 1}. ${f}`, font: FONT, size: 20 })] })));
    children.push(new Paragraph({ ...sp(60), children: [new TextRun({ text: 'Catatan: tekan klik-kanan > Update Field pada Daftar Isi di Word agar nomor halaman terisi.', font: FONT, size: 18, italics: true })] }));
    i++; continue;
  }
  if (/^DAFTAR ISI/i.test(line.replace(/^#+\s*/, '')) || /^BAB I Business Understanding ·/.test(line)) { i++; continue; } // diganti TOC otomatis
  let m;
  if ((m = line.match(/^(#{1,3})\s+(.*)$/))) {
    const lvl = m[1].length, txt = m[2];
    if (inCover) {
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: lvl === 1 ? 2400 : 200, after: 240 },
        children: [new TextRun({ text: txt, font: FONT, bold: true, size: lvl === 1 ? 36 : 28 })] }));
    } else {
      const h = [HeadingLevel.HEADING_1, HeadingLevel.HEADING_2, HeadingLevel.HEADING_3][lvl - 1];
      children.push(new Paragraph({ heading: h, pageBreakBefore: lvl === 1, children: [new TextRun({ text: txt, font: FONT })] }));
    }
    i++; continue;
  }
  if ((m = line.match(/^!\[(.*?)\]\((.*?)\)\s*$/))) {
    const p = path.resolve('reports', m[2]);
    if (fs.existsSync(p)) {
      const buf = fs.readFileSync(p), { w, h } = pngSize(buf);
      const k = Math.min(560 / w, 360 / h);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
        children: [new ImageRun({ type: 'png', data: buf, transformation: { width: Math.round(w * k), height: Math.round(h * k) },
          altText: { title: m[1], description: m[1], name: path.basename(p) } })] }));
      figNo++;
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
        children: [new TextRun({ text: `Gambar ${figNo}. ${m[1]}`, font: FONT, size: 18, italics: true })] }));
    }
    i++; continue;
  }
  if (line.startsWith('|')) {
    const rows = [];
    while (i < lines.length && lines[i].trim().startsWith('|')) { rows.push(lines[i].trim()); i++; }
    if (rows.length >= 3) { children.push(buildTable(rows)); children.push(new Paragraph({ spacing: { after: 120 }, children: [] })); }
    continue;
  }
  if (line.startsWith('>')) {
    children.push(new Paragraph({ indent: { left: 360 }, spacing: { before: 60, after: 120, line: 300 },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: '2E6F95', space: 8 } },
      children: inline(line.replace(/^>\s?/, ''), { size: 21, italics: true }) }));
    i++; continue;
  }
  if (/^\s*(-|\d+\.)\s+/.test(line)) {
    const ordered = /^\s*\d+\./.test(line);
    const ref = ordered ? `num${++listCount}` : 'bullets';
    if (ordered) numbering.push({ reference: ref, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] });
    while (i < lines.length && /^\s*(-|\d+\.)\s+/.test(lines[i])) {
      const t = lines[i].replace(/^\s*(-|\d+\.)\s+/, '');
      children.push(new Paragraph({ numbering: { reference: ref, level: 0 }, ...sp(60), children: inline(t, { size: 21 }) }));
      i++;
    }
    continue;
  }
  if (/^\*\*Tabel \d+\.\*\* /.test(line)) {                       // judul tabel: menempel ke tabel di bawahnya
    children.push(new Paragraph({ keepNext: true, spacing: { before: 160, after: 60 }, children: inline(line, { size: 20 }) }));
    i++; continue;
  }
  // paragraf biasa (cover: tengah)
  children.push(new Paragraph({ alignment: inCover ? AlignmentType.CENTER : AlignmentType.JUSTIFIED, ...sp(inCover ? 60 : 110),
    children: inline(line, { size: 21 }) }));
  i++;
}

const hStyle = (size, before) => ({ run: { font: FONT, size, bold: true, color: '1D4E6B' }, paragraph: { spacing: { before, after: 120 }, keepNext: true } });
const doc = new Document({
  features: { updateFields: true },
  creator: 'Tim Project Penambangan Data', title: 'Laporan Akhir Project Penambangan Data - DPKP Kota Tanjungpinang',
  numbering: { config: numbering },
  styles: {
    default: { document: { run: { font: FONT, size: 21 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, ...hStyle(32, 240), run: { font: FONT, size: 32, bold: true, color: '1D4E6B' } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, ...hStyle(26, 240) },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true, ...hStyle(23, 160) },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(OUT, b); console.log('DOCX:', OUT, Math.round(b.length / 1024), 'KB;', figs.length, 'gambar'); });
