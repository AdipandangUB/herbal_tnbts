import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import json
import os
from folium.plugins import MarkerCluster
import re
from datetime import datetime

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
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'highlighted_plants' not in st.session_state:
    st.session_state.highlighted_plants = []

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNGSI GEOSPATIAL (GeoJSON & Reproyeksi)
# ─────────────────────────────────────────────────────────────────────────────
def _find_file(filename):
    """Mencari file di beberapa direktori kandidat."""
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    candidates = [
        filename,
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(script_dir, 'data', filename),
        os.path.join(os.getcwd(), 'data', filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _find_geojson(filename):
    """Mencari file GeoJSON di beberapa direktori kandidat."""
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
    candidates = [
        filename,
        os.path.join(script_dir, filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(script_dir, 'data', filename),
        os.path.join(os.getcwd(), 'data', filename),
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
    """
    Membaca data sebaran tanaman herbal dari berkas Excel.
    Mendukung format .xlsx dan .xls
    """
    filepath = _find_file(filename)
    if not filepath:
        st.sidebar.error(f"Berkas data sebaran tanaman herbal '{filename}' tidak ditemukan.")
        return pd.DataFrame()
    
    try:
        # Coba baca sebagai Excel
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            # Fallback ke CSV
            df = pd.read_csv(filepath)
        
        # Bersihkan nama kolom
        df.columns = df.columns.str.strip()
        
        # Cari kolom yang sesuai
        # Kolom koordinat bisa bernama X, x, longitude, Longitude, lon, dll
        x_col = None
        y_col = None
        name_col = None
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['x', 'lon', 'longitude', 'long']:
                x_col = col
            elif col_lower in ['y', 'lat', 'latitude']:
                y_col = col
            elif col_lower in ['nama', 'name', 'jenis', 'spesies', 'tanaman']:
                name_col = col
        
        # Jika tidak ditemukan, gunakan kolom pertama sebagai nama dan X,Y sebagai koordinat
        if x_col is None:
            for col in df.columns:
                if 'x' in col.lower():
                    x_col = col
                    break
        
        if y_col is None:
            for col in df.columns:
                if 'y' in col.lower() or 'lat' in col.lower():
                    y_col = col
                    break
        
        if name_col is None:
            # Cari kolom yang berisi teks (bukan numerik)
            for col in df.columns:
                if df[col].dtype == 'object':
                    name_col = col
                    break
            if name_col is None:
                name_col = df.columns[0]
        
        # Jika masih belum ditemukan, gunakan indeks kolom yang umum
        if x_col is None and len(df.columns) >= 3:
            # Format: No, Nama, X, Y
            if 'no' in df.columns[0].lower() and 'nama' in df.columns[1].lower():
                name_col = df.columns[1]
                x_col = df.columns[2]
                y_col = df.columns[3]
            else:
                name_col = df.columns[1]
                x_col = df.columns[2]
                y_col = df.columns[3]
        
        # Konversi koordinat ke numerik
        df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
        
        # Hapus baris dengan koordinat NaN
        df = df.dropna(subset=[x_col, y_col])
        
        # Buat dataframe baru dengan kolom standar
        result_df = pd.DataFrame({
            'No': df.index + 1,
            'Nama': df[name_col] if name_col else 'Tanaman',
            'X': df[x_col],
            'Y': df[y_col]
        })
        
        # Tambahkan informasi tambahan jika ada
        if 'jenis' in df.columns:
            result_df['Jenis'] = df['jenis']
        else:
            result_df['Jenis'] = 'Herba'
        
        if 'fungsi' in df.columns:
            result_df['Fungsi'] = df['fungsi']
        else:
            result_df['Fungsi'] = 'Obat Tradisional'
        
        if 'kawasan' in df.columns:
            result_df['Kawasan'] = df['kawasan']
        else:
            result_df['Kawasan'] = 'TNBTS'
        
        if 'desa' in df.columns:
            result_df['Desa'] = df['desa']
        else:
            result_df['Desa'] = 'Desa Penyangga'
        
        st.sidebar.success(f"✅ Berhasil memuat {len(result_df)} data tanaman dari {filename}")
        return result_df
        
    except Exception as e:
        st.sidebar.error(f"Gagal membaca data sebaran tanaman herbal: {e}")
        return pd.DataFrame()


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

    .chat-message {
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
        max-width: 85%;
        box-shadow: 0 1px 3px rgba(0,0,0,.1);
    }
    .chat-message.user {
        background: linear-gradient(135deg, #4CAF50, #2E7D32);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .chat-message.bot {
        background: #f5f5f5;
        color: #333;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border-left: 4px solid #4CAF50;
    }
    
    .chat-container {
        max-height: 450px;
        overflow-y: auto;
        padding: 10px;
        background: #fafafa;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    
    .metric-card {
        background:white; padding:1rem; border-radius:10px;
        box-shadow:0 2px 4px rgba(0,0,0,.1); text-align:center;
        border-left:4px solid #2E7D32; margin-bottom:1rem;
        transition:transform .3s ease;
    }
    .metric-card:hover { transform:translateY(-5px); box-shadow:0 4px 8px rgba(0,0,0,.15); }
    .metric-card h3 { color:#2E7D32; margin:0; font-size:1.8rem; font-weight:bold; }
    .metric-card p  { color:#666; margin:.2rem 0 0 0; font-size:.9rem; text-transform:uppercase; }

    .info-box {
        background-color:#E8F5E9; border-left:4px solid #4CAF50;
        padding:1.5rem; border-radius:5px; margin:1rem 0;
    }
    .info-box h4 { color:#2E7D32; margin-top:0; margin-bottom:1rem; }
    
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
    <p>Taman Nasional Bromo Tengger Semeru (TNBTS) • Data Tanaman Herbal Terintegrasi</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
gdf_desa = load_desa_geojson()
gdf_kabupaten = load_kabupaten_geojson()
gdf_batas = load_batas_geojson()
df_herbal = load_herbal_data("Titik Rapihin.xlsx")

# Jika df_herbal kosong, coba alternatif
if df_herbal.empty:
    df_herbal = load_herbal_data("Titik Rapihin.xls")
if df_herbal.empty:
    df_herbal = load_herbal_data("Titik Rapihin.csv")

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
    menu_options = ["Peta Sebaran", "Chatbot Herbal", "Peta 3D Pegunungan", "Data Tanaman", "Statistik", "Informasi"]
    menu_icons   = ["🗺️", "🤖", "🏔️", "📋", "📊", "ℹ️"]
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed",
        key="menu_radio"
    )
    st.markdown("---")

    # Filter data jika tersedia
    if not df_herbal.empty:
        st.markdown("### 🔍 Filter Data")
        
        semua_tanaman = sorted(df_herbal['Nama'].unique())
        selected_tanaman = st.multiselect(
            "Pilih Nama Tanaman",
            options=["Semua"] + semua_tanaman,
            default=["Semua"],
            help="Pilih satu atau lebih tanaman"
        )
        
        # Filter kawasan jika tersedia
        if 'Kawasan' in df_herbal.columns:
            kawasan_options = ["Semua Kawasan"] + sorted(df_herbal['Kawasan'].unique())
            selected_kawasan = st.selectbox("Filter Kawasan Ekologi", kawasan_options)
        else:
            selected_kawasan = "Semua Kawasan"

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
        
        # Status file
        _p_desa = _find_geojson('Desa_kaw_TNBTS.geojson')
        _p_kab  = _find_geojson('Kabupaten_kaw_TNBTS.geojson')
        _p_bts  = _find_geojson('Batas_TNBTS.geojson')
        _p_data = _find_file('Titik Rapihin.xlsx')
        
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
        
        if _p_data:
            _fsz = os.path.getsize(_p_data) / 1024
            st.markdown(f"""
            <div class="status-badge">
                ✅ <b>Titik Rapihin.xlsx</b><br><small>{_fsz:.1f} KB • {len(df_herbal)} data tanaman</small>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-badge" style="border-left-color:#f44336;">
                ❌ <b>Titik Rapihin.xlsx</b><br><small>File tidak ditemukan</small>
            </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
if not df_herbal.empty:
    if "Semua" not in selected_tanaman and selected_tanaman:
        df_herbal_filtered = df_herbal[df_herbal['Nama'].isin(selected_tanaman)]
    else:
        df_herbal_filtered = df_herbal.copy()

    if selected_kawasan != "Semua Kawasan" and 'Kawasan' in df_herbal_filtered.columns:
        df_herbal_filtered = df_herbal_filtered[
            df_herbal_filtered['Kawasan'] == selected_kawasan
        ]
else:
    df_herbal_filtered = pd.DataFrame()

# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI CHATBOT AI (UNTUK DATA HERBAL)
# ─────────────────────────────────────────────────────────────────────────────
def extract_symptoms_from_text(text):
    """Ekstrak gejala penyakit dari teks."""
    symptom_keywords = {
        'demam': ['demam', 'panas', 'meriang', 'meriang'],
        'batuk': ['batuk', 'pilek', 'flu', 'influenza', 'bersin'],
        'nyeri': ['nyeri', 'sakit', 'pegal', 'linu', 'rematik'],
        'luka': ['luka', 'borok', 'bisul', 'cidera'],
        'pencernaan': ['mual', 'muntah', 'diare', 'perut', 'kembung', 'mulas'],
        'darah': ['tekanan darah', 'darah tinggi', 'hipertensi', 'kolesterol'],
        'antiradang': ['radang', 'bengkak', 'peradangan'],
        'diuretik': ['susah kencing', 'batu ginjal'],
        'antiseptik': ['infeksi', 'kuman', 'bakteri'],
        'kesuburan': ['kesuburan', 'hamil', 'reproduksi'],
        'antioksidan': ['antioksidan', 'penuaan', 'radikal bebas']
    }
    
    found_symptoms = []
    for symptom, keywords in symptom_keywords.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found_symptoms.append(symptom)
                break
    
    return list(set(found_symptoms))


def find_herbal_by_symptoms(symptoms, df_herbal):
    """Mencari tanaman herbal berdasarkan gejala."""
    if symptoms:
        symptom_matches = []
        for symptom in symptoms:
            # Cari berdasarkan nama atau fungsi
            for col in ['Nama', 'Jenis', 'Fungsi']:
                if col in df_herbal.columns:
                    matches = df_herbal[df_herbal[col].str.contains(symptom, case=False, na=False)].index.tolist()
                    symptom_matches.extend(matches)
        if symptom_matches:
            return df_herbal.loc[list(set(symptom_matches))]
    return df_herbal


def generate_chatbot_response_herbal(user_input, df_herbal):
    """Generate response from chatbot based on user input for herbal data."""
    user_input_lower = user_input.lower()
    
    greetings = ['halo', 'hai', 'hello', 'hi', 'selamat pagi', 'selamat siang', 'selamat sore', 'selamat malam']
    if any(greeting in user_input_lower for greeting in greetings):
        return "🌿 **Halo!** Saya adalah Asisten Tanaman Herbal TNBTS. Saya dapat membantu Anda menemukan tanaman herbal berdasarkan gejala penyakit yang Anda alami. Coba tanyakan: 'Tanaman untuk demam' atau 'Apa obat batuk?'"
    
    if 'bantuan' in user_input_lower or 'help' in user_input_lower:
        return """
        🤖 **Cara Menggunakan Chatbot:**
        
        1. **Sebutkan gejala penyakit** yang Anda alami
        
        **Contoh pertanyaan:**
        - "Tanaman untuk demam"
        - "Apa obat batuk?"
        - "Tanaman antiradang"
        - "Saya sakit perut"
        """
    
    symptoms = extract_symptoms_from_text(user_input)
    
    if not symptoms:
        return """
        🤔 **Saya belum memahami pertanyaan Anda.** 
        
        Untuk menggunakan chatbot ini, silakan sebutkan:
        - **Gejala penyakit** yang Anda alami
        
        Contoh: "Tanaman untuk demam"
        
        Ketik **'bantuan'** untuk melihat panduan lengkap.
        """
    
    results = find_herbal_by_symptoms(symptoms, df_herbal)
    
    if results.empty:
        response = "🌿 **Maaf, tidak ditemukan tanaman herbal** yang sesuai dengan kriteria Anda."
        response += f"\n\n💊 Gejala: **{', '.join(symptoms)}**"
        response += "\n\n💡 **Saran:** Coba gunakan kata kunci lain atau konsultasikan dengan ahli kesehatan setempat."
        return response
    
    response = "🌿 **Ditemukan tanaman herbal yang dapat membantu!**\n\n"
    if symptoms:
        response += f"💊 **Gejala:** {', '.join(symptoms)}\n"
    response += f"🌱 **Jumlah tanaman ditemukan:** {len(results)}\n\n"
    
    response += "**Rekomendasi Tanaman:**\n"
    for i, (_, row) in enumerate(results.head(5).iterrows()):
        response += f"\n{i+1}. **{row['Nama']}**\n"
        response += f"   - Koordinat: {row['Y']:.6f}, {row['X']:.6f}\n"
        if 'Jenis' in row:
            response += f"   - Jenis: {row['Jenis']}\n"
        if 'Fungsi' in row:
            response += f"   - Fungsi: {row['Fungsi']}\n"
    
    if len(results) > 5:
        response += f"\n📋 **{len(results)-5} tanaman lainnya** dapat dilihat di Data Tanaman."
    
    response += "\n\n💡 **Catatan:** Selalu konsultasikan dengan ahli kesehatan sebelum mengonsumsi tanaman herbal."
    return response


# ─────────────────────────────────────────────────────────────────────────────
# KONSTANTA WARNA
# ─────────────────────────────────────────────────────────────────────────────
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
    gdf_desa, gdf_kabupaten, gdf_batas, df_tanaman_filtered, highlight_points=None
):
    m = folium.Map(
        location=[-7.955, 112.953],
        zoom_start=11,
        tiles='OpenStreetMap',
        name='OpenStreetMap'
    )

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='🛰️ Satelit'
    ).add_to(m)
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap', name='🗻 Terrain'
    ).add_to(m)

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

    if show_tanaman and not df_tanaman_filtered.empty:
        herbal_cluster = MarkerCluster(
            name="🌿 Sebaran Tanaman Herbal",
            overlay=True,
            control=True,
            show=True
        )
        
        highlight_set = set(highlight_points) if highlight_points else set()
        
        for idx, row in df_tanaman_filtered.iterrows():
            lat = row['Y']
            lon = row['X']
            nama = row['Nama']
            
            is_highlighted = nama in highlight_set
            
            if is_highlighted:
                icon_color = 'red'
                icon_icon = 'star'
            else:
                icon_color = 'green'
                icon_icon = 'leaf'
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px; line-height: 1.5;">
                <h5 style="margin: 0 0 5px 0; color: #27AE60; border-bottom: 2px solid #2ECC71; padding-bottom: 3px; font-weight: bold;">
                    {'⭐ ' if is_highlighted else '🌿 '}{nama}
                </h5>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">Koordinat:</td>
                        <td style="padding: 3px 0; text-align: right; font-family: monospace;">{lat:.6f}, {lon:.6f}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0F0F0;">
                        <td style="padding: 3px 0; font-weight: bold; color: #666;">No. Urut:</td>
                        <td style="padding: 3px 0; text-align: right;">{row['No']}</td>
                    </tr>
                </table>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{'⭐ ' if is_highlighted else ''}{nama}",
                icon=folium.Icon(color=icon_color, icon=icon_icon, prefix='fa')
            ).add_to(herbal_cluster)
            
        herbal_cluster.add_to(m)

    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    return m

# ═════════════════════════════════════════════════════════════════════════════
# MENU: CHATBOT HERBAL
# ═════════════════════════════════════════════════════════════════════════════
if selected == "Chatbot Herbal":
    st.markdown("## 🤖 Asisten Tanaman Herbal TNBTS")
    
    if df_herbal.empty:
        st.error("❌ Data tanaman herbal tidak tersedia. Pastikan file 'Titik Rapihin.xlsx' tersedia.")
    else:
        st.markdown("""
        <div class="info-box">
            <h4>💬 Tanyakan Tanaman Herbal Berdasarkan Gejala</h4>
            <p>
                Chatbot ini akan membantu Anda menemukan tanaman herbal di sekitar TNBTS 
                berdasarkan <b>gejala penyakit</b> yang Anda alami.
            </p>
            <p><b>Contoh pertanyaan:</b><br>
            - "Tanaman untuk demam"<br>
            - "Apa obat batuk?"<br>
            - "Tanaman antiradang"<br>
            - "Saya sakit perut"
            </p>
        </div>
        """, unsafe_allow_html=True)

        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-message user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message bot">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        col_input, col_button = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "💬 Tanyakan sesuatu...",
                placeholder="Contoh: Tanaman untuk demam",
                key="chat_input",
                label_visibility="collapsed"
            )
        with col_button:
            send_button = st.button("📤 Kirim", use_container_width=True)
        
        if send_button and user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            response = generate_chatbot_response_herbal(user_input, df_herbal)
            
            highlighted = []
            if "**Rekomendasi Tanaman:**" in response:
                lines = response.split('\n')
                for line in lines:
                    if '**' in line:
                        parts = line.split('**')
                        if len(parts) >= 3:
                            highlighted.append(parts[1].strip())
            
            st.session_state.highlighted_plants = highlighted
            st.session_state.chat_history.append({'role': 'bot', 'content': response})
            st.rerun()
        
        if st.button("🗑️ Hapus Riwayat Chat"):
            st.session_state.chat_history = []
            st.session_state.highlighted_plants = []
            st.rerun()
        
        if st.session_state.highlighted_plants:
            st.markdown("---")
            st.markdown("### 🗺️ Peta Sebaran Tanaman yang Direkomendasikan")
            st.markdown("⭐ **Titik berwarna merah dengan bintang** adalah tanaman yang direkomendasikan berdasarkan pertanyaan Anda.")
            
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
                    df_tanaman_filtered=df_herbal,
                    highlight_points=st.session_state.highlighted_plants
                )
                folium_static(m, width=1200, height=500)
            except Exception as e:
                st.error(f"Error membuat peta: {e}")

# ═════════════════════════════════════════════════════════════════════════════
# MENU: PETA SEBARAN
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Peta Sebaran":
    st.markdown("## 🗺️ Peta Interaktif Tanaman Herbal TNBTS")
    
    if df_herbal.empty:
        st.error("❌ Data tanaman herbal tidak tersedia. Pastikan file 'Titik Rapihin.xlsx' tersedia.")
    else:
        st.markdown(
            f"Visualisasi sebaran **{len(df_herbal_filtered)} titik tanaman herbal** "
            f"dari **{df_herbal['Nama'].nunique()} spesies** di kawasan TNBTS."
        )

        # Metric cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card"><h3>{len(df_herbal)}</h3>
                <p>🌿 Total Titik</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card"><h3>{df_herbal['Nama'].nunique()}</h3>
                <p>🌱 Spesies Unik</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card"><h3>{len(df_herbal_filtered)}</h3>
                <p>📌 Ditampilkan</p></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card"><h3>{len(gdf_desa)}</h3>
                <p>🏘️ Desa</p></div>""", unsafe_allow_html=True)

        st.info(
            "🏔️ **Layer Batas TNBTS** dan **🏘️ Batas Desa** ditampilkan sebagai outline. "
            "🌿 **Titik hijau** adalah sebaran tanaman herbal. "
            "Gunakan **Layer Control** di pojok kanan atas peta untuk mengatur tampilan."
        )

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
                df_tanaman_filtered=df_herbal_filtered,
                highlight_points=None
            )
            folium_static(m, width=1200, height=640)
        except Exception as e:
            st.error(f"Error membuat peta: {e}")

        # Tabel ringkas
        with st.expander(f"📋 Daftar {len(df_herbal_filtered)} Tanaman yang Ditampilkan"):
            st.dataframe(
                df_herbal_filtered,
                use_container_width=True, height=350, hide_index=True
            )

# ═════════════════════════════════════════════════════════════════════════════
# MENU: PETA 3D
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Peta 3D Pegunungan":
    st.markdown("## 🏔️ Peta 3D Pegunungan TNBTS")
    st.markdown("Visualisasi 3D interaktif — putar 360° dengan mouse/touch")

    st.markdown(f"""
    <div style="border-radius:10px;overflow:hidden;
                box-shadow:0 4px 8px rgba(0,0,0,.2);height:{map_height_3d}px;">
        <iframe
            title="Mount Bromo / Bromo Tengger Semeru National Park"
            frameborder="0" allowfullscreen
            src="https://sketchfab.com/models/72f1c983ba4040eab89d75eb2b0d3e32/embed"
            style="width:100%;height:{map_height_3d}px;border:none;border-radius:10px;">
        </iframe>
    </div>""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# MENU: DATA TANAMAN
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Data Tanaman":
    st.markdown("## 📋 Data Tanaman Herbal TNBTS")
    
    if df_herbal.empty:
        st.error("❌ Data tanaman herbal tidak tersedia. Pastikan file 'Titik Rapihin.xlsx' tersedia.")
    else:
        tab1, tab2 = st.tabs(["🌿 Semua Data Tanaman", "📊 Statistik Singkat"])

        with tab1:
            search = st.text_input(
                "🔍 Cari (nama tanaman):",
                placeholder="Contoh: adas / jahe / jarak ..."
            )
            df_show = df_herbal_filtered.copy()
            if search:
                mask = df_show['Nama'].str.contains(search, case=False, na=False)
                df_show = df_show[mask]
                st.info(f"Ditemukan **{len(df_show)}** hasil")

            st.dataframe(
                df_show,
                use_container_width=True, height=500, hide_index=True
            )
            
            cc1, cc2, cc3 = st.columns([1, 2, 1])
            with cc2:
                st.download_button(
                    "📥 Download CSV Data Tanaman",
                    data=df_herbal.to_csv(index=False),
                    file_name="data_tanaman_herbal_tnbts.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with tab2:
            st.markdown("### 📊 Statistik Tanaman")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Top 10 Tanaman Terbanyak")
                top_plants = df_herbal['Nama'].value_counts().head(10)
                st.dataframe(
                    pd.DataFrame({'Tanaman': top_plants.index, 'Jumlah': top_plants.values}),
                    use_container_width=True, hide_index=True
                )
            
            with col2:
                st.markdown("#### Distribusi Spesies")
                st.metric("Total Spesies Unik", df_herbal['Nama'].nunique())
                st.metric("Total Titik Data", len(df_herbal))

# ═════════════════════════════════════════════════════════════════════════════
# MENU: STATISTIK
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal TNBTS")
    
    if df_herbal.empty:
        st.error("❌ Data tanaman herbal tidak tersedia.")
    else:
        st.markdown("### 🌿 Sebaran Spesies Tanaman")
        
        # Top tanaman
        top_counts = df_herbal['Nama'].value_counts().head(15)
        st.bar_chart(top_counts, use_container_width=True)
        
        st.markdown("### 📋 Detail Statistik")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spesies", df_herbal['Nama'].nunique())
        with col2:
            st.metric("Total Titik Data", len(df_herbal))
        with col3:
            # Hitung rata-rata tanaman per titik
            avg = len(df_herbal) / df_herbal['Nama'].nunique()
            st.metric("Rata-rata per Spesies", f"{avg:.1f}")

# ═════════════════════════════════════════════════════════════════════════════
# MENU: INFORMASI
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## ℹ️ Informasi TNBTS")
    st.markdown("""
    <div class="info-box">
        <h4>🌋 Taman Nasional Bromo Tengger Semeru</h4>
        <p>TNBTS adalah kawasan konservasi di Jawa Timur dengan keanekaragaman hayati tinggi.
        WebGIS ini menampilkan data sebaran tanaman herbal yang teridentifikasi di kawasan TNBTS.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_herbal.empty:
        st.markdown(f"""
        <div class="info-box" style="border-left-color:#2196F3;">
            <h4>📊 Data Tanaman Herbal</h4>
            <p>
                <b>{len(df_herbal)}</b> titik data tanaman herbal<br>
                <b>{df_herbal['Nama'].nunique()}</b> spesies unik teridentifikasi
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 📍 Sumber Data
    - **Data Tanaman:** Hasil survei lapangan Tim Peneliti UB (2026)
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
    <p>🌿 WebGIS Resiliensi Kesehatan Terhadap Potensi Bencana</p>
    <p>Bromo – Kaldera Tengger – Semeru Melalui Konsumsi Tanaman Herbal di TNBTS</p>
    <p>© Ekspedisi Tanaman Herbal TNBTS untuk Health Security — 2026</p>
</div>
""", unsafe_allow_html=True)
