import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import json
import os

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WebGIS Tanaman Herbal TNBTS",
    page_icon="🌿",
    layout="wide"
)

if 'menu_selected' not in st.session_state:
    st.session_state.menu_selected = "Peta Sebaran"
if 'music_playing' not in st.session_state:
    st.session_state.music_playing = True

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(rgba(0,0,0,.5),rgba(0,0,0,.5)),
                    url('https://tunashijau.id/wp-content/uploads/2023/12/tnbts.jpg');
        background-size:cover; background-position:center;
        padding:2.5rem 1.5rem; border-radius:10px; margin-bottom:1rem;
        color:white; text-align:center; box-shadow:0 4px 15px rgba(0,0,0,.3);
    }
    .main-header h1 { color:white; margin:0; font-size:2.2rem;
        text-shadow:2px 2px 4px rgba(0,0,0,.5); font-weight:bold; }
    .main-header p  { color:#E8F5E9; margin:.5rem 0 0 0; font-size:1rem;
        background:rgba(0,0,0,.3); display:inline-block;
        padding:.3rem 1rem; border-radius:30px; }

    [data-testid="stSidebar"] {
        background: linear-gradient(rgba(0,0,0,.6),rgba(0,0,0,.7)),
                    url('https://asset.kompas.com/crops/G4x25tAnC3TVtqQzc19Qi3y4fwo=/0x0:1200x800/1200x800/data/photo/2021/10/29/617b830f26293.png');
        background-size:cover; background-position:center;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color:white !important; text-shadow:2px 2px 4px rgba(0,0,0,.5); }
    [data-testid="stSidebar"] p  { color:rgba(255,255,255,.9) !important; }
    [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.3) !important; }
    [data-testid="stSidebar"] .stRadio>div {
        background-color:rgba(255,255,255,.15); padding:10px; border-radius:10px;
        backdrop-filter:blur(5px); border:1px solid rgba(255,255,255,.2); }
    [data-testid="stSidebar"] .stRadio label    { color:white !important; font-weight:500; }
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stCheckbox label { color:white !important; }

    .sidebar-header-new {
        background: linear-gradient(rgba(0,0,0,.5),rgba(0,0,0,.6)),
                    url('https://asset.kompas.com/crops/G4x25tAnC3TVtqQzc19Qi3y4fwo=/0x0:1200x800/1200x800/data/photo/2021/10/29/617b830f26293.png');
        background-size:cover; background-position:center;
        padding:1.5rem 1rem; border-radius:10px; color:white; text-align:center;
        margin-bottom:1rem; border:2px solid rgba(255,215,0,.3);
        box-shadow:0 4px 15px rgba(0,0,0,.4);
    }
    .sidebar-header-new h3 { color:#FFD700 !important; margin:0; font-size:1.4rem;
        text-shadow:2px 2px 4px rgba(0,0,0,.7); font-weight:bold; }
    .sidebar-header-new p  { color:#FFFFFF !important; margin:.5rem 0 0 0;
        font-style:italic; background:rgba(0,0,0,.3); display:inline-block;
        padding:.2rem 1rem; border-radius:20px; }

    .metric-card {
        background:white; padding:1rem; border-radius:10px;
        box-shadow:0 2px 4px rgba(0,0,0,.1); text-align:center;
        border-left:4px solid #2E7D32; margin-bottom:1rem;
        transition:transform .3s ease;
    }
    .metric-card:hover { transform:translateY(-5px); box-shadow:0 4px 8px rgba(0,0,0,.15); }
    .metric-card h3 { color:#2E7D32; margin:0; font-size:1.8rem; font-weight:bold; }
    .metric-card p  { color:#666; margin:.2rem 0 0 0; font-size:.9rem; text-transform:uppercase; }

    .stTabs [data-baseweb="tab-list"] {
        gap:2rem; background-color:#f5f5f5; padding:.5rem; border-radius:10px; }
    .stTabs [data-baseweb="tab"] { border-radius:5px; padding:.5rem 1rem; }

    .dataframe-container { border:1px solid #ddd; border-radius:10px;
        padding:1rem; background:white; }

    .footer {
        background: linear-gradient(rgba(0,0,0,.6),rgba(0,0,0,.7)),
                    url('https://statik.tempo.co/data/2024/05/26/id_1305154/1305154_720.jpg');
        background-size:cover; background-position:center;
        color:white; padding:2rem 1.5rem; border-radius:10px;
        text-align:center; margin-top:2rem;
    }
    .footer a { color:#FFD700; text-decoration:none; font-weight:bold; }

    .custom-divider {
        height:3px;
        background:linear-gradient(90deg,transparent,#4CAF50,transparent);
        margin:2rem 0;
    }
    .image-caption { text-align:center; font-style:italic;
        color:#666; margin-top:.3rem; font-size:.9rem; }
    .status-badge {
        background:rgba(255,255,255,.2); backdrop-filter:blur(5px);
        padding:.5rem; border-radius:5px; margin:.3rem 0;
        border-left:3px solid #FFD700; color:white;
    }
    .status-badge small { color:rgba(255,255,255,.8); }
    .stButton>button {
        background:linear-gradient(135deg,#2E7D32 0%,#4CAF50 100%);
        color:white; border:none; padding:.5rem 2rem; font-weight:bold;
        border-radius:5px; transition:all .3s ease;
    }
    .stButton>button:hover {
        background:linear-gradient(135deg,#1B5E20 0%,#2E7D32 100%);
        box-shadow:0 4px 8px rgba(0,0,0,.2);
    }
    .stDownloadButton>button {
        background:linear-gradient(135deg,#1976D2 0%,#2196F3 100%);
        color:white; border:none; padding:.5rem 2rem; font-weight:bold;
        border-radius:5px; transition:all .3s ease;
    }
    .info-box {
        background-color:#E8F5E9; border-left:4px solid #4CAF50;
        padding:1.5rem; border-radius:5px; margin:1rem 0;
    }
    .info-box h4 { color:#2E7D32; margin-top:0; margin-bottom:1rem; }
    .fungsi-card {
        background:white; border-radius:10px; padding:1.2rem;
        margin-bottom:1rem; box-shadow:0 2px 4px rgba(0,0,0,.1);
        border-left:4px solid #4CAF50; transition:transform .2s;
    }
    .fungsi-card:hover { transform:translateX(5px); }
    .fungsi-title { color:#2E7D32; font-size:1.1rem; font-weight:bold;
        margin-bottom:.8rem; border-bottom:2px solid #4CAF50; padding-bottom:.3rem; }
    .tanaman-list {
        display:flex; flex-wrap:wrap; gap:.5rem; max-height:250px;
        overflow-y:auto; padding:.5rem; border:1px solid #e0e0e0;
        border-radius:5px; background:#fafafa;
    }
    .tanaman-badge {
        background:#E8F5E9; color:#2E7D32; padding:.3rem .8rem;
        border-radius:20px; font-size:.85rem; border:1px solid #4CAF50;
        cursor:help; transition:all .2s;
    }
    .tanaman-badge:hover { background:#4CAF50; color:white; transform:scale(1.05); }
    .team-card {
        background:#f5f5f5; padding:1.5rem; border-radius:10px;
        text-align:center; min-height:380px;
        box-shadow:0 4px 8px rgba(0,0,0,.1); transition:transform .3s ease;
    }
    .team-card:hover { transform:translateY(-5px); }
    .team-photo {
        width:150px; height:150px; border-radius:50%; object-fit:cover;
        border:4px solid #4CAF50; margin-bottom:1rem;
    }
    .team-name  { color:#2E7D32; margin:.5rem 0 .2rem 0; font-size:1.1rem; font-weight:bold; }
    .team-title { color:#666; margin:.2rem 0; font-size:.9rem; }
    .team-role  { color:#666; font-style:italic; margin-top:.5rem; font-size:.85rem;
        background:rgba(76,175,80,.1); padding:.3rem; border-radius:20px; }
    .kawasan-badge {
        display:inline-block; padding:.25rem .75rem; border-radius:20px;
        font-size:.8rem; font-weight:600; color:white; margin:.2rem .1rem;
    }

    /* ── Legenda kawasan di peta ── */
    .legend-kawasan {
        background:white; border-radius:10px; padding:12px 14px;
        box-shadow:0 2px 8px rgba(0,0,0,.15); font-family:Arial,sans-serif;
    }
    .legend-kawasan h4 { margin:0 0 8px 0; font-size:13px; color:#1B5E20; }
    .legend-kawasan .l-row {
        display:flex; align-items:center; gap:6px;
        font-size:11px; margin-bottom:4px; color:#333;
    }
    .legend-kawasan .l-box {
        width:14px; height:14px; border-radius:3px;
        flex-shrink:0; border:1px solid rgba(0,0,0,.2);
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA WARNA
# ─────────────────────────────────────────────────────────────────────────────
# Hex fill untuk polygon kawasan (juga dipakai di marker & badge)
KAWASAN_HEX = {
    "Blok Ireng-Ireng & Hutan Atas":   "#1B5E20",
    "Kantong Air & Lembah":             "#0277BD",
    "Lereng Semeru & Dataran Tinggi":   "#6D4C41",
    "Ranu Darungan & Sekitar Danau":    "#00838F",
    "Savana Bromo & Lereng Terbuka":    "#F57F17",
    "Tepi Hutan & Zona Transisi":       "#558B2F",
    "Zona Budidaya & Pekarangan":       "#AD1457",
    "Zona Pesisir & Pantai Selatan":    "#1565C0",
}

# Warna CircleMarker berdasarkan jenis tanaman
JENIS_COLOR = {
    'Herba':  'cadetblue',
    'Pohon':  'green',
    'Semak':  'lightgreen',
    'Pakis':  'darkgreen',
    'Rumput': 'beige',
    'Bunga':  'pink',
    'Perdu':  'purple',
    'Lumut':  'lightgray',
}

# ─────────────────────────────────────────────────────────────────────────────
# POLYGON 8 KAWASAN EKOLOGI TNBTS
# Koordinat [lat, lon] mendekati batas ekologi riil masing-masing kawasan.
# Disusun sebagai GeoJSON "Polygon" (lon, lat — standar GeoJSON).
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Koordinat polygon dihitung dengan metode hexagonal non-overlapping.
# Setiap kawasan memiliki bounding box yang tidak bersinggungan dengan kawasan lain.
# Pusat polygon = centroid data survei; radius disesuaikan agar proporsional
# terhadap jumlah spesies dan luas ekologi relatif.
# Urutan koordinat: [lon, lat] — standar GeoJSON (bukan [lat, lon]).
# ─────────────────────────────────────────────────────────────────────────────
KAWASAN_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        # ── 1. Blok Ireng-Ireng & Hutan Atas ─────────────────────────────
        # Center: (-7.898, 112.917) | radius: 0.0085 lat × 0.0090 lon
        # Posisi: barat-laut TNBTS, hutan primer, ketinggian tertinggi
        {
            "type": "Feature",
            "properties": {
                "nama": "Blok Ireng-Ireng & Hutan Atas",
                "deskripsi": "Hutan primer, epifit, lumut, pakis langka, tanaman endemik",
                "ketinggian": "2.400 – 2.600 mdpl",
                "spesies": 14,
                "emoji": "🌲"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.92479, -7.89375],
                    [112.91700, -7.88950],
                    [112.90921, -7.89375],
                    [112.90921, -7.90225],
                    [112.91700, -7.90650],
                    [112.92479, -7.90225],
                    [112.92479, -7.89375]
                ]]
            }
        },
        # ── 2. Ranu Darungan & Sekitar Danau ─────────────────────────────
        # Center: (-7.904, 112.951) | radius: 0.0050 lat × 0.0055 lon
        # Posisi: utara-timur, dekat danau Ranu Darungan, area kecil
        {
            "type": "Feature",
            "properties": {
                "nama": "Ranu Darungan & Sekitar Danau",
                "deskripsi": "Tanaman tepi danau, pakis air, herba lembab riparian",
                "ketinggian": "1.860 mdpl",
                "spesies": 6,
                "emoji": "🏞️"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.95576, -7.90150],
                    [112.95100, -7.89900],
                    [112.94624, -7.90150],
                    [112.94624, -7.90650],
                    [112.95100, -7.90900],
                    [112.95576, -7.90650],
                    [112.95576, -7.90150]
                ]]
            }
        },
        # ── 3. Tepi Hutan & Zona Transisi ────────────────────────────────
        # Center: (-7.924, 112.933) | radius: 0.0075 lat × 0.0080 lon
        # Posisi: tengah-barat, zona peralihan hutan–ladang Tengger
        {
            "type": "Feature",
            "properties": {
                "nama": "Tepi Hutan & Zona Transisi",
                "deskripsi": "Rempah-rempah tradisional Tengger, herba obat, semak transisi",
                "ketinggian": "1.850 – 2.000 mdpl",
                "spesies": 18,
                "emoji": "🌿"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.93993, -7.91650],
                    [112.93300, -7.91200],
                    [112.92607, -7.91650],
                    [112.92607, -7.93150],
                    [112.93300, -7.93600],
                    [112.93993, -7.93150],
                    [112.93993, -7.91650]
                ]]
            }
        },
        # ── 4. Zona Budidaya & Pekarangan ────────────────────────────────
        # Center: (-7.937, 112.948) | radius: 0.0060 lat × 0.0065 lon
        # Posisi: tengah, desa-desa Tengger (Ngadisari, Wonokitri, dll.)
        {
            "type": "Feature",
            "properties": {
                "nama": "Zona Budidaya & Pekarangan",
                "deskripsi": "Tanaman budidaya Tengger, rempah pekarangan, sayuran tradisional",
                "ketinggian": "1.800 – 2.000 mdpl",
                "spesies": 5,
                "emoji": "🏡"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.95363, -7.93400],
                    [112.94800, -7.93100],
                    [112.94237, -7.93400],
                    [112.94237, -7.94000],
                    [112.94800, -7.94300],
                    [112.95363, -7.94000],
                    [112.95363, -7.93400]
                ]]
            }
        },
        # ── 5. Savana Bromo & Lereng Terbuka ─────────────────────────────
        # Center: (-7.945, 112.968) | radius: 0.0100 lat × 0.0110 lon
        # Posisi: tengah-timur, lautan pasir & savana Bromo, kawasan terluas
        {
            "type": "Feature",
            "properties": {
                "nama": "Savana Bromo & Lereng Terbuka",
                "deskripsi": "Padang savana vulkanik, rumput, herba terbuka, bunga liar",
                "ketinggian": "2.000 – 2.200 mdpl",
                "spesies": 20,
                "emoji": "🌾"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.97753, -7.94000],
                    [112.96800, -7.93500],
                    [112.95847, -7.94000],
                    [112.95847, -7.95000],
                    [112.96800, -7.95500],
                    [112.97753, -7.95000],
                    [112.97753, -7.94000]
                ]]
            }
        },
        # ── 6. Kantong Air & Lembah ──────────────────────────────────────
        # Center: (-7.960, 112.937) | radius: 0.0065 lat × 0.0070 lon
        # Posisi: selatan-barat, lembah sumber mata air TNBTS
        {
            "type": "Feature",
            "properties": {
                "nama": "Kantong Air & Lembah",
                "deskripsi": "Herba air, tanaman lembab, sumber mata air TNBTS",
                "ketinggian": "1.700 – 1.900 mdpl",
                "spesies": 6,
                "emoji": "💧"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.94306, -7.95675],
                    [112.93700, -7.95350],
                    [112.93094, -7.95675],
                    [112.93094, -7.96325],
                    [112.93700, -7.96650],
                    [112.94306, -7.96325],
                    [112.94306, -7.95675]
                ]]
            }
        },
        # ── 7. Lereng Semeru & Dataran Tinggi ────────────────────────────
        # Center: (-7.980, 112.987) | radius: 0.0110 lat × 0.0120 lon
        # Posisi: tenggara, lereng Gunung Semeru, kawasan luas
        {
            "type": "Feature",
            "properties": {
                "nama": "Lereng Semeru & Dataran Tinggi",
                "deskripsi": "Sayuran dataran tinggi, cemara gunung, purwoceng, stroberi tengger",
                "ketinggian": "2.200 – 2.500 mdpl",
                "spesies": 13,
                "emoji": "🏔️"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [112.99739, -7.97450],
                    [112.98700, -7.96900],
                    [112.97661, -7.97450],
                    [112.97661, -7.98550],
                    [112.98700, -7.99100],
                    [112.99739, -7.98550],
                    [112.99739, -7.97450]
                ]]
            }
        },
        # ── 8. Zona Pesisir & Pantai Selatan ─────────────────────────────
        # Center: (-8.020, 112.993) | radius: 0.0090 lat × 0.0110 lon
        # Posisi: jauh selatan, zona pesisir, terpisah dari kawasan atas
        {
            "type": "Feature",
            "properties": {
                "nama": "Zona Pesisir & Pantai Selatan",
                "deskripsi": "Pohon pantai, semak pesisir, tanaman mangrove transisi",
                "ketinggian": "0 – 400 mdpl",
                "spesies": 4,
                "emoji": "🌊"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [113.00253, -8.01550],
                    [112.99300, -8.01100],
                    [112.98347, -8.01550],
                    [112.98347, -8.02450],
                    [112.99300, -8.02900],
                    [113.00253, -8.02450],
                    [113.00253, -8.01550]
                ]]
            }
        }
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# MUSIK
# ─────────────────────────────────────────────────────────────────────────────
video_id = "imGaOIm5HOk"
col_m1, col_m2 = st.columns([1, 5])
with col_m1:
    if st.button(
        "🔊 Matikan Musik" if st.session_state.music_playing else "🔇 Nyalakan Musik",
        key="music_toggle"
    ):
        st.session_state.music_playing = not st.session_state.music_playing
        st.rerun()

