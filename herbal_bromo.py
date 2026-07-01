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
        gdf = gpd.read_file(path, encoding='utf-8')
        if gdf.crs is None:
            st.sidebar.warning(f"⚠️ File {filename} tidak memiliki CRS. Ditetapkan ke EPSG:4326.")
            gdf.set_crs("EPSG:4326", inplace=True)
        return gdf
    except Exception as e:
        st.sidebar.warning(f"⚠️ Error loading {filename}: {e}")
        return gpd.GeoDataFrame()


# ── Data Desa kawasan TNBTS (embedded fallback) ────────────────────────────
_DESA_GEOJSON_EMBEDDED = {"type":"FeatureCollection","name":"Desa_kaw_TNBTS","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[]}

@st.cache_data
def load_desa_geojson():
    gdf = _load_geojson('Desa_kaw_TNBTS.geojson')
    if not gdf.empty:
        return gdf
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
    try:
        _kab_data = {"type":"FeatureCollection","name":"Kabupaten_kaw_TNBTS","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":[]}
        gdf2 = gpd.GeoDataFrame.from_features(_kab_data["features"])
        gdf2.set_crs("EPSG:4326", inplace=True)
        return gdf2
    except Exception:
        return gpd.GeoDataFrame()


@st.cache_data
def load_batas_geojson():
    gdf = _load_geojson('Batas_TNBTS.geojson')
    if not gdf.empty:
        if gdf.crs and gdf.crs.to_epsg() != 4326:
            try:
                gdf = gdf.to_crs("EPSG:4326")
            except Exception as e:
                st.sidebar.error(f"❌ Gagal memproyeksikan Batas TNBTS: {e}")
                return gpd.GeoDataFrame()
        return gdf
    return gpd.GeoDataFrame()


@st.cache_data
def load_herbal_data(filename):
    filepath = _find_geojson(filename)
    if not filepath:
        st.sidebar.error(f"Berkas data sebaran tanaman herbal '{filename}' tidak ditemukan.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        df = df.dropna(subset=['X', 'Y'])
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        return df
    except Exception as e:
        st.sidebar.error(f"Gagal membaca data sebaran tanaman herbal: {e}")
        return pd.DataFrame()


@st.cache_data
def load_tanaman_herbal_data():
    records = [
        (1, 'Adas', 'Foeniculum vulgare', 'Herba', 'Pencernaan', -7.937000, 112.949336, 'Zona Budidaya & Pekarangan', 1900, 'Sekitar Desa Ngadisari & Wonokitri', 'Ngadisari, Wonokitri'),
        (2, 'Ajeran putih', 'Bidens pilosa L.', 'Herba', 'Antiradang', -7.945000, 112.969131, 'Savana Bromo & Lereng Terbuka', 2050, 'Lautan Pasir & Savana Bromo', 'Seluruh desa penyangga'),
        # ... tambahkan data lainnya sesuai kebutuhan
    ]
    df = pd.DataFrame(records, columns=[
        'id','nama_tanaman','nama_latin','jenis','fungsi_utama',
        'latitude','longitude','kawasan','ketinggian','lokasi_detail','desa'
    ])
    df['status_konservasi'] = 'Umum'
    df.loc[df['nama_tanaman'].isin(['Purwoceng','Parijoto','Anggrek tanah']), 'status_konservasi'] = 'Dilindungi'
    np.random.seed(42)
    df['jumlah'] = np.random.randint(10, 500, len(df))
    return df

# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA WARNA
# ─────────────────────────────────────────────────────────────────────────────
KAWASAN_HEX = {
    "Blok Ireng-Ireng & Hutan Atas": "#1B5E20",
    "Kantong Air & Lembah": "#0277BD",
    "Lereng Semeru & Dataran Tinggi": "#6D4C41",
    "Ranu Darungan & Sekitar Danau": "#00838F",
    "Savana Bromo & Lereng Terbuka": "#F57F17",
    "Tepi Hutan & Zona Transisi": "#558B2F",
    "Zona Budidaya & Pekarangan": "#AD1457",
    "Zona Pesisir & Pantai Selatan": "#1565C0",
}

JENIS_COLOR = {
    'Herba': 'cadetblue',
    'Pohon': 'green',
    'Semak': 'lightgreen',
    'Pakis': 'darkgreen',
    'Rumput': 'beige',
    'Bunga': 'pink',
    'Perdu': 'purple',
    'Lumut': 'lightgray',
}

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

    # ── LAYER 1: Batas TNBTS ────────────────────────────────────────────────
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
                sticky=False
            )
        ).add_to(batas_group)
        batas_group.add_to(m)

    # ── LAYER 2: Batas Kabupaten ─────────────────────────────────────────────
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
                sticky=False
            )
        ).add_to(kabupaten_group)
        kabupaten_group.add_to(m)

    # ── LAYER 3: Batas Desa ──────────────────────────────────────────────────
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
                fields=available_fields, aliases=field_aliases)
        ).add_to(desa_group)
        desa_group.add_to(m)

    # ── LAYER 4: Sebaran Tanaman ─────────────────────────────────────────────
    if show_tanaman and not df_tanaman_filtered.empty:
        herbal_cluster = MarkerCluster(
            name="🌿 Sebaran Tanaman Herbal",
            overlay=True,
            control=True,
            show=True
        )
        
        for idx, row in df_tanaman_filtered.iterrows():
            lat = row['latitude']
            lon = row['longitude']
            nama_tanaman = row['nama_tanaman']
            nama_latin = row['nama_latin']
            jenis = row['jenis']
            fungsi = row['fungsi_utama']
            kawasan = row['kawasan']
            desa = row['desa']
            ketinggian = row['ketinggian']
            status = row.get('status_konservasi', 'Umum')
            
            if status == 'Dilindungi':
                icon_color = 'red'
                icon_icon = 'lock'
            else:
                icon_color = JENIS_COLOR.get(jenis, 'green')
                icon_icon = 'leaf'
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px; line-height: 1.5;">
                <h5 style="margin: 0 0 5px 0; color: #27AE60; border-bottom: 2px solid #2ECC71; padding-bottom: 3px; font-weight: bold;">
                    🌿 {nama_tanaman}
                </h5>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Nama Latin:</td>
                        <td style="padding: 3px 0; text-align: right; font-style: italic;">{nama_latin}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Jenis:</td>
                        <td style="padding: 3px 0; text-align: right;">{jenis}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Fungsi:</td>
                        <td style="padding: 3px 0; text-align: right;">{fungsi}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Kawasan:</td>
                        <td style="padding: 3px 0; text-align: right;">{kawasan}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Desa:</td>
                        <td style="padding: 3px 0; text-align: right;">{desa}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Ketinggian:</td>
                        <td style="padding: 3px 0; text-align: right;">{ketinggian} mdpl</td>
                    </tr>
                    <tr>
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Status:</td>
                        <td style="padding: 3px 0; text-align: right;">
                            <span style="background: {'#FF5722' if status == 'Dilindungi' else '#4CAF50'}; 
                                         color: white; padding: 2px 8px; border-radius: 12px; font-size: 10px;">
                                {status}
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{nama_tanaman} ({jenis}) - {kawasan}",
                icon=folium.Icon(color=icon_color, icon=icon_icon, prefix='fa')
            ).add_to(herbal_cluster)
            
        herbal_cluster.add_to(m)

    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    return m

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN STREAMLIT (HANYA SEKALI)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WebGIS Tanaman Herbal TNBTS",
    page_icon="🌿",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# INISIALISASI SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
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
# MUSIK (Floating Player)
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
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
gdf_desa = load_desa_geojson()
gdf_kabupaten = load_kabupaten_geojson()
gdf_batas = load_batas_geojson()
df_tanaman = load_tanaman_herbal_data()

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
    semua_tanaman = sorted(df_tanaman['nama_tanaman'].unique())
    selected_tanaman = st.multiselect(
        "Pilih Nama Tanaman",
        options=["Semua"] + semua_tanaman,
        default=["Semua"],
        help="Pilih satu atau lebih tanaman"
    )

    kawasan_options = ["Semua Kawasan"] + sorted(df_tanaman['kawasan'].unique())
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
# FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
if "Semua" not in selected_tanaman and selected_tanaman:
    df_tanaman_filtered = df_tanaman[df_tanaman['nama_tanaman'].isin(selected_tanaman)]
