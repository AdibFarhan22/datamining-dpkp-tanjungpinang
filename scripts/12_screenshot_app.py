"""Tahap 12: tangkapan layar aplikasi Streamlit yang sedang berjalan (Playwright + Microsoft Edge terpasang).
Prasyarat: python -m streamlit run app/app.py --server.port 8502 --theme.base light
Keluaran: figures/app/*.png"""
import os

from playwright.sync_api import sync_playwright

URL = 'http://localhost:8502'
OUT = 'figures/app'
os.makedirs(OUT, exist_ok=True)


ORDER = {'Jenis kejadian': 0, 'Kelurahan': 1, 'Pos jaga yang bertugas': 2, 'Regu': 3, 'Armada yang digunakan': 4, 'Hari': 5}


def pick(page, label, value):
    """Pilih opsi pada kotak pilihan ke-N (urutan sesuai tata letak app/app.py), ketik nilai, tekan Enter."""
    sel = page.locator('div[data-baseweb="select"]').nth(ORDER[label])
    sel.click()
    page.keyboard.type(value)
    page.wait_for_timeout(400)
    page.keyboard.press('Enter')
    page.wait_for_timeout(700)


def set_hour(page, hour):
    """Geser slider jam: klik di perkiraan posisi, lalu koreksi satu langkah demi satu sambil membaca nilai aktual."""
    sl = page.get_by_role('slider').first
    box = page.locator('[data-testid="stSlider"]').first.bounding_box()
    page.mouse.click(box['x'] + 12 + (box['width'] - 24) * hour / 23, box['y'] + box['height'] - 22)
    page.wait_for_timeout(600)
    for _ in range(40):
        cur = int(page.get_by_role('slider').first.get_attribute('aria-valuenow'))
        if cur == hour:
            break
        sl.focus()
        page.keyboard.press('ArrowRight' if cur < hour else 'ArrowLeft')
        page.wait_for_timeout(450)
    assert int(page.get_by_role('slider').first.get_attribute('aria-valuenow')) == hour, 'slider jam tidak mencapai target'
    page.wait_for_timeout(500)


def settle(page):
    page.wait_for_timeout(1800)


with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True)
    page = br.new_page(viewport={'width': 1360, 'height': 900}, device_scale_factor=2)
    page.goto(URL)
    page.get_by_text('Risiko Keterlambatan Respons - DPKP Kota Tanjungpinang').wait_for(timeout=30000)
    page.wait_for_timeout(2500)

    # skenario A: berisiko
    pick(page, 'Jenis kejadian', 'Evakuasi Ular')
    pick(page, 'Kelurahan', 'Batu IX')
    pick(page, 'Pos jaga yang bertugas', 'Pos Dompak')
    pick(page, 'Regu', 'Regu 6')
    pick(page, 'Armada yang digunakan', 'Mobil Rescue')
    pick(page, 'Hari', 'Rabu')
    set_hour(page, 14)
    settle(page)
    page.screenshot(path=f'{OUT}/app_1_skor_berisiko.png', clip={'x': 0, 'y': 0, 'width': 1360, 'height': 740})
    metric = lambda: page.locator('[data-testid="stMetricValue"]').first.inner_text()
    print('debug A:', metric(), page.get_by_text('RISIKO TINGGI').count(), page.locator('[data-testid="stAlert"]').all_inner_texts())
    assert metric() == '60%' and page.get_by_text('RISIKO TINGGI').count() == 1, 'skenario A tidak sesuai harapan'
    print('A (tinggi):', metric())

    # skenario C: tingkat perhatian (regu diganti)
    pick(page, 'Regu', 'Regu 4')
    settle(page)
    assert metric() == '50%' and page.get_by_text('PERHATIAN').count() == 1, 'skenario C tidak sesuai harapan'
    page.screenshot(path=f'{OUT}/app_5_skor_perhatian.png', clip={'x': 0, 'y': 0, 'width': 1360, 'height': 740})
    print('C (perhatian):', metric())

    # skenario B: tingkat rendah
    pick(page, 'Pos jaga yang bertugas', 'Mako SKB')
    pick(page, 'Regu', 'Regu 2')
    set_hour(page, 3)
    settle(page)
    page.screenshot(path=f'{OUT}/app_2_skor_rendah.png', clip={'x': 0, 'y': 0, 'width': 1360, 'height': 740})
    assert metric() == '12%' and page.get_by_text('RENDAH').count() == 1, 'skenario B tidak sesuai harapan'
    print('B (rendah):', metric())

    page.get_by_role('tab', name='Profil wilayah (klaster)').click()
    page.set_viewport_size({'width': 1360, 'height': 1330})      # kontainer Streamlit menggulir sendiri: tinggikan viewport
    settle(page)
    page.screenshot(path=f'{OUT}/app_3_profil_wilayah.png', clip={'x': 0, 'y': 0, 'width': 1360, 'height': 1110})
    page.set_viewport_size({'width': 1360, 'height': 900})

    page.get_by_role('tab', name='Peta titik kejadian').click()
    page.wait_for_timeout(4000)
    page.screenshot(path=f'{OUT}/app_4_peta_titik.png', clip={'x': 0, 'y': 0, 'width': 1360, 'height': 850})
    br.close()
print('selesai:', sorted(os.listdir(OUT)))
