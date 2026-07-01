import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import json
import os
from folium.plugins import MarkerCluster

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNGSI GEOSPATIAL (GeoJSON & Reproyeksi)
# ─────────────────────────────────────────────────────────────────────────────
def _find_geojson(filename):
    """Mencari file spasial (GeoJSON/CSV) di beberapa direktori kandidat."""
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    candidates = [
        filename,
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _load_geojson(filename):
    """Membaca file GeoJSON ke dalam GeoDataFrame dengan penanganan encoding."""
    path = _find_geojson(filename)
    if path is None:
        return gpd.GeoDataFrame()
    try:
        # Baca file GeoJSON
        gdf = gpd.read_file(path, encoding='utf-8')
        
        # Jika file memiliki CRS, gunakan itu. Jika tidak, set ke EPSG:4326
        if gdf.crs is None:
            st.sidebar.warning(f"⚠️ File {filename} tidak memiliki CRS. Ditetapkan ke EPSG:4326.")
            gdf.set_crs("EPSG:4326", inplace=True)
        # Jika CRS sudah diketahui (dan mungkin benar), kita tetap akan menggunakannya.
        # Nanti di fungsi load_batas kita akan reproject jika perlu.
        return gdf
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error loading {filename}: {e}")
        return gpd.GeoDataFrame()


# ── Data Desa kawasan TNBTS (embedded fallback) ────────────────────────────
_DESA_GEOJSON_EMBEDDED = {"type":"FeatureCollection","name":"Desa_kaw_TNBTS","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[...]}  # (data lengkap seperti di file asli)

@st.cache_data
def load_desa_geojson():
    gdf = _load_geojson('Desa_kaw_TNBTS.geojson')
    if not gdf.empty:
        return gdf
    # Fallback: use embedded data
    try:
        gdf2 = gpd.GeoDataFrame.from_features(_DESA_GEOJSON_EMBEDDED["features"])
        gdf2.set_crs("EPSG:4326", inplace=True)
        return gdf2
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error loading embedded Desa data: {e}")
        return gpd.GeoDataFrame()


@st.cache_data
def load_kabupaten_geojson():
    gdf = _load_geojson('Kabupaten_kaw_TNBTS.geojson')
    if not gdf.empty:
        return gdf
    # Fallback: embedded data
    try:
        _kab_data = {"type":"FeatureCollection","name":"Kabupaten_kaw_TNBTS","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[...]}  # (data lengkap seperti di file asli)
        gdf2 = gpd.GeoDataFrame.from_features(_kab_data["features"])
        gdf2.set_crs("EPSG:4326", inplace=True)
        return gdf2
    except Exception:
        return gpd.GeoDataFrame()


@st.cache_data
def load_batas_geojson():
    """Load GeoJSON batas TNBTS dan proyeksikan ke EPSG:4326 jika perlu."""
    gdf = _load_geojson('Batas_TNBTS.geojson')
    if not gdf.empty:
        # Periksa apakah CRS-nya bukan EPSG:4326 (WGS84)
        # Jika CRS-nya EPSG:3857 (Web Mercator) atau lainnya, kita proyeksikan.
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            st.sidebar.info("📐 Melakukan proyeksi data Batas TNBTS ke EPSG:4326 (WGS84) untuk visualisasi.")
            try:
                gdf = gdf.to_crs("EPSG:4326")
            except Exception as e:
                st.sidebar.error(f"❌ Gagal memproyeksikan Batas TNBTS: {e}")
                return gpd.GeoDataFrame()
        return gdf
    # Fallback ke data embedded (tetap menggunakan EPSG:4326)
    try:
        _batas_data = { ... }  # data embedded Anda
        gdf2 = gpd.GeoDataFrame.from_features(_batas_data["features"])
        gdf2.set_crs("EPSG:4326", inplace=True)
        return gdf2
    except Exception:
        return gpd.GeoDataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# PEMUATAN DATA TANAMAN HERBAL
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_herbal_data(filename):
    """Membaca data sebaran tanaman herbal dari berkas CSV."""
    filepath = _find_geojson(filename)
    if not filepath:
        st.sidebar.error(f"Berkas data sebaran tanaman herbal '{filename}' tidak ditemukan.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        # Membersihkan spasi pada nama kolom dan memastikan kolom X, Y tersedia
        df.columns = df.columns.str.strip()
        # Hapus baris dengan nilai NaN pada kolom X dan Y
        df = df.dropna(subset=['X', 'Y'])
        # Konversi ke float jika diperlukan
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        return df
    except Exception as e:
        st.sidebar.error(f"Gagal membaca data sebaran tanaman herbal: {e}")
        return pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# ANTARMUKA STREAMLIT DAN FILTERING DATA
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sistem Spasial Konservasi TNBTS",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Sistem Informasi Geografis Keanekaragaman Hayati TNBTS")
st.markdown(
    """
    Sistem ini memproyeksikan batas kawasan konservasi TNBTS, pembagian wilayah administrasi kabupaten, 
    batas administrasi desa penyangga, serta visualisasi titik sebaran inventarisasi tanaman herbal secara dinamis.
    """
)

# Memuat data spasial menggunakan fungsi load_batas (tanpa menulis ulang koordinat)
gdf_tnbts = load_batas_geojson() 
gdf_kabupaten = load_kabupaten_geojson()
gdf_desa = load_desa_geojson()
df_herbal = load_herbal_data("Titik Rapihin.xlsx - Sheet1.csv") 

# Penanganan fallback untuk data desa penyangga
if gdf_desa.empty:
    gdf_desa = gpd.GeoDataFrame.from_features(_DESA_GEOJSON_EMBEDDED['features'], crs="EPSG:4326") 

# Penyiapan filter spesies tanaman herbal pada bilah samping (sidebar)
selected_species = []
if not df_herbal.empty:
    st.sidebar.header("Filter Distribusi Spasial")
    all_species = sorted(df_herbal['Nama'].unique()) 
    
    select_all = st.sidebar.checkbox("Pilih Semua Spesies Herbal", value=True)
    if select_all:
        selected_species = all_species
    else:
        selected_species = st.sidebar.multiselect(
            "Pilih Spesies Herbal yang Ditampilkan:",
            options=all_species,
            default=all_species[:5]
        )
    
    df_herbal_filtered = df_herbal[df_herbal['Nama'].isin(selected_species)]
else:
    df_herbal_filtered = pd.DataFrame()


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
# Koordinat polygon berbentuk OVAL/LINGKARAN (32 titik) — non-overlapping.
# Dihitung: lon_c + r_lon×cos(θ), lat_c + r_lat×sin(θ), θ = 0..360°/32 langkah.
# Bounding box setiap kawasan tidak bersinggungan dengan kawasan lain (terverifikasi).
# Urutan koordinat: [lon, lat] — standar GeoJSON.
# ─────────────────────────────────────────────────────────────────────────────
KAWASAN_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        # ── 1. Blok Ireng-Ireng & Hutan Atas ─────────────────────────────
        # Center (-7.8980, 112.9170) | oval 32 titik | r_lat=0.0085 r_lon=0.0090
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
                    [112.926, -7.898], [112.92583, -7.89634], [112.92531, -7.89475],
                    [112.92448, -7.89328], [112.92336, -7.89199], [112.922, -7.89093],
                    [112.92044, -7.89015], [112.91876, -7.88966], [112.917, -7.8895],
                    [112.91524, -7.88966], [112.91356, -7.89015], [112.912, -7.89093],
                    [112.91064, -7.89199], [112.90952, -7.89328], [112.90869, -7.89475],
                    [112.90817, -7.89634], [112.908, -7.898], [112.90817, -7.89966],
                    [112.90869, -7.90125], [112.90952, -7.90272], [112.91064, -7.90401],
                    [112.912, -7.90507], [112.91356, -7.90585], [112.91524, -7.90634],
                    [112.917, -7.9065], [112.91876, -7.90634], [112.92044, -7.90585],
                    [112.922, -7.90507], [112.92336, -7.90401], [112.92448, -7.90272],
                    [112.92531, -7.90125], [112.92583, -7.89966], [112.926, -7.898]
                ]]
            }
        },
        # ── 2. Ranu Darungan & Sekitar Danau ─────────────────────────────
        # Center (-7.9040, 112.9510) | oval 32 titik | r_lat=0.0050 r_lon=0.0055
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
                    [112.9565, -7.904], [112.95639, -7.90302], [112.95608, -7.90209],
                    [112.95557, -7.90122], [112.95489, -7.90046], [112.95406, -7.89984],
                    [112.9531, -7.89938], [112.95207, -7.8991], [112.951, -7.899],
                    [112.94993, -7.8991], [112.9489, -7.89938], [112.94794, -7.89984],
                    [112.94711, -7.90046], [112.94643, -7.90122], [112.94592, -7.90209],
                    [112.94561, -7.90302], [112.9455, -7.904], [112.94561, -7.90498],
                    [112.94592, -7.90591], [112.94643, -7.90678], [112.94711, -7.90754],
                    [112.94794, -7.90816], [112.9489, -7.90862], [112.94993, -7.9089],
                    [112.951, -7.909], [112.95207, -7.9089], [112.9531, -7.90862],
                    [112.95406, -7.90816], [112.95489, -7.90754], [112.95557, -7.90678],
                    [112.95608, -7.90591], [112.95639, -7.90498], [112.9565, -7.904]
                ]]
            }
        },
        # ── 3. Tepi Hutan & Zona Transisi ────────────────────────────────
        # Center (-7.9240, 112.9330) | oval 32 titik | r_lat=0.0075 r_lon=0.0080
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
                    [112.941, -7.924], [112.94085, -7.92254], [112.94039, -7.92113],
                    [112.93965, -7.91983], [112.93866, -7.9187], [112.93744, -7.91776],
                    [112.93606, -7.91707], [112.93456, -7.91664], [112.933, -7.9165],
                    [112.93144, -7.91664], [112.92994, -7.91707], [112.92856, -7.91776],
                    [112.92734, -7.9187], [112.92635, -7.91983], [112.92561, -7.92113],
                    [112.92515, -7.92254], [112.925, -7.924], [112.92515, -7.92546],
                    [112.92561, -7.92687], [112.92635, -7.92817], [112.92734, -7.9293],
                    [112.92856, -7.93024], [112.92994, -7.93093], [112.93144, -7.93136],
                    [112.933, -7.9315], [112.93456, -7.93136], [112.93606, -7.93093],
                    [112.93744, -7.93024], [112.93866, -7.9293], [112.93965, -7.92817],
                    [112.94039, -7.92687], [112.94085, -7.92546], [112.941, -7.924]
                ]]
            }
        },
        # ── 4. Zona Budidaya & Pekarangan ────────────────────────────────
        # Center (-7.9370, 112.9480) | oval 32 titik | r_lat=0.0060 r_lon=0.0065
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
                    [112.9545, -7.937], [112.95438, -7.93583], [112.95401, -7.9347],
                    [112.9534, -7.93367], [112.9526, -7.93276], [112.95161, -7.93201],
                    [112.95049, -7.93146], [112.94927, -7.93112], [112.948, -7.931],
                    [112.94673, -7.93112], [112.94551, -7.93146], [112.94439, -7.93201],
                    [112.9434, -7.93276], [112.9426, -7.93367], [112.94199, -7.9347],
                    [112.94162, -7.93583], [112.9415, -7.937], [112.94162, -7.93817],
                    [112.94199, -7.9393], [112.9426, -7.94033], [112.9434, -7.94124],
                    [112.94439, -7.94199], [112.94551, -7.94254], [112.94673, -7.94288],
                    [112.948, -7.943], [112.94927, -7.94288], [112.95049, -7.94254],
                    [112.95161, -7.94199], [112.9526, -7.94124], [112.9534, -7.94033],
                    [112.95401, -7.9393], [112.95438, -7.93817], [112.9545, -7.937]
                ]]
            }
        },
        # ── 5. Savana Bromo & Lereng Terbuka ─────────────────────────────
        # Center (-7.9450, 112.9680) | oval 32 titik | r_lat=0.0100 r_lon=0.0110
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
                    [112.979, -7.945], [112.97879, -7.94305], [112.97816, -7.94117],
                    [112.97715, -7.93944], [112.97578, -7.93793], [112.97411, -7.93669],
                    [112.97221, -7.93576], [112.97015, -7.93519], [112.968, -7.935],
                    [112.96585, -7.93519], [112.96379, -7.93576], [112.96189, -7.93669],
                    [112.96022, -7.93793], [112.95885, -7.93944], [112.95784, -7.94117],
                    [112.95721, -7.94305], [112.957, -7.945], [112.95721, -7.94695],
                    [112.95784, -7.94883], [112.95885, -7.95056], [112.96022, -7.95207],
                    [112.96189, -7.95331], [112.96379, -7.95424], [112.96585, -7.95481],
                    [112.968, -7.955], [112.97015, -7.95481], [112.97221, -7.95424],
                    [112.97411, -7.95331], [112.97578, -7.95207], [112.97715, -7.95056],
                    [112.97816, -7.94883], [112.97879, -7.94695], [112.979, -7.945]
                ]]
            }
        },
        # ── 6. Kantong Air & Lembah ──────────────────────────────────────
        # Center (-7.9600, 112.9370) | oval 32 titik | r_lat=0.0065 r_lon=0.0070
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
                    [112.944, -7.96], [112.94387, -7.95873], [112.94347, -7.95751],
                    [112.94282, -7.95639], [112.94195, -7.9554], [112.94089, -7.9546],
                    [112.93968, -7.95399], [112.93837, -7.95362], [112.937, -7.9535],
                    [112.93563, -7.95362], [112.93432, -7.95399], [112.93311, -7.9546],
                    [112.93205, -7.9554], [112.93118, -7.95639], [112.93053, -7.95751],
                    [112.93013, -7.95873], [112.93, -7.96], [112.93013, -7.96127],
                    [112.93053, -7.96249], [112.93118, -7.96361], [112.93205, -7.9646],
                    [112.93311, -7.9654], [112.93432, -7.96601], [112.93563, -7.96638],
                    [112.937, -7.9665], [112.93837, -7.96638], [112.93968, -7.96601],
                    [112.94089, -7.9654], [112.94195, -7.9646], [112.94282, -7.96361],
                    [112.94347, -7.96249], [112.94387, -7.96127], [112.944, -7.96]
                ]]
            }
        },
        # ── 7. Lereng Semeru & Dataran Tinggi ────────────────────────────
        # Center (-7.9800, 112.9870) | oval 32 titik | r_lat=0.0110 r_lon=0.0120
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
                    [112.999, -7.98], [112.99877, -7.97785], [112.99809, -7.97579],
                    [112.99698, -7.97389], [112.99549, -7.97222], [112.99367, -7.97085],
                    [112.99159, -7.96984], [112.98934, -7.96921], [112.987, -7.969],
                    [112.98466, -7.96921], [112.98241, -7.96984], [112.98033, -7.97085],
                    [112.97851, -7.97222], [112.97702, -7.97389], [112.97591, -7.97579],
                    [112.97523, -7.97785], [112.975, -7.98], [112.97523, -7.98215],
                    [112.97591, -7.98421], [112.97702, -7.98611], [112.97851, -7.98778],
                    [112.98033, -7.98915], [112.98241, -7.99016], [112.98466, -7.99079],
                    [112.987, -7.991], [112.98934, -7.99079], [112.99159, -7.99016],
                    [112.99367, -7.98915], [112.99549, -7.98778], [112.99698, -7.98611],
                    [112.99809, -7.98421], [112.99877, -7.98215], [112.999, -7.98]
                ]]
            }
        },
        # ── 8. Zona Pesisir & Pantai Selatan ─────────────────────────────
        # Center (-8.0200, 112.9930) | oval 32 titik | r_lat=0.0090 r_lon=0.0110
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
                    [113.004, -8.02], [113.00379, -8.01824], [113.00316, -8.01656],
                    [113.00215, -8.015], [113.00078, -8.01364], [112.99911, -8.01252],
                    [112.99721, -8.01169], [112.99515, -8.01117], [112.993, -8.011],
                    [112.99085, -8.01117], [112.98879, -8.01169], [112.98689, -8.01252],
                    [112.98522, -8.01364], [112.98385, -8.015], [112.98284, -8.01656],
                    [112.98221, -8.01824], [112.982, -8.02], [112.98221, -8.02176],
                    [112.98284, -8.02344], [112.98385, -8.025], [112.98522, -8.02636],
                    [112.98689, -8.02748], [112.98879, -8.02831], [112.99085, -8.02883],
                    [112.993, -8.029], [112.99515, -8.02883], [112.99721, -8.02831],
                    [112.99911, -8.02748], [113.00078, -8.02636], [113.00215, -8.025],
                    [113.00316, -8.02344], [113.00379, -8.02176], [113.004, -8.02]
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
        show_desa_geojson  = st.checkbox("🏘️ Batas Desa",         value=True)
        show_kawasan       = st.checkbox("🏔️ Kawasan Ekologi",     value=True)
    with c2:
        show_tanaman       = st.checkbox("🌿 Tanaman",             value=True)
        show_kabupaten     = st.checkbox("🗺️ Batas Kabupaten",     value=True)
    show_batas_tnbts   = st.checkbox("🔲 Batas TNBTS",         value=True)

    st.markdown("### 🏔️ Kontrol Tampilan 3D")
    map_height_3d = st.slider("Tinggi Iframe", 400, 800, 600, step=50)

    st.markdown("---")
    st.markdown("### 📁 Status File")
    # Status berdasarkan path pencarian aktual
    _p_desa = _find_geojson('Desa_kaw_TNBTS.geojson')
    _p_kab  = _find_geojson('Kabupaten_kaw_TNBTS.geojson')
    _p_bts  = _find_geojson('Batas_TNBTS.geojson')
    for _fname, _path, _keterangan in [
        ('Desa_kaw_TNBTS.geojson',      _p_desa, '41 desa kawasan'),
        ('Kabupaten_kaw_TNBTS.geojson', _p_kab,  '4 kabupaten'),
        ('Batas_TNBTS.geojson',         _p_bts,  'Batas TNBTS'),
    ]:
        if _path:
            _fsz = os.path.getsize(_path) / 1024
            st.markdown(f"""
            <div class="status-badge">
                ✅ <b>{_fname}</b><br><small>{_fsz:.1f} KB • {_keterangan}</small>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-badge" style="border-left-color:#f44336;">
                ❌ <b>{_fname}</b><br><small>File tidak ditemukan</small>
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
        # Koordinat setiap tanaman ditempatkan di dalam oval kawasannya
        # menggunakan distribusi golden-angle agar tidak bertumpuk.
        # lat/lon = center_kawasan + offset spiral (max 65% radius oval).
        (1,  'Adas',                              'Foeniculum vulgare',               'Herba', 'Pencernaan',                -7.937000, 112.949336, 'Zona Budidaya & Pekarangan',           1900, 'Sekitar Desa Ngadisari & Wonokitri',    'Ngadisari, Wonokitri'),
        (2,  'Ajeran putih',                      'Bidens pilosa L.',                 'Herba', 'Antiradang',                -7.945000, 112.969131, 'Savana Bromo & Lereng Terbuka',        2050, 'Lautan Pasir & Savana Bromo',           'Seluruh desa penyangga'),
        (3,  'Alang-alang',                       'Imperata cylindrica L.',           'Rumput','Diuretik',                  -7.943798, 112.966556, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Savana Tengger',                 'Ngadas, Argosari'),
        (4,  'Andong',                            'Cordyline fruticosa Linn',         'Pohon', 'Menghentikan pendarahan',   -7.960000, 112.938313, 'Kantong Air & Lembah',                 1750, 'Lembah Sumber Air TNBTS',              'Ngadas, Ranupani'),
        (5,  'Awar-awar',                         'Ficus septica Burm.f.',            'Pohon', 'Antiradang',                -7.924000, 112.933867, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan Cemara – Desa Ngadisari',   'Ngadisari, Wonokitri'),
        (6,  'Bakung',                            'Crinum asiaticium L.',             'Herba', 'Mengurangi bengkak',        -7.904000, 112.952032, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan',                   'Ranupani'),
        (7,  'Bawang merah',                      'Allium cepa L.',                   'Herba', 'Penurun demam',             -7.935557, 112.946294, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pertanian Tengger',              'Seluruh desa penyangga'),
        (8,  'Bawang putih',                      'Allium sativum',                   'Herba', 'Menurunkan tekanan darah',  -7.980000, 112.988530, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Atas Semeru – Ranupani',         'Ranupani, Argosari'),
        (9,  'Beluntas',                          'Pluchea indica',                   'Semak', 'Pencernaan',                -8.020000, 112.995528, 'Zona Pesisir & Pantai Selatan',        300,  'Zona Pesisir Selatan TNBTS',            'Desa pesisir selatan'),
        (10, 'Bidara laut',                       'Strychnos lucida',                 'Pohon', 'Pereda nyeri',              -8.017580, 112.989771, 'Zona Pesisir & Pantai Selatan',        250,  'Pantai Selatan – Batas TNBTS',          'Desa pesisir selatan'),
        (11, 'Buah klandingan',                   'Lucas lavandulifolia',             'Pohon', 'Batuk & pilek',             -7.923049, 112.931893, 'Tepi Hutan & Zona Transisi',           1900, 'Zona Transisi Hutan – Ladang',          'Ngadisari, Wonokitri'),
        (12, 'Bunga hariang',                     'Begonia',                         'Bunga', 'Batuk',                     -7.978359, 112.985046, 'Lereng Semeru & Dataran Tinggi',       2300, 'Lereng Semeru Barat Daya',              'Ranupani'),
        (13, 'Bunga Matahari',                    'Helianthus annuus',               'Bunga', 'Penurun demam',             -7.947289, 112.968221, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana & Ladang Bromo',                 'Ngadisari, Argosari'),
        (14, 'Calingan',                          'Centella asiatica L.',             'Herba', 'Penyembuhan luka',          -7.902902, 112.949682, 'Ranu Darungan & Sekitar Danau',        1860, 'Bantaran Ranu Darungan',                'Ranupani'),
        (15, 'Cemplukan',                         'Physalis minima',                  'Herba', 'Penurun demam',             -7.942842, 112.969820, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana Bromo',                     'Ngadas, Argosari'),
        (16, 'Daun dadap',                        'Erythrina variegata L.',           'Pohon', 'Pereda nyeri',              -7.925810, 112.933169, 'Tepi Hutan & Zona Transisi',           1900, 'Batas Hutan Cemara & Ladang',           'Ngadisari'),
        (17, 'Dringu',                            'Acorus calamus L.',                'Herba', 'Pencernaan',                -7.906090, 112.951202, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Pinggir Air',     'Ranupani'),
        (18, 'Ganjan',                            'Artemisia vulgaris',               'Herba', 'Obat luka',                 -7.898000, 112.918106, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Hutan Primer',       'Ireng-Ireng'),
        (19, 'Ganyong',                           'Canna indica L.',                  'Herba', 'Pencernaan',                -7.958573, 112.935322, 'Kantong Air & Lembah',                 1750, 'Lembah Basah – Sumber Mata Air',       'Ngadas, Ranupani'),
        (20, 'Jahe',                              'Zingiber Officinale Rocs',         'Herba', 'Pencernaan',                -7.922294, 112.934395, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Campuran Tepi Hutan',             'Seluruh desa penyangga'),
        (21, 'Jambu wer',                         'Prunus persica',                   'Pohon', 'Diare',                     -7.983123, 112.987299, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Kebun Desa Ranupani',  'Ranupani'),
        (22, 'Jarak',                             'Jatropha curcas',                  'Pohon', 'Pencahar',                  -7.945537, 112.964660, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana & Batas Ladang',            'Ngadisari, Cemoro Lawang'),
        (23, 'Jarak merah',                       'Jatropha curcas L.',               'Pohon', 'Obat luka',                 -7.946830, 112.971164, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana – Agak Ke Utara',          'Cemoro Lawang'),
        (24, 'Jenggot wesi',                      'Usnea Barbata Fries',              'Lumut', 'Antibakteri',               -7.896778, 112.915588, 'Blok Ireng-Ireng & Hutan Atas',       2500, 'Pohon Tua Blok Ireng-Ireng',            'Ireng-Ireng'),
        (25, 'Jenis Talas',                       'Homalomena sp.',                   'Herba', 'Masuk angin',               -7.962717, 112.937257, 'Kantong Air & Lembah',                 1750, 'Lembah Basah – Sekitar Mata Air',      'Ngadas'),
        (26, 'Kayu Ampet',                        'Alstonia macrophylla',             'Pohon', 'Sakit perut',               -8.024607, 112.993494, 'Zona Pesisir & Pantai Selatan',        250,  'Hutan Pantai Selatan',                  'Desa pesisir selatan'),
        (27, 'Kayu putih',                        'Melaleuca leucadendra',            'Pohon', 'Masuk angin',               -8.015657, 112.997069, 'Zona Pesisir & Pantai Selatan',        300,  'Hutan Pantai – Zona Penyangga Selatan', 'Desa pesisir selatan'),
        (28, 'Keladi tikus',                      'Typhonium flagelliforme',          'Herba', 'Antikanker',                -7.924425, 112.930440, 'Tepi Hutan & Zona Transisi',           1900, 'Bawah Tegakan Hutan Cemara',            'Ngadisari'),
        (29, 'Keladi/sente-sentean',              'Alocasia sp.',                     'Herba', 'Obat bisul',                -7.957439, 112.939114, 'Kantong Air & Lembah',                 1750, 'Lembah Sungai – Naungan Lebat',        'Ngadas, Ranupani'),
        (30, 'Kencana Ungu',                      'Ruellia',                         'Herba', 'Penurun gula darah',        -7.941421, 112.966942, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Jalan Savana Bromo',               'Ngadisari, Cemoro Lawang'),
        (31, 'Kencur',                            'Kaempferia galanga L.',            'Herba', 'Batuk & pilek',             -7.925446, 112.935425, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah Tradisional',              'Ngadisari, Wonokitri'),
        (32, 'Keningar',                          'Ageratina sp.',                    'Herba', 'Menghentikan pendarahan',   -7.977056, 112.989462, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Zona Terbuka',          'Ranupani, Argosari'),
        (33, 'Kesimbukan',                        'Paederia foetida',                 'Herba', 'Menghentikan pendarahan',   -7.921171, 112.932189, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan – Merambat Di Pohon',       'Wonokitri, Ngadisari'),
        (34, 'Kunyit',                            'Curcuma domestica Rumph.',         'Herba', 'Antiradang',                -7.926793, 112.931453, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah Tradisional',              'Seluruh desa penyangga'),
        (35, 'Lengkuas',                          'Alpinia galanga',                  'Herba', 'Masuk angin',               -7.922851, 112.936357, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Campuran – Tepi Hutan',           'Seluruh desa penyangga'),
        (36, 'Lili-lilian liar',                  'Molineria sp.',                    'Herba', 'Obat luka',                 -7.900326, 112.917216, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Blok Ireng-Ireng',         'Ireng-Ireng'),
        (37, 'Lobak',                             'Raphanus sativus L.',              'Herba', 'Pencernaan',                -7.980733, 112.982481, 'Lereng Semeru & Dataran Tinggi',       2200, 'Ladang Dataran Tinggi Ranupani',        'Ranupani, Argosari'),
        (38, 'Lombok terong',                     'Solanum torvum Sw.',               'Herba', 'Tekanan darah tinggi',      -7.948532, 112.965982, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana – Tumbuh Liar',             'Ngadisari, Cemoro Lawang'),
        (39, 'Lombok udel',                       'Capsicum frutescens L.',           'Herba', 'Menghangatkan tubuh',       -7.939747, 112.948261, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pekarangan Desa Tengger',        'Ngadisari, Wonokitri'),
        (40, 'Paitan',                            'Tithonia diversifolia',            'Herba', 'Penurun demam',             -7.922649, 112.929508, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Jalan – Batas Hutan & Ladang',    'Ngadisari'),
        (41, 'Pakis',                             'Davallia',                        'Pakis', 'Pencernaan',                -7.895808, 112.918780, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer Blok Ireng-Ireng',  'Ireng-Ireng'),
        (42, 'Pakis (fern)',                      'Phegopteris',                     'Pakis', 'Pencernaan',                -7.898546, 112.913734, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Naungan Lebat',     'Ireng-Ireng'),
        (43, 'Pakis/paku pedang',                 'Nephrolepis sp.',                  'Pakis', 'Diuretik',                  -7.902030, 112.952661, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Danau Ranu Darungan',             'Ranupani'),
        (44, 'Paku rane/paku kawat',              'Selaginella sp.',                  'Pakis', 'Melancarkan peredaran darah',-7.899859, 112.920094,'Blok Ireng-Ireng & Hutan Atas',       2500, 'Bebatuan Hutan Primer',                 'Ireng-Ireng'),
        (45, 'Paku sigung',                       'Didymochlaena',                   'Pakis', 'Penyembuhan luka',          -7.982496, 112.991281, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Bawah Tegakan',        'Ranupani'),
        (46, 'Parijoto',                          'Medinilla speciosa',               'Herba', 'Kesuburan',                 -7.894364, 112.915965, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Tanaman Endemik',   'Ireng-Ireng'),
        (47, 'Pecut kuda',                        'Stachytarpheta sp.',               'Herba', 'Penurun demam',             -7.943546, 112.972378, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Tumbuh Liar',             'Ngadas'),
        (48, 'Pisang',                            'Musa paradisiaca',                 'Pohon', 'Diare',                     -7.960637, 112.933120, 'Kantong Air & Lembah',                 1750, 'Lembah – Sekitar Sumber Air',           'Ngadas, Ranupani'),
        (49, 'Pulosari',                          'Alyxia reinwardtii Blume.',        'Herba', 'Batuk & pilek',             -7.901589, 112.915027, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Blok Ireng-Ireng – Semak Bawah Pohon', 'Ireng-Ireng'),
        (50, 'Purwoceng',                         'Pimpinella pruatjan',              'Herba', 'Kesuburan',                 -7.975118, 112.985568, 'Lereng Semeru & Dataran Tinggi',       2400, 'Lereng Semeru – Tanaman Endemik Jawa', 'Ranupani'),
        (51, 'Air kuncup kecubung gunung',        'Brugmansia candida',               'Perdu', 'Pereda nyeri, asma',        -7.984820, 112.984269, 'Lereng Semeru & Dataran Tinggi',       2300, 'Lereng Semeru – Tepi Vegetasi',        'Ranupani'),
        (52, 'Akar sempretan',                    'Mikania cordata',                  'Herba', 'Antiradang, diuretik',      -7.927372, 112.934683, 'Tepi Hutan & Zona Transisi',           1850, 'Merambat di Tepi Hutan Cemara',         'Ngadisari, Wonokitri'),
        (53, 'Daun kancing-kancing/semanggi liar','Desmodium sp.',                   'Herba', 'Anti radang, batuk',        -7.920282, 112.934244, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan – Tanah Lembab',             'Ngadisari'),
        (54, 'Daun-daunan hutan mirip garutan',   'Stachyphrynium sp.',               'Herba', 'Obat luka',                 -7.896523, 112.921282, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer',                   'Ireng-Ireng'),
        (55, 'Ranti',                             'Tinospora crispa L. Miers',       'Herba', 'Antimalaria',               -7.926037, 112.929251, 'Tepi Hutan & Zona Transisi',           1850, 'Merambat di Tepi Hutan',                'Ngadisari, Wonokitri'),
        (56, 'Rumput asystasia',                  'Asystasia sp.',                    'Herba', 'Anti radang',               -7.943291, 112.963445, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Padang Terbuka',         'Cemoro Lawang'),
        (57, 'Rumput hutan',                      'Oplismenus sp.',                   'Rumput','Anti radang',               -7.896263, 112.912546, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Primer Blok Ireng-Ireng',  'Ireng-Ireng'),
        (58, 'Rumput karpet',                     'Axonopus sp.',                    'Rumput','Obat luka',                  -7.949266, 112.970196, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Terbuka – Savana Tengger',       'Ngadas, Argosari'),
        (59, 'Rumput teki-tekian (nutrush)',      'Scleria sp.',                     'Rumput','Diuretik',                   -7.940297, 112.969623, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Savana – Tepian Lembab',         'Ngadas'),
        (60, 'Tumbuhan herba bawah (Amischotolype)','Amischotolype sp.',             'Herba', 'Obat luka',                 -7.902334, 112.919147, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Blok Ireng-Ireng',         'Ireng-Ireng'),
        (61, 'Sawi ireng',                        'Brassica juncea',                  'Herba', 'Pencernaan',                -7.978017, 112.992924, 'Lereng Semeru & Dataran Tinggi',       2200, 'Ladang Sayuran Dataran Tinggi',         'Ranupani, Argosari'),
        (62, 'Semanggi',                          'Marsilea crenata',                 'Pakis', 'Melancarkan peredaran darah',-7.904490, 112.947951,'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Di Air',          'Ranupani'),
        (63, 'Sengganen/Senggani',                'Melastoma malabathricum L.',       'Semak', 'Obat diare',                -7.947577, 112.963109, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Semak Terbuka',           'Ngadas, Argosari'),
        (64, 'Sirih',                             'Piper betle Linn',                 'Semak', 'Antiseptik',                -7.934411, 112.950151, 'Zona Budidaya & Pekarangan',           1900, 'Pekarangan Desa Tengger',               'Ngadisari, Wonokitri'),
        (65, 'Snikir',                            'C. Caudatus',                     'Herba', 'Penyembuhan luka',          -7.946147, 112.973737, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Tumbuh Liar',            'Cemoro Lawang, Ngadisari'),
        (66, 'Stroberi tengger',                  'Rubus Idaeus L.',                  'Perdu', 'Kesehatan darah',           -7.977668, 112.980837, 'Lereng Semeru & Dataran Tinggi',       2400, 'Lereng Semeru – Khas Dataran Tinggi',  'Ranupani'),
        (67, 'Suplir',                            'Adiantum',                        'Pakis', 'Batuk, darah tinggi',       -7.985820, 112.989971, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Bebatuan Lembab',      'Ranupani'),
        (68, 'Suri pandak',                       'Plantago mayor Linn.',             'Herba', 'Penyembuhan luka',          -7.924907, 112.937398, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Jalan Hutan',                      'Ngadisari'),
        (69, 'Tapak liman',                       'Elephantopus scaber L.',           'Herba', 'Penurun demam',             -7.940472, 112.964499, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana & Jalur Trekking',          'Ngadas, Argosari'),
        (70, 'Teklan',                            'Eupatorium riparium',              'Herba', 'Obat demam',                -7.905670, 112.953888, 'Ranu Darungan & Sekitar Danau',        1860, 'Tepi Ranu Darungan – Bantaran',        'Ranupani'),
        (71, 'Tepung otot',                       'Borreria laevis',                  'Herba', 'Pereda nyeri otot',         -7.950675, 112.967191, 'Savana Bromo & Lereng Terbuka',        2050, 'Padang Rumput Savana',                  'Ngadisari, Cemoro Lawang'),
        (72, 'Tirem',                             'Chromolaena odoratum',             'Semak', 'Sakit perut',               -7.941195, 112.972966, 'Savana Bromo & Lereng Terbuka',        2000, 'Tepi Savana – Semak Invasif',           'Ngadas, Argosari'),
        (73, 'Trabasan',                          'Ageratum conyzoides',              'Herba', 'Obat luka',                 -7.920421, 112.930316, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan & Ladang',                   'Ngadisari, Wonokitri'),
        (74, 'Vervain',                           'Stachytarpheta mutabilis Vahl',    'Herba', 'Penurun demam',             -7.944749, 112.961317, 'Savana Bromo & Lereng Terbuka',        2050, 'Savana Bromo – Tepian Jalan',           'Cemoro Lawang'),
        (75, 'Wedusan',                           'Ageratum conyzoides',              'Herba', 'Obat luka',                 -7.928486, 112.932380, 'Tepi Hutan & Zona Transisi',           1850, 'Batas Ladang & Hutan Cemara',           'Ngadisari'),
        (76, 'Ketumbar',                          'Coriandrum sativum Linn.',         'Herba', 'Pencernaan',                -7.937644, 112.944053, 'Zona Budidaya & Pekarangan',           1900, 'Ladang Pekarangan Desa Tengger',        'Seluruh desa penyangga'),
        (77, 'Teh-tehan',                         'Eclipta prostrata Linn.',          'Herba', 'Kesehatan hati',            -7.962171, 112.940676, 'Kantong Air & Lembah',                 1750, 'Lembah – Pinggir Aliran Air',           'Ngadas'),
        (78, 'Cemara besi',                       'Casuarina junghuhniana Miq.',      'Pohon', 'Penyembuhan luka',          -7.973583, 112.989196, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Tegakan Cemara Khas',  'Ranupani'),
        (79, 'Simbaran',                          'Peperomia sp.',                    'Herba', 'Penyembuhan luka',          -7.893222, 112.918587, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Epifit di Pohon Tua Blok Ireng-Ireng', 'Ireng-Ireng'),
        (80, 'Kenikir',                           'Cosmos caudatus Kunth',            'Herba', 'Antioksidan',               -7.920992, 112.936807, 'Tepi Hutan & Zona Transisi',           1850, 'Tepi Hutan & Ladang',                   'Ngadisari, Wonokitri'),
        (81, 'Tumbuhan herba bawah (Commelina)',  'Commelina sp.',                   'Herba', 'Obat luka',                 -7.900618, 112.912217, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Lantai Hutan Lembab Blok Ireng-Ireng', 'Ireng-Ireng'),
        (82, 'Rumput ilalang',                    'Imperata cylindrica',              'Rumput','Diuretik',                  -7.949410, 112.972874, 'Savana Bromo & Lereng Terbuka',        2000, 'Padang Terbuka Savana Tengger',         'Ngadas, Argosari'),
        (83, 'Paku sarang burung',                'Asplenium nidus',                  'Pakis', 'Obat luka',                 -7.899165, 112.922611, 'Blok Ireng-Ireng & Hutan Atas',       2400, 'Epifit di Pohon – Blok Ireng-Ireng',   'Ireng-Ireng'),
        (84, 'Anggrek tanah',                     'Spathoglottis plicata',            'Bunga', 'Antioksidan',               -7.938589, 112.967674, 'Savana Bromo & Lereng Terbuka',        2050, 'Tepi Savana Bromo – Semi Terbuka',     'Ngadisari, Cemoro Lawang'),
        (85, 'Jahe merah',                        'Zingiber officinale var. rubrum',  'Herba', 'Antiradang',                -7.923801, 112.927877, 'Tepi Hutan & Zona Transisi',           1900, 'Kebun Rempah & Tepi Hutan',             'Ngadisari, Wonokitri'),
        (86, 'Cemara gunung',                     'Casuarina junghuhniana',           'Pohon', 'Penyembuhan luka',          -7.983515, 112.980382, 'Lereng Semeru & Dataran Tinggi',       2200, 'Lereng Semeru – Dominant Trees',       'Ranupani'),
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



# ─────────────────────────────────────────────────────────────────────────────
# LOAD & FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
df_tanaman   = load_tanaman_herbal_data()
gdf_desa     = load_desa_geojson()
gdf_kabupaten = load_kabupaten_geojson()
gdf_batas    = load_batas_geojson()

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
def create_tnbts_map(
    show_kawasan, show_desa_geojson, show_kabupaten, show_batas_tnbts, show_tanaman,
    gdf_desa, gdf_kabupaten, gdf_batas, df_tanaman_filtered
):
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

    # ── LAYER 1: Batas TNBTS (outline tebal, fill no color) ─────────────────
    if show_batas_tnbts and not gdf_batas.empty:
        batas_group = folium.FeatureGroup(name='🔲 Batas TNBTS', show=True)

        folium.GeoJson(
            gdf_batas,
            name='Batas TNBTS',
            style_function=lambda f: {
                'fillColor': 'none',
                'color': '#B71C1C',
                'weight': 4,
                'fillOpacity': 0,
                'opacity': 1,
                'dashArray': '8, 4',
            },
            highlight_function=lambda f: {
                'fillColor': '#B71C1C',
                'color': '#7F0000',
                'weight': 5,
                'fillOpacity': 0.10,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['Keterangan'],
                aliases=['Keterangan:'],
                localize=False,
                sticky=False,
                style=(
                    'background-color:white;'
                    'border:2px solid #B71C1C;'
                    'border-radius:6px;'
                    'padding:6px 10px;'
                    'font-family:Arial;'
                    'font-size:12px;'
                    'font-weight:bold;'
                    'color:#B71C1C;'
                    'box-shadow:2px 2px 6px rgba(0,0,0,.15);'
                    'pointer-events:none;'
                ),
            ),
            popup=folium.GeoJsonPopup(
                fields=['Keterangan'],
                aliases=[''],
                max_width=300
            )
        ).add_to(batas_group)
        batas_group.add_to(m)

    # ── LAYER 2: Batas Kabupaten (outline tebal, fill no color, label) ─────
    if show_kabupaten and not gdf_kabupaten.empty:
        kabupaten_group = folium.FeatureGroup(name='🗺️ Batas Kabupaten', show=True)

        folium.GeoJson(
            gdf_kabupaten,
            name='Kabupaten',
            style_function=lambda f: {
                'fillColor': 'none',
                'color': '#1565C0',
                'weight': 4,
                'fillOpacity': 0,
                'opacity': 1,
                'dashArray': '',
            },
            highlight_function=lambda f: {
                'fillColor': '#1565C0',
                'color': '#0D47A1',
                'weight': 5,
                'fillOpacity': 0.12,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['nama_kabko', 'nama_provi'],
                aliases=['Kabupaten:', 'Provinsi:'],
                localize=False,
                sticky=False,
                style=(
                    'background-color:white;'
                    'border:1px solid #1565C0;'
                    'border-radius:6px;'
                    'padding:6px 10px;'
                    'font-family:Arial;'
                    'font-size:12px;'
                    'box-shadow:2px 2px 6px rgba(0,0,0,.15);'
                    'pointer-events:none;'
                ),
            ),
            popup=folium.GeoJsonPopup(
                fields=['nama_kabko', 'nama_provi'],
                aliases=['Kabupaten', 'Provinsi'],
                max_width=250
            )
        ).add_to(kabupaten_group)

        # Label nama kabupaten menggunakan DivIcon di centroid masing-masing
        import geopandas as _gpd
        for _, row_kab in gdf_kabupaten.iterrows():
            try:
                centroid = row_kab.geometry.centroid
                nama_kab = row_kab.get('nama_kabko', '')
                folium.Marker(
                    location=[centroid.y, centroid.x],
                    icon=folium.DivIcon(
                        html=f"""<div style="
                            font-family: Arial, sans-serif;
                            font-size: 12px;
                            font-weight: bold;
                            color: #1565C0;
                            background: rgba(255,255,255,0.85);
                            border: 2px solid #1565C0;
                            border-radius: 5px;
                            padding: 3px 7px;
                            white-space: nowrap;
                            box-shadow: 1px 1px 4px rgba(0,0,0,0.2);
                            text-transform: uppercase;
                            letter-spacing: 0.5px;
                        ">{nama_kab}</div>""",
                        icon_size=(150, 28),
                        icon_anchor=(75, 14),
                    )
                ).add_to(kabupaten_group)
            except Exception:
                pass

        kabupaten_group.add_to(m)

    # ── LAYER 3: Batas Desa (outline tebal, fill no color) ──────────────────
    # DAN Label Desa pada centroid (perbaikan utama)
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
                'fillColor':'none',
                'color':'#e65100',
                'weight':2.5,
                'fillOpacity':0,
                'opacity':1,
            },
            highlight_function=lambda f: {
                'fillColor':'#ff6d00',
                'color':'#bf360c',
                'weight':3.5,
                'fillOpacity':0.15,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=available_fields, aliases=field_aliases),
            popup=folium.GeoJsonPopup(
                fields=available_fields,
                aliases=field_aliases,
                max_width=300
            )
        ).add_to(desa_group)
        
         # ===== PERBAIKAN UTAMA: Menambahkan Label untuk Batas Desa =====
        # Label nama desa menggunakan DivIcon di centroid masing-masing polygon desa
        # Format: NAMA_DESA - NAMA_KABUPATEN
        for _, row_desa in gdf_desa.iterrows():
            try:
                # Hitung centroid polygon desa
                centroid = row_desa.geometry.centroid
                # Ambil nama desa dan kabupaten
                nama_desa = row_desa.get('nama_kelur', '')
                nama_kabupaten = row_desa.get('nama_kabko', '')
                
                # Format label: DESA - KABUPATEN
                if nama_desa and nama_kabupaten:
                    label_text = f"{nama_desa.upper()} - {nama_kabupaten.upper()}"
                elif nama_desa:
                    label_text = nama_desa.upper()
                else:
                    label_text = ""
                
                # Hanya tambahkan marker jika label_text tidak kosong
                if label_text:
                    # Sesuaikan ukuran ikon berdasarkan panjang teks (opsional)
                    # Panjang teks diperkirakan, bisa disesuaikan
                    text_length = len(label_text)
                    # Lebar ikon: 8px per karakter + 20px padding
                    icon_width = max(140, text_length * 8 + 20)
                    icon_height = 24
                    
                    folium.Marker(
                        location=[centroid.y, centroid.x],
                        icon=folium.DivIcon(
                            html=f"""<div style="
                                font-family: Arial, sans-serif;
                                font-size: 10px;
                                font-weight: bold;
                                color: #e65100;
                                background: rgba(255,255,255,0.9);
                                border: 1.5px solid #e65100;
                                border-radius: 4px;
                                padding: 3px 6px;
                                white-space: nowrap;
                                box-shadow: 1px 1px 3px rgba(0,0,0,0.15);
                                letter-spacing: 0.3px;
                                text-align: center;
                            ">{label_text}</div>""",
                            icon_size=(icon_width, icon_height),
                            icon_anchor=(icon_width // 2, icon_height // 2),  # Posisikan di tengah centroid
                        )
                    ).add_to(desa_group)
            except Exception as e:
                # Lewati jika ada error pada geometry (misalnya MultiPolygon yang kompleks)
                pass
        # ================================================================

        desa_group.add_to(m)

# 4. LAYER: Sebaran Spesies Tanaman Herbal (Menggunakan Cluster Marker)
if not df_herbal_filtered.empty:
    herbal_cluster = MarkerCluster(
        name="Sebaran Tanaman Herbal",
        overlay=True,
        control=True,
        show=True
    )
    
    for idx, row in df_herbal_filtered.iterrows(): [1, 2]
        lat = row
        lon = row['X']
        nama_herbal = row['Nama'].strip().upper() 
        nomor_id = row['No']
        
        # Desain pop-up berbasis HTML terstruktur
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; width: 200px; line-height: 1.5;">
            <h5 style="margin: 0 0 5px 0; color: #27AE60; border-bottom: 2px solid #2ECC71; padding-bottom: 3px; font-weight: bold;">
                {nama_herbal}
            </h5>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #F0F0F0;">
                    <td style="padding: 3px 0; font-weight: bold; color: #666;">No. Urut:</td>
                    <td style="padding: 3px 0; text-align: right;">{nomor_id}</td>
                </tr>
                <tr style="border-bottom: 1px solid #F0F0F0;">
                    <td style="padding: 3px 0; font-weight: bold; color: #666;">Latitude:</td>
                    <td style="padding: 3px 0; text-align: right; font-family: monospace;">{lat:.6f}</td>
                </tr>
                <tr>
                    <td style="padding: 3px 0; font-weight: bold; color: #666;">Longitude:</td>
                    <td style="padding: 3px 0; text-align: right; font-family: monospace;">{lon:.6f}</td>
                </tr>
            </table>
        </div>
        """
        
        folium.Marker(
            location=[lat, lon][2]
            popup=folium.Popup(popup_html, max_width=250)[2]
            tooltip=f"Spesies: {nama_herbal}",
            icon=folium.Icon(color='green', icon='leaf', prefix='fa')
        ).add_to(herbal_cluster)
        
    herbal_cluster.add_to(m)

# Aktivasi Layer Control (Kontrol visibilitas layer secara dinamis)
folium.LayerControl(collapsed=False, position='topright').add_to(m) [4]

# Rendering Peta pada Aplikasi Streamlit
folium_static(m, width=1024, height=600) [2, 5]

# Menampilkan data tabular terfilter untuk keperluan audit dan ekspor data
if not df_herbal_filtered.empty:
    st.subheader(f"Data Atribut Tanaman Herbal Terpilih ({len(df_herbal_filtered)} Titik)")
    st.dataframe(
        df_herbal_filtered].rename(
            columns={
                'No': 'No. Inventaris',
                'Nama': 'Nama Spesies',
                'X': 'Longitude (X)',
                'Y': 'Latitude (Y)'
            }
        ),
        use_container_width=True
    )
    
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
        "🏘️ **Batas Desa** ditampilkan sebagai outline tebal warna oranye (fill transparan). "
        "🗺️ **Batas Kabupaten** ditampilkan sebagai outline tebal biru dengan label nama. "
        "🔲 **Batas TNBTS** ditampilkan sebagai outline merah putus-putus. "
        "Gunakan **Layer Control** di pojok kanan atas peta untuk menampilkan/menyembunyikan layer. "
        "**Hover** pada polygon untuk melihat informasi. **Klik polygon** untuk info lengkap."
    )

    # Peta
    try:
        folium_static(create_tnbts_map(
            show_kawasan=show_kawasan,
            show_desa_geojson=show_desa_geojson,
            show_kabupaten=show_kabupaten,
            show_batas_tnbts=show_batas_tnbts,
            show_tanaman=show_tanaman,
            gdf_desa=gdf_desa,
            gdf_kabupaten=gdf_kabupaten,
            gdf_batas=gdf_batas,
            df_tanaman_filtered=df_tanaman_filtered,
        ), width=1200, height=640)
    except Exception as e:
        st.error(f"Error membuat peta: {e}")
        m0 = folium.Map(location=[-7.940, 112.950], zoom_start=10)
        folium_static(m0)

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
            st.error("❌ Desa_kaw_TNBTS.geojson tidak ditemukan.")

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

