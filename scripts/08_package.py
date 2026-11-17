"""Tahap 8: kemas Mentah_2401020051.7z dan SiapMining_2401020051.7z sesuai panduan unggah."""
import os
import py7zr

NIM = '2401020051'
os.makedirs('dist', exist_ok=True)
PAKET = {
    f'dist/Mentah_{NIM}.7z': ['data/mentah_anonim/events_mentah_anon.csv', 'data/mentah_anonim/KAMUS_DATA_MENTAH.md'],
    f'dist/SiapMining_{NIM}.7z': ['data/siap_mining/klasifikasi.csv', 'data/siap_mining/titik_geo.csv', 'data/siap_mining/hasil_klaster_titik.csv',
                                  'data/siap_mining/kelurahan_profil.csv', 'data/siap_mining/hasil_klaster_kelurahan.csv',
                                  'data/siap_mining/events_bersih.csv', 'data/siap_mining/KAMUS_DATA_SIAP_MINING.md'],
}
for out, files in PAKET.items():
    for f in files:
        assert os.path.exists(f), f'berkas tidak ada: {f}'
    assert not any('raw_private' in f or f.endswith('_chat.txt') for f in files)     # data privat tidak boleh masuk paket
    with py7zr.SevenZipFile(out, 'w') as z:
        for f in files:
            z.write(f, arcname=os.path.basename(f))
    with py7zr.SevenZipFile(out, 'r') as z:
        names = z.getnames()
    print(f'{out}: {os.path.getsize(out) / 1024:.0f} KB, isi: {names}')