if st.session_state.music_playing:
    st.markdown(f"""
    <div style="position:fixed;bottom:60px;right:10px;z-index:9999;width:300px;
                height:80px;background:rgba(0,0,0,.8);border-radius:10px;
                padding:5px;border:1px solid #4CAF50;">
        <iframe width="100%" height="80"
            src="https://www.youtube.com/embed/{video_id}?autoplay=1&loop=1&playlist={video_id}&controls=1&showinfo=0"
            frameborder="0" allow="autoplay;encrypted-media" allowfullscreen
            style="border-radius:5px;"></iframe>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🌿 WebGIS Resiliensi Kesehatan Terhadap Potensi Bencana<br>
    Bromo – Kaldera Tengger – Semeru<br>Melalui Konsumsi Tanaman Herbal</h1>
    <p>Taman Nasional Bromo Tengger Semeru (TNBTS) • 86 Spesies Tanaman • 8 Kawasan Ekologi • 41 Desa</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header-new">
        <h3>🏔️ Bromo – Tengger – Semeru</h3>
        <p>Saat Matahari Terbit</p>
    </div>""", unsafe_allow_html=True)

    st.image(
        "https://adipandang.wordpress.com/wp-content/uploads/2026/03/"
        "3ffcb908-4978-4464-bf12-178125ad26ec.jpg",
        use_container_width=True
    )
    st.markdown(
        '<p class="image-caption" style="color:white!important;">Tim Ekspedisi Penelitian</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.markdown("### 📋 Menu Navigasi")
    menu_options = ["Peta Sebaran", "Peta 3D Pegunungan", "Data Tanaman", "Statistik", "Informasi"]
    menu_icons   = ["🗺️", "🏔️", "📋", "📊", "ℹ️"]
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed",
        key="menu_radio"
    )
    st.markdown("---")

    st.markdown("### 🔍 Filter Data")
    semua_tanaman = [
        'Adas','Ajeran putih','Alang-alang','Andong','Awar-awar',
        'Bakung','Bawang merah','Bawang putih','Beluntas','Bidara laut',
        'Buah klandingan','Bunga hariang','Bunga Matahari','Calingan','Cemplukan',
        'Daun dadap','Dringu','Ganjan','Ganyong','Jahe',
        'Jambu wer','Jarak','Jarak merah','Jenggot wesi','Jenis Talas',
        'Kayu Ampet','Kayu putih','Keladi tikus','Keladi/sente-sentean','Kencana Ungu',
        'Kencur','Keningar','Kesimbukan','Kunyit','Lengkuas',
        'Lili-lilian liar','Lobak','Lombok terong','Lombok udel','Paitan',
        'Pakis','Pakis (fern)','Pakis/paku pedang','Paku rane/paku kawat','Paku sigung',
        'Parijoto','Pecut kuda','Pisang','Pulosari','Purwoceng',
        'Air kuncup kecubung gunung','Akar sempretan',
        'Daun kancing-kancing/semanggi liar','Daun-daunan hutan mirip garutan',
        'Ranti','Rumput asystasia','Rumput hutan','Rumput karpet',
        'Rumput teki-tekian (nutrush)','Tumbuhan herba bawah (Amischotolype)',
        'Sawi ireng','Semanggi','Sengganen/Senggani','Sirih','Snikir',
        'Stroberi tengger','Suplir','Suri pandak','Tapak liman','Teklan',
        'Tepung otot','Tirem','Trabasan','Vervain','Wedusan',
        'Ketumbar','Teh-tehan','Cemara besi','Simbaran','Kenikir',
        'Tumbuhan herba bawah (Commelina)','Rumput ilalang','Paku sarang burung',
        'Anggrek tanah','Jahe merah','Cemara gunung'
    ]
    selected_tanaman = st.multiselect(
        "Pilih Nama Tanaman",
        options=["Semua"] + sorted(semua_tanaman),
        default=["Semua"],
        help="Pilih satu atau lebih tanaman"
    )

    kawasan_options = [
        "Semua Kawasan",
        "Blok Ireng-Ireng & Hutan Atas",
        "Kantong Air & Lembah",
        "Lereng Semeru & Dataran Tinggi",
        "Ranu Darungan & Sekitar Danau",
        "Savana Bromo & Lereng Terbuka",
        "Tepi Hutan & Zona Transisi",
        "Zona Budidaya & Pekarangan",
        "Zona Pesisir & Pantai Selatan",
    ]
    selected_kawasan = st.selectbox("Filter Kawasan Ekologi", kawasan_options)

    st.markdown("---")
    st.markdown("### 🗂️ Layer Control")
    c1, c2 = st.columns(2)
    with c1:
        show_desa_geojson = st.checkbox("🏘️ Batas Desa",     value=True)
        show_kawasan      = st.checkbox("🏔️ Kawasan Ekologi", value=True)
    with c2:
        show_tanaman = st.checkbox("🌿 Tanaman", value=True)

    st.markdown("### 🏔️ Kontrol Tampilan 3D")
    map_height_3d = st.slider("Tinggi Iframe", 400, 800, 600, step=50)

    st.markdown("---")
    st.markdown("### 📁 Status File")
    if os.path.exists('Desa_TNBTS.geojson'):
        fsz = os.path.getsize('Desa_TNBTS.geojson') / 1024
        st.markdown(f"""
        <div class="status-badge">
            ✅ <b>Desa_TNBTS.geojson</b><br><small>{fsz:.1f} KB • 41 desa</small>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="status-badge" style="border-left-color:#f44336;">
            ❌ <b>Desa_TNBTS.geojson</b><br><small>File tidak ditemukan</small>
        </div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class="status-badge">
        🌿 <b>Database Tanaman</b><br><small>86 spesies teridentifikasi</small>
    </div>
    <div class="status-badge">
        🏔️ <b>Layer Kawasan</b><br><small>8 kawasan ekologi TNBTS</small>
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA TANAMAN
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_tanaman_herbal_data():
    records = [
        (1,  'Adas',                        'Foeniculum vulgare',               'Herba', 'Pencernaan',                -7.9385, 112.9515, 'Zona Budidaya & Pekarangan',           1900, 'Sekitar Desa Ngadisari & Wonokitri',    'Ngadisari, Wonokitri'),
        (2,  'Ajeran putih',                'Bidens pilosa L.',                 'Herba', 'Antiradang',                -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Lautan Pasir & Savana Bromo',           'Seluruh desa penyangga'),
        (3,  'Alang-alang',                 'Imperata cylindrica L.',           'Rumput','Diuretik',                  -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Savana Tengger',                 'Ngadas, Argosari'),
        (4,  'Andong',                      'Cordyline fruticosa Linn',         'Pohon', 'Menghentikan pendarahan',   -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah Sumber Air TNBTS',              'Ngadas, Ranupani'),
        (5,  'Awar-awar',                   'Ficus septica Burm.f.',            'Pohon', 'Antiradang',                -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan Cemara – Desa Ngadisari',   'Ngadisari, Wonokitri'),
        (6,  'Bakung',                      'Crinum asiaticium L.',             'Herba', 'Mengurangi bengkak',        -7.9150, 112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan',                   'Ranupani'),
        (7,  'Bawang merah',                'Allium cepa L.',                   'Herba', 'Penurun demam',             -7.9385, 112.9515, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pertanian Tengger',              'Seluruh desa penyangga'),
        (8,  'Bawang putih',                'Allium sativum',                   'Herba', 'Menurunkan tekanan darah',  -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Atas Semeru – Ranupani',         'Ranupani, Argosari'),
        (9,  'Beluntas',                    'Pluchea indica',                   'Semak', 'Pencernaan',                -8.0200, 112.9950, 'Zona Pesisir & Pantai Selatan',        300,  'Zona Pesisir Selatan TNBTS',            'Desa pesisir selatan'),
        (10, 'Bidara laut',                 'Strychnos lucida',                 'Pohon', 'Pereda nyeri',              -8.0180, 112.9900, 'Zona Pesisir & Pantai Selatan',        250,  'Pantai Selatan – Batas TNBTS',          'Desa pesisir selatan'),
        (11, 'Buah klandingan',             'Lucas lavandulifolia',             'Pohon', 'Batuk & pilek',             -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Zona Transisi Hutan – Ladang',          'Ngadisari, Wonokitri'),
        (12, 'Bunga hariang',               'Begonia',                         'Bunga', 'Batuk',                     -7.9800, 112.9850, 'Lereng Semeru & Dataran Tinggi',       2300, 'Lereng Semeru Barat Daya',              'Ranupani'),
        (13, 'Bunga Matahari',              'Helianthus annuus',               'Bunga', 'Penurun demam',             -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana & Ladang Bromo',                 'Ngadisari, Argosari'),
        (14, 'Calingan',                    'Centella asiatica L.',             'Herba', 'Penyembuhan luka',          -7.9150, 112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Bantaran Ranu Darungan',                'Ranupani'),
        (15, 'Cemplukan',                   'Physalis minima',                  'Herba', 'Penurun demam',             -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana Bromo',                     'Ngadas, Argosari'),
        (16, 'Daun dadap',                  'Erythrina variegata L.',           'Pohon', 'Pereda nyeri',              -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Batas Hutan Cemara & Ladang',           'Ngadisari'),
        (17, 'Dringu',                      'Acorus calamus L.',                'Herba', 'Pencernaan',                -7.9150, 112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Pinggir Air',     'Ranupani'),
        (18, 'Ganjan',                      'Artemisia vulgaris',               'Herba', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Hutan Primer',       'Ireng-Ireng'),
        (19, 'Ganyong',                     'Canna indica L.',                  'Herba', 'Pencernaan',                -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah Basah – Sumber Mata Air',       'Ngadas, Ranupani'),
        (20, 'Jahe',                        'Zingiber Officinale Rocs',         'Herba', 'Pencernaan',                -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Campuran Tepi Hutan',             'Seluruh desa penyangga'),
        (21, 'Jambu wer',                   'Prunus persica',                   'Pohon', 'Diare',                     -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Kebun Desa Ranupani',  'Ranupani'),
        (22, 'Jarak',                       'Jatropha curcas',                  'Pohon', 'Pencahar',                  -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana & Batas Ladang',            'Ngadisari, Cemoro Lawang'),
        (23, 'Jarak merah',                 'Jatropha curcas L.',               'Pohon', 'Obat luka',                 -7.9480, 112.9640, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana – Agak Ke Utara',          'Cemoro Lawang'),
        (24, 'Jenggot wesi',                'Usnea Barbata Fries',              'Lumut', 'Antibakteri',               -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2500, 'Pohon Tua Blok Ireng-Ireng',            'Ireng-Ireng'),
        (25, 'Jenis Talas',                 'Homalomena sp.',                   'Herba', 'Masuk angin',               -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah Basah – Sekitar Mata Air',      'Ngadas'),
        (26, 'Kayu Ampet',                  'Alstonia macrophylla',             'Pohon', 'Sakit perut',               -8.0180, 112.9900, 'Zona Pesisir & Pantai Selatan',        250,  'Hutan Pantai Selatan',                  'Desa pesisir selatan'),
        (27, 'Kayu putih',                  'Melaleuca leucadendra',            'Pohon', 'Masuk angin',               -8.0200, 112.9950, 'Zona Pesisir & Pantai Selatan',        300,  'Hutan Pantai – Zona Penyangga Selatan', 'Desa pesisir selatan'),
        (28, 'Keladi tikus',                'Typhonium flagelliforme',          'Herba', 'Antikanker',                -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Bawah Tegakan Hutan Cemara',            'Ngadisari'),
        (29, 'Keladi/sente-sentean',        'Alocasia sp.',                     'Herba', 'Obat bisul',                -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah Sungai – Naungan Lebat',        'Ngadas, Ranupani'),
        (30, 'Kencana Ungu',                'Ruellia',                         'Herba', 'Penurun gula darah',        -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Jalan Savana Bromo',               'Ngadisari, Cemoro Lawang'),
        (31, 'Kencur',                      'Kaempferia galanga L.',            'Herba', 'Batuk & pilek',             -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah Tradisional',              'Ngadisari, Wonokitri'),
        (32, 'Keningar',                    'Ageratina sp.',                    'Herba', 'Menghentikan pendarahan',   -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Zona Terbuka',          'Ranupani, Argosari'),
        (33, 'Kesimbukan',                  'Paederia foetida',                 'Herba', 'Menghentikan pendarahan',   -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan – Merambat Di Pohon',       'Wonokitri, Ngadisari'),
        (34, 'Kunyit',                      'Curcuma domestica Rumph.',         'Herba', 'Antiradang',                -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah Tradisional',              'Seluruh desa penyangga'),
        (35, 'Lengkuas',                    'Alpinia galanga',                  'Herba', 'Masuk angin',               -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Campuran – Tepi Hutan',           'Seluruh desa penyangga'),
        (36, 'Lili-lilian liar',            'Molineria sp.',                    'Herba', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Blok Ireng-Ireng',         'Ireng-Ireng'),
        (37, 'Lobak',                       'Raphanus sativus L.',              'Herba', 'Pencernaan',                -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Ladang Dataran Tinggi Ranupani',        'Ranupani, Argosari'),
        (38, 'Lombok terong',               'Solanum torvum Sw.',               'Herba', 'Tekanan darah tinggi',      -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana – Tumbuh Liar',             'Ngadisari, Cemoro Lawang'),
        (39, 'Lombok udel',                 'Capsicum frutescens L.',           'Herba', 'Menghangatkan tubuh',       -7.9385, 112.9515, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pekarangan Desa Tengger',        'Ngadisari, Wonokitri'),
        (40, 'Paitan',                      'Tithonia diversifolia',            'Herba', 'Penurun demam',             -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Jalan – Batas Hutan & Ladang',    'Ngadisari'),
        (41, 'Pakis',                       'Davallia',                        'Pakis', 'Pencernaan',                -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer Blok Ireng-Ireng',  'Ireng-Ireng'),
        (42, 'Pakis (fern)',                'Phegopteris',                     'Pakis', 'Pencernaan',                -7.9060, 112.9260, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Naungan Lebat',     'Ireng-Ireng'),
        (43, 'Pakis/paku pedang',           'Nephrolepis sp.',                  'Pakis', 'Diuretik',                  -7.9150, 112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Danau Ranu Darungan',             'Ranupani'),
        (44, 'Paku rane/paku kawat',        'Selaginella sp.',                  'Pakis', 'Melancarkan peredaran darah',-7.9050,112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2500, 'Bebatuan Hutan Primer',                 'Ireng-Ireng'),
        (45, 'Paku sigung',                 'Didymochlaena',                   'Pakis', 'Penyembuhan luka',          -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Bawah Tegakan',        'Ranupani'),
        (46, 'Parijoto',                    'Medinilla speciosa',               'Herba', 'Kesuburan',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Tanaman Endemik',   'Ireng-Ireng'),
        (47, 'Pecut kuda',                  'Stachytarpheta sp.',               'Herba', 'Penurun demam',             -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Tumbuh Liar',             'Ngadas'),
        (48, 'Pisang',                      'Musa paradisiaca',                 'Pohon', 'Diare',                     -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah – Sekitar Sumber Air',           'Ngadas, Ranupani'),
        (49, 'Pulosari',                    'Alyxia reinwardtii Blume.',        'Herba', 'Batuk & pilek',             -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Semak Bawah Pohon', 'Ireng-Ireng'),
        (50, 'Purwoceng',                   'Pimpinella pruatjan',              'Herba', 'Kesuburan',                 -7.9820, 112.9880, 'Lereng Semeru & Dataran Tinggi',       2400, 'Lereng Semeru – Tanaman Endemik Jawa', 'Ranupani'),
        (51, 'Air kuncup kecubung gunung',  'Brugmansia candida',               'Perdu', 'Pereda nyeri, asma',        -7.9800, 112.9850, 'Lereng Semeru & Dataran Tinggi',       2300, 'Lereng Semeru – Tepi Vegetasi',        'Ranupani'),
        (52, 'Akar sempretan',              'Mikania cordata',                  'Herba', 'Antiradang, diuretik',      -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Merambat di Tepi Hutan Cemara',         'Ngadisari, Wonokitri'),
        (53, 'Daun kancing-kancing/semanggi liar','Desmodium sp.',             'Herba', 'Anti radang, batuk',        -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan – Tanah Lembab',             'Ngadisari'),
        (54, 'Daun-daunan hutan mirip garutan','Stachyphrynium sp.',            'Herba', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer',                   'Ireng-Ireng'),
        (55, 'Ranti',                       'Tinospora crispa L. Miers',       'Herba', 'Antimalaria',               -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Merambat di Tepi Hutan',                'Ngadisari, Wonokitri'),
        (56, 'Rumput asystasia',            'Asystasia sp.',                    'Herba', 'Anti radang',               -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Padang Terbuka',         'Cemoro Lawang'),
        (57, 'Rumput hutan',                'Oplismenus sp.',                   'Rumput','Anti radang',               -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer Blok Ireng-Ireng',  'Ireng-Ireng'),
        (58, 'Rumput karpet',               'Axonopus sp.',                    'Rumput','Obat luka',                  -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Terbuka – Savana Tengger',       'Ngadas, Argosari'),
        (59, 'Rumput teki-tekian (nutrush)','Scleria sp.',                     'Rumput','Diuretik',                   -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Savana – Tepian Lembab',         'Ngadas'),
        (60, 'Tumbuhan herba bawah (Amischotolype)','Amischotolype sp.',       'Herba', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Blok Ireng-Ireng',         'Ireng-Ireng'),
        (61, 'Sawi ireng',                  'Brassica juncea',                  'Herba', 'Pencernaan',                -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Ladang Sayuran Dataran Tinggi',         'Ranupani, Argosari'),
        (62, 'Semanggi',                    'Marsilea crenata',                 'Pakis', 'Melancarkan peredaran darah',-7.9150,112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Di Air',          'Ranupani'),
        (63, 'Sengganen/Senggani',          'Melastoma malabathricum L.',       'Semak', 'Obat diare',                -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Semak Terbuka',           'Ngadas, Argosari'),
        (64, 'Sirih',                       'Piper betle Linn',                 'Semak', 'Antiseptik',                -7.9385, 112.9515, 'Zona Budidaya & Pekarangan',           1900, 'Pekarangan Desa Tengger',               'Ngadisari, Wonokitri'),
        (65, 'Snikir',                      'C. Caudatus',                     'Herba', 'Penyembuhan luka',          -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Tumbuh Liar',            'Cemoro Lawang, Ngadisari'),
        (66, 'Stroberi tengger',            'Rubus Idaeus L.',                  'Perdu', 'Kesehatan darah',           -7.9820, 112.9880, 'Lereng Semeru & Dataran Tinggi',       2400, 'Lereng Semeru – Khas Dataran Tinggi',  'Ranupani'),
        (67, 'Suplir',                      'Adiantum',                        'Pakis', 'Batuk, darah tinggi',       -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Bebatuan Lembab',      'Ranupani'),
        (68, 'Suri pandak',                 'Plantago mayor Linn.',             'Herba', 'Penyembuhan luka',          -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Jalan Hutan',                      'Ngadisari'),
        (69, 'Tapak liman',                 'Elephantopus scaber L.',           'Herba', 'Penurun demam',             -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana & Jalur Trekking',          'Ngadas, Argosari'),
        (70, 'Teklan',                      'Eupatorium riparium',              'Herba', 'Obat demam',                -7.9150, 112.9400, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Bantaran',        'Ranupani'),
        (71, 'Tepung otot',                 'Borreria laevis',                  'Herba', 'Pereda nyeri otot',         -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Padang Rumput Savana',                  'Ngadisari, Cemoro Lawang'),
        (72, 'Tirem',                       'Chromolaena odoratum',             'Semak', 'Sakit perut',               -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Semak Invasif',           'Ngadas, Argosari'),
        (73, 'Trabasan',                    'Ageratum conyzoides',              'Herba', 'Obat luka',                 -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan & Ladang',                   'Ngadisari, Wonokitri'),
        (74, 'Vervain',                     'Stachytarpheta mutabilis Vahl',    'Herba', 'Penurun demam',             -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Tepian Jalan',           'Cemoro Lawang'),
        (75, 'Wedusan',                     'Ageratum conyzoides',              'Herba', 'Obat luka',                 -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Batas Ladang & Hutan Cemara',           'Ngadisari'),
        (76, 'Ketumbar',                    'Coriandrum sativum Linn.',         'Herba', 'Pencernaan',                -7.9385, 112.9515, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pekarangan Desa Tengger',        'Seluruh desa penyangga'),
        (77, 'Teh-tehan',                   'Eclipta prostrata Linn.',          'Herba', 'Kesehatan hati',            -7.9550, 112.9450, 'Kantong Air & Lembah',                 1750, 'Lembah – Pinggir Aliran Air',           'Ngadas'),
        (78, 'Cemara besi',                 'Casuarina junghuhniana Miq.',      'Pohon', 'Penyembuhan luka',          -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Tegakan Cemara Khas',  'Ranupani'),
        (79, 'Simbaran',                    'Peperomia sp.',                    'Herba', 'Penyembuhan luka',          -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Epifit di Pohon Tua Blok Ireng-Ireng', 'Ireng-Ireng'),
        (80, 'Kenikir',                     'Cosmos caudatus Kunth',            'Herba', 'Antioksidan',               -7.9200, 112.9320, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan & Ladang',                   'Ngadisari, Wonokitri'),
        (81, 'Tumbuhan herba bawah (Commelina)','Commelina sp.',               'Herba', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Lembab Blok Ireng-Ireng', 'Ireng-Ireng'),
        (82, 'Rumput ilalang',              'Imperata cylindrica',              'Rumput','Diuretik',                  -7.9425, 112.9700, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Terbuka Savana Tengger',         'Ngadas, Argosari'),
        (83, 'Paku sarang burung',          'Asplenium nidus',                  'Pakis', 'Obat luka',                 -7.9050, 112.9250, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Epifit di Pohon – Blok Ireng-Ireng',   'Ireng-Ireng'),
        (84, 'Anggrek tanah',               'Spathoglottis plicata',            'Bunga', 'Antioksidan',               -7.9500, 112.9620, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana Bromo – Semi Terbuka',     'Ngadisari, Cemoro Lawang'),
        (85, 'Jahe merah',                  'Zingiber officinale var. rubrum',  'Herba', 'Antiradang',                -7.9250, 112.9380, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah & Tepi Hutan',             'Ngadisari, Wonokitri'),
        (86, 'Cemara gunung',               'Casuarina junghuhniana',           'Pohon', 'Penyembuhan luka',          -7.9750, 112.9820, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Dominant Trees',       'Ranupani'),
    ]

    df = pd.DataFrame(records, columns=[
        'id','nama_tanaman','nama_latin','jenis','fungsi_utama',
        'latitude','longitude','kawasan','ketinggian','lokasi_detail','desa'
    ])
    df['status_konservasi'] = 'Umum'
    df.loc[df['nama_tanaman'].isin(['Purwoceng','Parijoto','Anggrek tanah']),
           'status_konservasi'] = 'Dilindungi'
    np.random.seed(42)
    df['jumlah'] = np.random.randint(10, 500, len(df))
    return df


@st.cache_data
def load_desa_geojson():
    try:
        if not os.path.exists('Desa_TNBTS.geojson'):
            return gpd.GeoDataFrame()
        with open('Desa_TNBTS.geojson', 'r', encoding='utf-8') as f:
            data = json.load(f)
        gdf = gpd.GeoDataFrame.from_features(data["features"])
        gdf.crs = "EPSG:4326"
        return gdf
    except Exception as e:
        st.sidebar.error(f"❌ Error loading GeoJSON: {e}")
        return gpd.GeoDataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# LOAD & FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
df_tanaman = load_tanaman_herbal_data()
gdf_desa   = load_desa_geojson()

if "Semua" not in selected_tanaman and selected_tanaman:
    df_tanaman_filtered = df_tanaman[df_tanaman['nama_tanaman'].isin(selected_tanaman)]
else:
    df_tanaman_filtered = df_tanaman.copy()

if selected_kawasan != "Semua Kawasan":
    df_tanaman_filtered = df_tanaman_filtered[
        df_tanaman_filtered['kawasan'] == selected_kawasan
    ]

# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI BUAT PETA
# ─────────────────────────────────────────────────────────────────────────────
def create_tnbts_map():
    m = folium.Map(
        location=[-7.955, 112.953],
        zoom_start=11,
        tiles='OpenStreetMap',
        name='OpenStreetMap'
    )

    # Tile tambahan
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='🛰️ Satelit'
    ).add_to(m)
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap', name='🗻 Terrain'
    ).add_to(m)

    # ── LAYER 1: 8 Kawasan Ekologi (Polygon) ─────────────────────────────
    # Setiap kawasan digambar sebagai GeoJson tersendiri dengan:
    #   • GeoJsonTooltip (field-based, sticky=False) → muncul hanya saat hover
    #   • folium.Popup (HTML custom) → daftar lengkap nama tanaman saat klik
    if show_kawasan:
        kawasan_group = folium.FeatureGroup(name='🏔️ Kawasan Ekologi TNBTS', show=True)

        for feat in KAWASAN_GEOJSON["features"]:
            props      = feat["properties"]
            nama_kw    = props["nama"]
            hex_col    = KAWASAN_HEX.get(nama_kw, "#4CAF50")
            spesies_n  = props["spesies"]
            deskripsi  = props["deskripsi"]
            ketinggian = props["ketinggian"]
            emoji      = props["emoji"]

            # ── Ambil daftar nama tanaman dari df_tanaman ──────────────────
            tanaman_kw = df_tanaman[
                df_tanaman["kawasan"] == nama_kw
            ]["nama_tanaman"].tolist()

            # Buat badge HTML untuk setiap tanaman
            badges_html = "".join([
                f'<span style="display:inline-block;background:#E8F5E9;'
                f'color:#1B5E20;border:1px solid {hex_col};border-radius:12px;'
                f'padding:2px 8px;font-size:11px;margin:2px 2px;">'
                f'🌿 {t}</span>'
                for t in sorted(tanaman_kw)
            ])

            # ── Popup HTML lengkap (muncul saat klik) ─────────────────────
            popup_html = f"""
            <div style="font-family:Arial;width:320px;max-width:340px;">
                <div style="background:{hex_col};color:white;
                            padding:10px 14px;border-radius:8px 8px 0 0;">
                    <span style="font-size:18px;">{emoji}</span>
                    <b style="font-size:13px;margin-left:6px;">{nama_kw}</b>
                </div>
                <div style="padding:10px 12px;border:1px solid #ddd;
                            border-top:none;border-radius:0 0 8px 8px;">
                    <table style="font-size:12px;width:100%;
                                  border-collapse:collapse;margin-bottom:8px;">
                        <tr style="background:#f1f8e9;">
                            <td style="padding:4px 8px;font-weight:bold;
                                       color:#555;width:90px;">Ketinggian</td>
                            <td style="padding:4px 8px;">⛰️ {ketinggian}</td>
                        </tr>
                        <tr>
                            <td style="padding:4px 8px;font-weight:bold;color:#555;">
                                Jml. Spesies</td>
                            <td style="padding:4px 8px;">
                                <b style="color:{hex_col};">{spesies_n}</b> spesies herbal
                            </td>
                        </tr>
                        <tr style="background:#f1f8e9;">
                            <td style="padding:4px 8px;font-weight:bold;color:#555;">
                                Vegetasi</td>
                            <td style="padding:4px 8px;">{deskripsi}</td>
                        </tr>
                    </table>
                    <div style="font-weight:bold;color:#2E7D32;font-size:12px;
                                margin-bottom:5px;border-top:1px solid #e0e0e0;
                                padding-top:7px;">
                        🌿 Daftar Tanaman Herbal ({spesies_n} spesies):
                    </div>
                    <div style="display:flex;flex-wrap:wrap;gap:2px;
                                max-height:160px;overflow-y:auto;padding:2px;">
                        {badges_html}
                    </div>
                </div>
            </div>"""

            # ── Tooltip ringkas (muncul saat hover) ───────────────────────
            # Gunakan GeoJsonTooltip field-based agar TIDAK jadi label permanen.
            # Sisipkan field tooltip ke properties copy
            feat_with_tt = {
                "type": feat["type"],
                "geometry": feat["geometry"],
                "properties": {
                    **props,
                    "fill":          hex_col,
                    "tt_nama":       f"{emoji} {nama_kw}",
                    "tt_info":       f"{spesies_n} spesies herbal  |  ⛰️ {ketinggian}",
                }
            }

            folium.GeoJson(
                feat_with_tt,
                style_function=lambda f: {
                    "fillColor":   f["properties"]["fill"],
                    "color":       f["properties"]["fill"],
                    "weight":      2.5,
                    "fillOpacity": 0.18,
                    "dashArray":   "5, 4",
                },
                highlight_function=lambda f: {
                    "fillColor":   f["properties"]["fill"],
                    "color":       f["properties"]["fill"],
                    "weight":      4,
                    "fillOpacity": 0.40,
                    "dashArray":   "",
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["tt_nama", "tt_info"],
                    aliases=["", ""],
                    localize=False,
                    sticky=False,
                    labels=False,
                    style=(
                        "background-color:white;"
                        "border:1px solid #ccc;"
                        "border-radius:6px;"
                        "padding:6px 10px;"
                        "font-family:Arial;"
                        "font-size:12px;"
                        "box-shadow:2px 2px 6px rgba(0,0,0,.15);"
                        "pointer-events:none;"
                    ),
                ),
                popup=folium.Popup(popup_html, max_width=360),
            ).add_to(kawasan_group)

        kawasan_group.add_to(m)

    # ── LAYER 2: Batas Desa ───────────────────────────────────────────────
    if show_desa_geojson and not gdf_desa.empty:
        desa_group = folium.FeatureGroup(name='🏘️ Batas Desa', show=True)
        available_fields, field_aliases = [], []
        for col, alias in [
            ('nama_kelur','Desa:'),('nama_kecam','Kecamatan:'),
            ('nama_kabko','Kabupaten:'),('jumlah_pen','Penduduk:')
        ]:
            if col in gdf_desa.columns:
                available_fields.append(col)
                field_aliases.append(alias)

        folium.GeoJson(
            gdf_desa,
            name='Desa',
            style_function=lambda f: {
                'fillColor':'#ffeda0','color':'#e65100',
                'weight':1.5,'fillOpacity':.15},
            highlight_function=lambda f: {
                'fillColor':'#fffde7','color':'#bf360c',
                'weight':3,'fillOpacity':.45},
            tooltip=folium.GeoJsonTooltip(
                fields=available_fields, aliases=field_aliases),
            popup=folium.GeoJsonPopup(
                fields=['nama_kelur','nama_kecam','nama_kabko','kode','jumlah_pen'],
                aliases=['Desa','Kecamatan','Kabupaten','Kode','Jumlah Penduduk'],
                max_width=300
            )
        ).add_to(desa_group)
        desa_group.add_to(m)

    # ── LAYER 3: Marker Tanaman ───────────────────────────────────────────
    if show_tanaman and not df_tanaman_filtered.empty:
        tanaman_group = folium.FeatureGroup(name='🌿 Sebaran Tanaman Herbal', show=True)

        for _, row in df_tanaman_filtered.iterrows():
            mk_color = JENIS_COLOR.get(row['jenis'], 'blue')
            kw_color = KAWASAN_HEX.get(row['kawasan'], '#555555')

            popup_html = f"""
            <div style="font-family:Arial;min-width:270px;max-width:300px;padding:4px;">
                <div style="background:{kw_color};color:white;padding:8px 10px;
                            border-radius:6px 6px 0 0;margin:-4px -4px 8px -4px;">
                    <b style="font-size:15px;">🌿 {row['nama_tanaman']}</b><br>
                    <i style="font-size:11px;opacity:.85;">{row['nama_latin']}</i>
                </div>
                <table style="font-size:12px;width:100%;border-collapse:collapse;">
                    <tr style="background:#f9fbe7;">
                        <td style="padding:4px 6px;font-weight:bold;color:#555;width:90px;">Jenis</td>
                        <td style="padding:4px 6px;">{row['jenis']}</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Fungsi</td>
                        <td style="padding:4px 6px;color:#1a6b2a;font-weight:600;">{row['fungsi_utama']}</td>
                    </tr>
                    <tr style="background:#f9fbe7;">
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Kawasan</td>
                        <td style="padding:4px 6px;">
                            <span style="background:{kw_color};color:white;padding:2px 7px;
                                         border-radius:12px;font-size:10px;">{row['kawasan']}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Lokasi</td>
                        <td style="padding:4px 6px;">{row['lokasi_detail']}</td>
                    </tr>
                    <tr style="background:#f9fbe7;">
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Desa</td>
                        <td style="padding:4px 6px;">{row['desa']}</td>
                    </tr>
                    <tr>
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Ketinggian</td>
                        <td style="padding:4px 6px;">⛰️ {row['ketinggian']:,} mdpl</td>
                    </tr>
                    <tr style="background:#f9fbe7;">
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Status</td>
                        <td style="padding:4px 6px;">
                            {'🔒 <b style="color:#c62828;">Dilindungi</b>'
                             if row['status_konservasi'] == 'Dilindungi'
                             else '✅ Umum'}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:4px 6px;font-weight:bold;color:#555;">Koordinat</td>
                        <td style="padding:4px 6px;font-size:11px;color:#666;">
                            {row['latitude']:.4f}, {row['longitude']:.4f}
                        </td>
                    </tr>
                </table>
            </div>"""

            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=7,
                popup=folium.Popup(popup_html, max_width=310),
                tooltip=(
                    f"🌿 <b>{row['nama_tanaman']}</b> ({row['jenis']})<br>"
                    f"<small>{row['kawasan']}</small>"
                ),
                color=mk_color,
                fill=True,
                fillColor=mk_color,
                fillOpacity=0.90,
                weight=2
            ).add_to(tanaman_group)

        tanaman_group.add_to(m)

    # ── Legenda kawasan (HTML overlay kiri bawah) ─────────────────────────
    legend_items_html = "".join([
        f'<div class="l-row">'
        f'<div class="l-box" style="background:{col};"></div>'
        f'{nm.split("&")[0].strip()} ({len(df_tanaman[df_tanaman["kawasan"]==nm])} sp.)'
        f'</div>'
        for nm, col in KAWASAN_HEX.items()
    ])
    legend_html = f"""
    <div style="position:fixed;bottom:30px;left:10px;z-index:9000;
                background:white;border-radius:10px;padding:12px 14px;
                box-shadow:0 2px 10px rgba(0,0,0,.2);font-family:Arial;
                max-width:220px;border:1px solid #e0e0e0;">
        <div style="font-weight:bold;font-size:12px;color:#1B5E20;
                    margin-bottom:8px;border-bottom:2px solid #4CAF50;padding-bottom:4px;">
            🏔️ Kawasan Ekologi TNBTS
        </div>
        {legend_items_html}
        <div style="margin-top:8px;border-top:1px solid #eee;padding-top:6px;
                    font-size:10px;color:#888;">
            Klik polygon untuk detail kawasan
        </div>
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))

    # Layer control & plugins
    folium.LayerControl(collapsed=False).add_to(m)
    try:
        from folium.plugins import Fullscreen
        Fullscreen(position='topright').add_to(m)
    except Exception:
        pass
    try:
        from folium.plugins import MeasureControl
        MeasureControl(position='bottomright',
                       primary_length_unit='kilometers').add_to(m)
    except Exception:
        pass

    return m


# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: PETA SEBARAN
# ═════════════════════════════════════════════════════════════════════════════
if selected == "Peta Sebaran":
    st.markdown("## 🗺️ Peta Interaktif Tanaman Herbal TNBTS")
    st.markdown(
        "Visualisasi sebaran **86 spesies tanaman herbal** di **8 kawasan ekologi** TNBTS. "
        "Layer kawasan dapat diaktifkan/nonaktifkan melalui Layer Control di peta."
    )

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card"><h3>{len(gdf_desa)}</h3>
            <p>🏘️ Total Desa</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card"><h3>{len(df_tanaman_filtered)}</h3>
            <p>🌿 Spesies Ditampilkan</p></div>""", unsafe_allow_html=True)
    with c3:
        kws = df_tanaman_filtered['kawasan'].nunique()
        st.markdown(f"""<div class="metric-card"><h3>{kws}</h3>
            <p>🏔️ Kawasan Aktif</p></div>""", unsafe_allow_html=True)
    with c4:
        dilind = (df_tanaman_filtered['status_konservasi'] == 'Dilindungi').sum()
        st.markdown(f"""<div class="metric-card"><h3>{dilind}</h3>
            <p>🔒 Dilindungi</p></div>""", unsafe_allow_html=True)

    # Info kawasan filter aktif
    if selected_kawasan != "Semua Kawasan":
        kw_col = KAWASAN_HEX.get(selected_kawasan, '#2E7D32')
        st.markdown(
            f'<div style="background:{kw_col};color:white;padding:.6rem 1rem;'
            f'border-radius:8px;margin-bottom:.5rem;font-weight:600;">'
            f'📍 Filter aktif: {selected_kawasan} ({len(df_tanaman_filtered)} spesies)</div>',
            unsafe_allow_html=True
        )

    # Info layer kawasan
    st.info(
        "🏔️ **Layer Kawasan Ekologi** aktif — 8 zona ditampilkan sebagai polygon berwarna. "
        "Gunakan **Layer Control** di pojok kanan atas peta untuk menampilkan/menyembunyikan layer. "
        "**Hover** pada polygon untuk melihat nama kawasan. **Klik polygon** untuk info lengkap."
    )

    # Peta
    try:
        folium_static(create_tnbts_map(), width=1200, height=640)
    except Exception as e:
        st.error(f"Error membuat peta: {e}")
        m0 = folium.Map(location=[-7.940, 112.950], zoom_start=10)
        folium_static(m0)

    # Legenda kawasan & jenis
    with st.expander("📖 Legenda & Keterangan Kawasan Ekologi", expanded=False):
        lc1, lc2 = st.columns(2)
        with lc1:
            st.markdown("**🏔️ 8 Kawasan Ekologi TNBTS (Warna Polygon):**")
            for kw, col in KAWASAN_HEX.items():
                cnt   = len(df_tanaman[df_tanaman['kawasan'] == kw])
                props = next(
                    f["properties"]
                    for f in KAWASAN_GEOJSON["features"]
                    if f["properties"]["nama"] == kw
                )
                st.markdown(
                    f'<div style="border-left:5px solid {col};padding:4px 10px;'
                    f'margin-bottom:5px;background:#fafafa;border-radius:0 6px 6px 0;">'
                    f'<span style="font-size:14px;">{props["emoji"]}</span> '
                    f'<b style="color:{col};">{kw}</b><br>'
                    f'<small>⛰️ {props["ketinggian"]} | 🌿 {cnt} spesies</small></div>',
                    unsafe_allow_html=True
                )
        with lc2:
            st.markdown("**🌿 Warna Marker Berdasarkan Jenis Tanaman:**")
            for j, c in JENIS_COLOR.items():
                cnt = len(df_tanaman[df_tanaman['jenis'] == j])
                st.markdown(
                    f'<span style="display:inline-block;width:13px;height:13px;'
                    f'background:{c};border-radius:50%;margin-right:8px;'
                    f'vertical-align:middle;border:1px solid #999;"></span>'
                    f'**{j}** ({cnt} sp.)',
                    unsafe_allow_html=True
                )

    # Tabel ringkas
    with st.expander(f"📋 Daftar {len(df_tanaman_filtered)} Tanaman yang Ditampilkan"):
        st.dataframe(
            df_tanaman_filtered[[
                'nama_tanaman','nama_latin','jenis','fungsi_utama',
                'kawasan','ketinggian','desa','status_konservasi'
            ]].rename(columns={
                'nama_tanaman':'Nama Tanaman','nama_latin':'Nama Latin',
                'jenis':'Jenis','fungsi_utama':'Fungsi',
                'kawasan':'Kawasan Ekologi','ketinggian':'mdpl',
                'desa':'Desa','status_konservasi':'Status'
            }),
            use_container_width=True, height=350, hide_index=True
        )

# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: PETA 3D
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Peta 3D Pegunungan":
    st.markdown("## 🏔️ Peta 3D Pegunungan TNBTS")
    st.markdown("Visualisasi 3D interaktif — putar 360° dengan mouse/touch")
    st.info("**🖱️ Cara penggunaan:** Klik kiri + drag untuk memutar | Scroll untuk zoom | Klik fullscreen di pojok kanan bawah")

    st.markdown(f"""
    <div style="border-radius:10px;overflow:hidden;
                box-shadow:0 4px 8px rgba(0,0,0,.2);height:{map_height_3d}px;">
        <iframe
            title="Mount Bromo / Bromo Tengger Semeru National Park"
            frameborder="0" allowfullscreen mozallowfullscreen webkitallowfullscreen
            allow="autoplay;fullscreen;xr-spatial-tracking"
            src="https://sketchfab.com/models/72f1c983ba4040eab89d75eb2b0d3e32/embed"
            style="width:100%;height:{map_height_3d}px;border:none;border-radius:10px;">
        </iframe>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1,'5','⛰️ Gunung'),(c2,'41','🏘️ Desa'),
        (c3,'86','🌿 Spesies'),(c4,'3.676','📏 mdpl tertinggi'),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card"><h3>{val}</h3>
                <p>{lbl}</p></div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: DATA TANAMAN
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Data Tanaman":
    st.markdown("## 📋 Data Tanaman Herbal TNBTS")
    tab1, tab2 = st.tabs(["🌿 86 Spesies Tanaman", "🏘️ Data Desa (GeoJSON)"])

    with tab1:
        search = st.text_input(
            "🔍 Cari (nama, fungsi, nama latin, kawasan):",
            placeholder="Contoh: antiradang / blok ireng / herba ..."
        )
        df_show = df_tanaman_filtered.copy()
        if search:
            mask = (
                df_show['nama_tanaman'].str.contains(search, case=False, na=False) |
                df_show['fungsi_utama'].str.contains(search, case=False, na=False) |
                df_show['nama_latin'].str.contains(search, case=False, na=False) |
                df_show['kawasan'].str.contains(search, case=False, na=False) |
                df_show['desa'].str.contains(search, case=False, na=False)
            )
            df_show = df_show[mask]
            st.info(f"Ditemukan **{len(df_show)}** hasil")

        st.dataframe(
            df_show[[
                'id','nama_tanaman','nama_latin','jenis','fungsi_utama',
                'kawasan','ketinggian','lokasi_detail','desa','status_konservasi'
            ]].rename(columns={
                'id':'No','nama_tanaman':'Nama Tanaman','nama_latin':'Nama Latin',
                'jenis':'Jenis','fungsi_utama':'Fungsi Utama',
                'kawasan':'Kawasan Ekologi','ketinggian':'mdpl',
                'lokasi_detail':'Lokasi Detail','desa':'Desa',
                'status_konservasi':'Status Konservasi'
            }),
            use_container_width=True, height=500, hide_index=True
        )
        cc1, cc2, cc3 = st.columns([1, 2, 1])
        with cc2:
            st.download_button(
                "📥 Download CSV Tanaman (86 Spesies)",
                data=df_tanaman_filtered.to_csv(index=False),
                file_name="tanaman_herbal_tnbts_86.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tab2:
        st.markdown("### 📊 Data Desa dari File GeoJSON")
        if not gdf_desa.empty:
            st.success(f"✅ {len(gdf_desa)} desa berhasil dimuat")
            desa_df = gdf_desa.drop('geometry', axis=1, errors='ignore')
            st.dataframe(desa_df, use_container_width=True, height=500)
            st.download_button(
                "📥 Download Data Desa (CSV)",
                data=desa_df.to_csv(index=False),
                file_name="data_desa_tnbts.csv",
                mime="text/csv"
            )
        else:
            st.error("❌ Desa_TNBTS.geojson tidak ditemukan.")

# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: STATISTIK
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal TNBTS")

    st.markdown("### 🏔️ Sebaran Spesies per Kawasan Ekologi")
    kw_counts = df_tanaman_filtered['kawasan'].value_counts()
    st.bar_chart(kw_counts, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🌿 Distribusi Jenis Tanaman")
        jenis_counts = df_tanaman_filtered['jenis'].value_counts()
        st.bar_chart(jenis_counts, use_container_width=True)
        st.dataframe(
            pd.DataFrame({'Jenis': jenis_counts.index, 'Jumlah': jenis_counts.values}),
            use_container_width=True, hide_index=True
        )
    with c2:
        st.markdown("### 💊 Top 10 Fungsi Tanaman")
        fungsi_counts = df_tanaman_filtered['fungsi_utama'].value_counts().head(10)
        st.bar_chart(fungsi_counts, use_container_width=True)

    st.markdown("### ⛰️ Distribusi Ketinggian Lokasi")
    kd = df_tanaman_filtered['ketinggian'].describe()
    cc1, cc2, cc3, cc4 = st.columns(4)
    for col, val, lbl in [
        (cc1, f"{kd['min']:.0f}", 'Minimum (mdpl)'),
        (cc2, f"{kd['max']:.0f}", 'Maksimum (mdpl)'),
        (cc3, f"{kd['mean']:.0f}", 'Rata-rata (mdpl)'),
        (cc4, f"{kd['std']:.0f}", 'Std Deviasi'),
    ]:
        with col:
            st.markdown(f"""<div class="metric-card"><h3>{val}</h3>
                <p>{lbl}</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📋 Komposisi Jenis per Kawasan")
    pivot = df_tanaman_filtered.groupby(['kawasan','jenis']).size().unstack(fill_value=0)
    st.dataframe(pivot, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: INFORMASI
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## ℹ️ Informasi TNBTS")

    total_penduduk  = gdf_desa['jumlah_pen'].sum()    if not gdf_desa.empty and 'jumlah_pen'  in gdf_desa.columns else 0
    total_kecamatan = gdf_desa['nama_kecam'].nunique() if not gdf_desa.empty and 'nama_kecam' in gdf_desa.columns else 0
    total_kabupaten = gdf_desa['nama_kabko'].nunique() if not gdf_desa.empty and 'nama_kabko' in gdf_desa.columns else 0
    tanaman_dilind  = len(df_tanaman[df_tanaman['status_konservasi'] == 'Dilindungi'])

    st.markdown("""
    <div class="info-box">
        <h4>🌋 Taman Nasional Bromo Tengger Semeru</h4>
        <p>TNBTS adalah kawasan konservasi di Jawa Timur dengan keanekaragaman hayati tinggi.
        WebGIS ini menampilkan <b>86 spesies tanaman herbal</b> yang teridentifikasi
        di <b>8 kawasan ekologi</b> berbeda, dari savana vulkanik Bromo (±2.000 mdpl)
        hingga lereng atas Semeru (±2.500 mdpl) dan hutan primer Blok Ireng-Ireng.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── 8 Kawasan Ekologi ────────────────────────────────────────────────────
    st.markdown("### 🏔️ 8 Kawasan Ekologi TNBTS")
    kw_cols_ui = st.columns(2)
    for i, feat in enumerate(KAWASAN_GEOJSON["features"]):
        props = feat["properties"]
        kw    = props["nama"]
        col_h = KAWASAN_HEX.get(kw, '#555')
        cnt   = len(df_tanaman[df_tanaman['kawasan'] == kw])
        with kw_cols_ui[i % 2]:
            st.markdown(
                f'<div style="border-left:5px solid {col_h};padding:.6rem 1rem;'
                f'margin-bottom:.6rem;background:#fafafa;border-radius:0 8px 8px 0;">'
                f'<b style="font-size:16px;">{props["emoji"]}</b> '
                f'<b style="color:{col_h};">{kw}</b><br>'
                f'<small>⛰️ {props["ketinggian"]} &nbsp;|&nbsp; 🌿 {cnt} spesies</small><br>'
                f'<span style="font-size:.85rem;color:#555;">{props["deskripsi"]}</span></div>',
                unsafe_allow_html=True
            )

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Fungsi utama tanaman ──────────────────────────────────────────────────
    st.markdown("### 💊 Kelompok Fungsi Tanaman")
    FUNGSI_GROUPS = {
        "🫀 Pencernaan":      ['Pencernaan','Diare','Sakit perut','Masuk angin','Pencahar','Obat diare'],
        "🔥 Antiradang":      ['Antiradang','Anti radang','Anti radang, batuk','Antiradang, diuretik'],
        "🤒 Penurun Demam":   ['Penurun demam','Obat demam'],
        "💊 Pereda Nyeri":    ['Pereda nyeri','Pereda nyeri, asma','Pereda nyeri otot'],
        "🩹 Obat Luka":       ['Obat luka','Penyembuhan luka','Menghentikan pendarahan','Obat bisul'],
        "🌡️ Batuk & Pilek":  ['Batuk & pilek','Batuk','Batuk, darah tinggi'],
        "🌿 Fungsi Khusus":   ['Diuretik','Antiseptik','Kesuburan','Antikanker','Antibakteri',
                               'Menurunkan tekanan darah','Tekanan darah tinggi','Penurun gula darah',
                               'Melancarkan peredaran darah','Kesehatan darah','Kesehatan hati',
                               'Menghangatkan tubuh','Mengurangi bengkak','Antimalaria','Antioksidan'],
    }

    def get_tanaman_by_group(flist, df):
        tanaman = []
        for f in flist:
            tanaman.extend(
                df[df['fungsi_utama'].str.contains(
                    '|'.join([x.strip() for x in f.split(',')]),
                    case=False, na=False
                )]['nama_tanaman'].tolist()
            )
        return list(dict.fromkeys(tanaman))

    fg_cols = st.columns(3)
    for idx, (label, flist) in enumerate(FUNGSI_GROUPS.items()):
        t_list = get_tanaman_by_group(flist, df_tanaman)
        badges = "".join([
            f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>'
            for t in t_list
        ])
        with fg_cols[idx % 3]:
            st.markdown(f"""
            <div class="fungsi-card">
                <div class="fungsi-title">{label} ({len(t_list)} sp.)</div>
                <div class="tanaman-list">{badges}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Tim peneliti ──────────────────────────────────────────────────────────
    st.markdown("### 👥 Tim Peneliti")
    tm_cols = st.columns(3)
    team = [
        ("https://prasetya.ub.ac.id/wp-content/uploads/2023/10/BU-TYAS-405x270.jpg",
         "Dr Eng Turniningtyas Ayu R.", "ST., MT", "Ketua Tim"),
        ("https://img.inews.co.id/files/networks/2022/11/03/e9d8d_prof-sasmito-djati.jpg",
         "Prof.Dr.Ir. Moch. Sasmito Djati", "M.S.", "Pakar Tanaman Herbal"),
        ("https://i1.rgstatic.net/ii/profile.image/296334033735682-1447662947469_Q512/Adipandang-Yudono.jpg",
         "Adipandang Yudono", "S.Si., M.U.R.P., Ph.D", "Pakar GIS & WebGIS Analytics"),
    ]
    for (photo, name, title, role), col in zip(team, tm_cols):
        with col:
            st.markdown(f"""
            <div class="team-card">
                <img src="{photo}" class="team-photo" alt="{name}">
                <h4 class="team-name">{name}</h4>
                <p class="team-title">{title}</p>
                <p class="team-role">{role}</p>
            </div>""", unsafe_allow_html=True)

    cc1, cc2, cc3 = st.columns([1, 2, 1])
    with cc2:
        st.markdown("""
        <div class="team-card">
            <img src="https://file-filkom.ub.ac.id/fileupload/assets/uploads/foto/crop/arief_andy_soebroto.jpg"
                 class="team-photo" alt="Dr. Ir. Arief Andy Soebroto">
            <h4 class="team-name">Dr. Ir. Arief Andy Soebroto</h4>
            <p class="team-title">ST., M.Kom.</p>
            <p class="team-role">Pakar Platform AI & IoT</p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("""
    ### 📍 Sumber Data
    - **Data Tanaman:** Hasil survei lapangan Tim Peneliti UB (2026) — 86 spesies, 8 kawasan ekologi
    - **Koordinat Kawasan:** Batas ekologi TNBTS berdasarkan survei GPS lapangan & interpretasi citra satelit
    - **Data Desa:** GeoJSON BIG/BPS (41 desa penyangga TNBTS)
    - **Peta Basemap:** OpenStreetMap, Esri World Imagery (Satelit), OpenTopoMap
    - **Model 3D:** Sketchfab — smartmAPPS
    """)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    <p style="font-size:1.1rem;margin-bottom:.5rem;">
        🌿 WebGIS Resiliensi Kesehatan Terhadap Potensi Bencana<br>
        Bromo – Kaldera Tengger – Semeru Melalui Konsumsi Tanaman Herbal di TNBTS
    </p>
    <p style="margin-bottom:.3rem;">© Ekspedisi Tanaman Herbal TNBTS untuk Health Security — 2026</p>
    <p style="font-size:.9rem;opacity:.9;">86 Spesies • 8 Kawasan Ekologi • 41 Desa Penyangga</p>
    <p style="font-size:.7rem;opacity:.5;">© WebGIS Developer: Adipandang Yudono (2026)</p>
</div>
""", unsafe_allow_html=True)
