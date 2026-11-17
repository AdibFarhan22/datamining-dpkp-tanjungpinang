"""Aplikasi pendukung keputusan DPKP Tanjungpinang (prototipe). Jalankan: streamlit run app/app.py"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring import ARMADA, JENIS, KELURAHAN, POS, REGU, ROOT, load_model, score

st.set_page_config(page_title='Risiko Keterlambatan Respons DPKP', layout='wide')
st.title('Risiko Keterlambatan Respons - DPKP Kota Tanjungpinang')
st.caption('Prototipe hasil penambangan data. Estimasi bersifat statistik dan lemah-sedang (PR-AUC uji 0,47; acak 0,19). '
           'Bukan alat evaluasi kinerja personel dan bukan bukti sebab-akibat.')
bundle = load_model()
t1, t2, t3 = st.tabs(['Skor risiko kejadian', 'Profil wilayah (klaster)', 'Peta titik kejadian'])

with t1:
    c = st.columns(4)
    jenis = c[0].selectbox('Jenis kejadian', JENIS)
    kel = c[1].selectbox('Kelurahan', KELURAHAN)
    pos = c[2].selectbox('Pos jaga yang bertugas', POS, index=len(POS) - 1)
    regu = c[3].selectbox('Regu', REGU, index=len(REGU) - 1)
    c = st.columns(3)
    armada = c[0].selectbox('Armada yang digunakan', ARMADA, index=4)
    jam = c[1].slider('Jam laporan diterima', 0, 23, 12)
    hari = c[2].selectbox('Hari', range(7), format_func=lambda i: ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'][i])
    r = score(bundle, jenis=jenis, kelurahan=kel, pos=pos, regu=regu, armada_grup=armada, jam=jam, hari=hari)
    st.metric('Skor risiko terlambat (> 15 menit)', f"{r['prob']:.0%}", help='Skor relatif dari model Random Forest; bukan probabilitas terkalibrasi.')
    if r['tingkat'] == 'tinggi':
        st.error('**RISIKO TINGGI** (skor 60% ke atas). Pada data uji, 70% kejadian dengan skor setinggi ini benar-benar terlambat '
                 '(hanya 20 kejadian, jadi masih belum pasti).')
    elif r['tingkat'] == 'perhatian':
        st.warning(f"**PERHATIAN** (skor di atas ambang model {r['ambang']:.2f} tetapi di bawah 60%). Pada data uji, hanya sekitar 17% kejadian "
                   'pada rentang skor ini yang terlambat, setara rata-rata keseluruhan. Jangan dibaca sebagai peringatan khusus.')
    else:
        st.success(f"**RENDAH** (di bawah ambang model {r['ambang']:.2f}). Pada data uji, sekitar 9-15% kejadian pada rentang skor ini yang terlambat.")
    st.caption('Gunakan sebagai bahan pertimbangan kesiapsiagaan, bukan keputusan otomatis. Skor adalah ukuran relatif, bukan peluang sebenarnya. '
               'Model lebih baik untuk penyelamatan hewan (recall 77%) daripada kebakaran (recall 31%).')
    h = pd.read_csv(os.path.join(ROOT, 'data', 'siap_mining', 'klasifikasi.csv'))
    s = h[(h.jenis == jenis) & (h.pos == pos)]
    st.write(f'Konteks historis: {len(s)} kejadian "{jenis}" dengan pos "{pos}"; terlambat {s.label_usulan.mean():.0%}' if len(s) else 'Tidak ada kejadian historis pada kombinasi jenis dan pos ini.')

with t2:
    k = pd.read_csv(os.path.join(ROOT, 'data', 'siap_mining', 'hasil_klaster_kelurahan.csv'))
    st.write('Segmentasi deskriptif 16 kelurahan (eksploratif, struktur klaster lemah).')
    st.dataframe(k[['kelurahan', 'klaster', 'n_event', 'event_per_bulan', 'share_kebakaran', 'share_malam', 'median_respons', 'pct_terlambat']].round(3), use_container_width=True)
    st.scatter_chart(k, x='event_per_bulan', y='pct_terlambat', color='klaster', size=60)

with t3:
    g = pd.read_csv(os.path.join(ROOT, 'data', 'siap_mining', 'hasil_klaster_titik.csv'))
    st.write(f'{len(g)} kejadian yang pin lokasinya dapat ditautkan (16% dari seluruh event). Koordinat dibulatkan ~110 m.')
    st.map(g.rename(columns={'lat_r': 'latitude', 'lon_r': 'longitude'}), latitude='latitude', longitude='longitude')