else:
    df_tanaman_filtered = df_tanaman.copy()

if selected_kawasan != "Semua Kawasan":
    df_tanaman_filtered = df_tanaman_filtered[
        df_tanaman_filtered['kawasan'] == selected_kawasan
    ]

# ═════════════════════════════════════════════════════════════════════════════
# MENU: PETA SEBARAN
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

    # Info layer
    st.info(
        "🏔️ **Layer Kawasan Ekologi** aktif — 8 zona ditampilkan sebagai polygon berwarna. "
        "🏘️ **Batas Desa** ditampilkan sebagai outline tebal warna oranye (fill transparan). "
        "🗺️ **Batas Kabupaten** ditampilkan sebagai outline tebal biru dengan label nama. "
        "🔲 **Batas TNBTS** ditampilkan sebagai outline merah putus-putus. "
        "Gunakan **Layer Control** di pojok kanan atas peta untuk menampilkan/menyembunyikan layer. "
        "**Hover** pada polygon untuk melihat informasi. **Klik polygon** untuk info lengkap."
    )

    # Tampilkan peta
    try:
        m = create_tnbts_map(
            show_kawasan=show_kawasan,
            show_desa_geojson=show_desa_geojson,
            show_kabupaten=show_kabupaten,
            show_batas_tnbts=show_batas_tnbts,
            show_tanaman=show_tanaman,
            gdf_desa=gdf_desa,
            gdf_kabupaten=gdf_kabupaten,
            gdf_batas=gdf_batas,
            df_tanaman_filtered=df_tanaman_filtered,
        )
        folium_static(m, width=1200, height=640)
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
# MENU: PETA 3D
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
# MENU: DATA TANAMAN
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
# MENU: STATISTIK
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
# MENU: INFORMASI
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
    
    # Buat dictionary kawasan dari data tanaman
    kawasan_dict = {}
    for k in df_tanaman['kawasan'].unique():
        kawasan_dict[k] = {
            'spesies': len(df_tanaman[df_tanaman['kawasan'] == k]),
            'deskripsi': 'Kawasan ekologi TNBTS',
            'ketinggian': 'Beragam'
        }
    
    kw_cols_ui = st.columns(2)
    for i, (kw, data) in enumerate(kawasan_dict.items()):
        col_h = KAWASAN_HEX.get(kw, '#555')
        cnt = data['spesies']
        with kw_cols_ui[i % 2]:
            st.markdown(
                f'<div style="border-left:5px solid {col_h};padding:.6rem 1rem;'
                f'margin-bottom:.6rem;background:#fafafa;border-radius:0 8px 8px 0;">'
                f'<b style="font-size:16px;">🌿</b> '
                f'<b style="color:{col_h};">{kw}</b><br>'
                f'<small>⛰️ {data["ketinggian"]} &nbsp;|&nbsp; 🌿 {cnt} spesies</small><br>'
                f'<span style="font-size:.85rem;color:#555;">{data["deskripsi"]}</span></div>',
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
