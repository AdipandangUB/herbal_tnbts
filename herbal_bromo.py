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
        (3, 'Alang-alang', 'Imperata cylindrica L.', 'Rumput', 'Diuretik', -7.943798, 112.966556, 'Savana Bromo & Lereng Terbuka', 2000, 'Padang Savana Tengger', 'Ngadas, Argosari'),
        (4, 'Andong', 'Cordyline fruticosa Linn', 'Pohon', 'Menghentikan pendarahan', -7.960000, 112.938313, 'Kantong Air & Lembah', 1750, 'Lembah Sumber Air TNBTS', 'Ngadas, Ranupani'),
        (5, 'Awar-awar', 'Ficus septica Burm.f.', 'Pohon', 'Antiradang', -7.924000, 112.933867, 'Tepi Hutan & Zona Transisi', 1850, 'Tepi Hutan Cemara – Desa Ngadisari', 'Ngadisari, Wonokitri'),
        (6, 'Bakung', 'Crinum asiaticium L.', 'Herba', 'Mengurangi bengkak', -7.904000, 112.952032, 'Ranu Darungan & Sekitar Danau', 1860, 'Tepi Ranu Darungan', 'Ranupani'),
        (7, 'Bawang merah', 'Allium cepa L.', 'Herba', 'Penurun demam', -7.935557, 112.946294, 'Zona Budidaya & Pekarangan', 1900, 'Ladang Pertanian Tengger', 'Seluruh desa penyangga'),
        (8, 'Bawang putih', 'Allium sativum', 'Herba', 'Menurunkan tekanan darah', -7.980000, 112.988530, 'Lereng Semeru & Dataran Tinggi', 2200, 'Lereng Atas Semeru – Ranupani', 'Ranupani, Argosari'),
        (9, 'Beluntas', 'Pluchea indica', 'Semak', 'Pencernaan', -8.020000, 112.995528, 'Zona Pesisir & Pantai Selatan', 300, 'Zona Pesisir Selatan TNBTS', 'Desa pesisir selatan'),
        (10, 'Bidara laut', 'Strychnos lucida', 'Pohon', 'Pereda nyeri', -8.017580, 112.989771, 'Zona Pesisir & Pantai Selatan', 250, 'Pantai Selatan – Batas TNBTS', 'Desa pesisir selatan'),
        (11, 'Buah klandingan', 'Lucas lavandulifolia', 'Pohon', 'Batuk & pilek', -7.923049, 112.931893, 'Tepi Hutan & Zona Transisi', 1900, 'Zona Transisi Hutan – Ladang', 'Ngadisari, Wonokitri'),
        (12, 'Bunga hariang', 'Begonia', 'Bunga', 'Batuk', -7.978359, 112.985046, 'Lereng Semeru & Dataran Tinggi', 2300, 'Lereng Semeru Barat Daya', 'Ranupani'),
        (13, 'Bunga Matahari', 'Helianthus annuus', 'Bunga', 'Penurun demam', -7.947289, 112.968221, 'Savana Bromo & Lereng Terbuka', 2050, 'Savana & Ladang Bromo', 'Ngadisari, Argosari'),
        (14, 'Calingan', 'Centella asiatica L.', 'Herba', 'Penyembuhan luka', -7.902902, 112.949682, 'Ranu Darungan & Sekitar Danau', 1860, 'Bantaran Ranu Darungan', 'Ranupani'),
        (15, 'Cemplukan', 'Physalis minima', 'Herba', 'Penurun demam', -7.942842, 112.969820, 'Savana Bromo & Lereng Terbuka', 2000, 'Tepi Savana Bromo', 'Ngadas, Argosari'),
        (16, 'Daun dadap', 'Erythrina variegata L.', 'Pohon', 'Pereda nyeri', -7.925810, 112.933169, 'Tepi Hutan & Zona Transisi', 1900, 'Batas Hutan Cemara & Ladang', 'Ngadisari'),
        (17, 'Dringu', 'Acorus calamus L.', 'Herba', 'Pencernaan', -7.906090, 112.951202, 'Ranu Darungan & Sekitar Danau', 1860, 'Tepi Ranu Darungan – Pinggir Air', 'Ranupani'),
        (18, 'Ganjan', 'Artemisia vulgaris', 'Herba', 'Obat luka', -7.898000, 112.918106, 'Blok Ireng-Ireng & Hutan Atas', 2400, 'Blok Ireng-Ireng – Hutan Primer', 'Ireng-Ireng'),
        (19, 'Ganyong', 'Canna indica L.', 'Herba', 'Pencernaan', -7.958573, 112.935322, 'Kantong Air & Lembah', 1750, 'Lembah Basah – Sumber Mata Air', 'Ngadas, Ranupani'),
        (20, 'Jahe', 'Zingiber Officinale Rocs', 'Herba', 'Pencernaan', -7.922294, 112.934395, 'Tepi Hutan & Zona Transisi', 1900, 'Kebun Campuran Tepi Hutan', 'Seluruh desa penyangga'),
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
# FUNGSI CHATBOT AI
# ─────────────────────────────────────────────────────────────────────────────
def extract_location(text):
    """Ekstrak nama desa atau kabupaten dari teks."""
    desa_list = ['Ngadisari', 'Wonokitri', 'Ngadas', 'Argosari', 'Ranupani', 
                 'Ireng-Ireng', 'Cemoro Lawang', 'Sariwani', 'Kertosari',
                 'Sukapura', 'Tosari', 'Pasuruan', 'Malang', 'Lumajang',
                 'Probolinggo', 'Senduro', 'Gucialit', 'Jabung', 'Wajak',
                 'Tutur', 'Puspo', 'Lumbang']
    kabupaten_list = ['Malang', 'Pasuruan', 'Lumajang', 'Probolinggo']
    
    location_found = None
    location_type = None
    
    for desa in desa_list:
        if desa.lower() in text.lower():
            location_found = desa
            location_type = 'desa'
            break
    
    if not location_found:
        for kab in kabupaten_list:
            if kab.lower() in text.lower():
                location_found = kab
                location_type = 'kabupaten'
                break
    
    return location_found, location_type


def extract_symptoms(text):
    """Ekstrak gejala penyakit dari teks."""
    symptom_keywords = {
        'demam': ['demam', 'panas', 'meriang'],
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


def find_herbal_by_location_and_symptoms(location, location_type, symptoms, df_tanaman, gdf_desa):
    """Mencari tanaman herbal berdasarkan lokasi dan gejala."""
    if location:
        if location_type == 'desa':
            filtered_df = df_tanaman[df_tanaman['desa'].str.contains(location, case=False, na=False)]
        else:
            if not gdf_desa.empty and 'nama_kabko' in gdf_desa.columns:
                desa_in_kab = gdf_desa[gdf_desa['nama_kabko'].str.contains(location, case=False, na=False)]
                desa_names = desa_in_kab['nama_kelur'].tolist() if 'nama_kelur' in desa_in_kab.columns else []
                if desa_names:
                    filtered_df = df_tanaman[df_tanaman['desa'].str.contains('|'.join(desa_names), case=False, na=False)]
                else:
                    filtered_df = df_tanaman
            else:
                filtered_df = df_tanaman
    else:
        filtered_df = df_tanaman
    
    if symptoms:
        symptom_matches = []
        for symptom in symptoms:
            symptom_matches.extend(
                filtered_df[filtered_df['fungsi_utama'].str.contains(symptom, case=False, na=False)].index.tolist()
            )
        if symptom_matches:
            filtered_df = filtered_df.loc[list(set(symptom_matches))]
    
    filtered_df = filtered_df.sort_values('ketinggian', ascending=True)
    return filtered_df


def generate_chatbot_response(user_input, df_tanaman, gdf_desa):
    """Generate response from chatbot based on user input."""
    user_input_lower = user_input.lower()
    
    greetings = ['halo', 'hai', 'hello', 'hi', 'selamat pagi', 'selamat siang', 'selamat sore', 'selamat malam']
    if any(greeting in user_input_lower for greeting in greetings):
        return "🌿 **Halo!** Saya adalah Asisten Tanaman Herbal TNBTS. Saya dapat membantu Anda menemukan tanaman herbal berdasarkan lokasi Anda (desa/kabupaten) dan gejala penyakit yang Anda alami. Coba tanyakan: 'Tanaman untuk demam di Ngadisari' atau 'Apa obat luka di Malang?'"
    
    if 'bantuan' in user_input_lower or 'help' in user_input_lower:
        return """
        🤖 **Cara Menggunakan Chatbot:**
        
        1. **Sebutkan lokasi Anda** (desa atau kabupaten)
        2. **Sebutkan gejala penyakit** yang Anda alami
        
        **Contoh pertanyaan:**
        - "Tanaman untuk demam di Ngadisari"
        - "Apa obat batuk di Malang?"
        - "Tanaman antiradang di Pasuruan"
        - "Saya sakit perut di Wonokitri"
        
        **Desa yang tersedia:** Ngadisari, Wonokitri, Ngadas, Argosari, Ranupani, Ireng-Ireng, Cemoro Lawang, Sariwani, Kertosari
        **Kabupaten:** Malang, Pasuruan, Lumajang, Probolinggo
        """
    
    location, location_type = extract_location(user_input)
    symptoms = extract_symptoms(user_input)
    
    if not location and not symptoms:
        return """
        🤔 **Saya belum memahami pertanyaan Anda.** 
        
        Untuk menggunakan chatbot ini, silakan sebutkan:
        - **Lokasi** (desa atau kabupaten di sekitar TNBTS)
        - **Gejala penyakit** yang Anda alami
        
        Contoh: "Tanaman untuk demam di Ngadisari"
        
        Ketik **'bantuan'** untuk melihat panduan lengkap.
        """
    
    results = find_herbal_by_location_and_symptoms(location, location_type, symptoms, df_tanaman, gdf_desa)
    
    if results.empty:
        response = "🌿 **Maaf, tidak ditemukan tanaman herbal** yang sesuai dengan kriteria Anda."
        if location:
            response += f"\n\n📍 Lokasi: **{location}** ({location_type})"
        if symptoms:
            response += f"\n\n💊 Gejala: **{', '.join(symptoms)}**"
        response += "\n\n💡 **Saran:** Coba gunakan kata kunci lain atau konsultasikan dengan ahli kesehatan setempat."
        return response
    
    response = "🌿 **Ditemukan tanaman herbal yang dapat membantu!**\n\n"
    if location:
        response += f"📍 **Lokasi:** {location} ({location_type})\n"
    if symptoms:
        response += f"💊 **Gejala:** {', '.join(symptoms)}\n"
    response += f"🌱 **Jumlah tanaman ditemukan:** {len(results)}\n\n"
    
    response += "**Rekomendasi Tanaman:**\n"
    for i, (_, row) in enumerate(results.head(5).iterrows()):
        response += f"\n{i+1}. **{row['nama_tanaman']}** ({row['nama_latin']})\n"
        response += f"   - Jenis: {row['jenis']}\n"
        response += f"   - Fungsi: {row['fungsi_utama']}\n"
        response += f"   - Lokasi: {row['desa']} - {row['kawasan']}\n"
        response += f"   - Ketinggian: {row['ketinggian']} mdpl\n"
        if row['status_konservasi'] == 'Dilindungi':
            response += "   - ⚠️ **Status: Dilindungi** - Jangan dikonsumsi tanpa izin\n"
    
    if len(results) > 5:
        response += f"\n📋 **{len(results)-5} tanaman lainnya** dapat dilihat di Data Tanaman."
    
    response += "\n\n💡 **Catatan:** Selalu konsultasikan dengan ahli kesehatan sebelum mengonsumsi tanaman herbal."
    return response


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
    .chat-message.bot h4 { color: #2E7D32; margin-top: 0; }
    .chat-message.bot ul { margin: 4px 0; padding-left: 20px; }
    .chat-message.bot li { margin-bottom: 4px; }
    
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
            
            is_highlighted = nama_tanaman in highlight_set
            
            if is_highlighted:
                icon_color = 'red'
                icon_icon = 'star'
            elif status == 'Dilindungi':
                icon_color = 'orange'
                icon_icon = 'lock'
            else:
                icon_color = JENIS_COLOR.get(jenis, 'green')
                icon_icon = 'leaf'
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px; line-height: 1.5;">
                <h5 style="margin: 0 0 5px 0; color: #27AE60; border-bottom: 2px solid #2ECC71; padding-bottom: 3px; font-weight: bold;">
                    {'⭐ ' if is_highlighted else '🌿 '}{nama_tanaman}
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
                tooltip=f"{'⭐ ' if is_highlighted else ''}{nama_tanaman} ({jenis}) - {kawasan}",
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
    st.markdown("""
    <div class="info-box">
        <h4>💬 Tanyakan Tanaman Herbal Berdasarkan Lokasi & Gejala</h4>
        <p>
            Chatbot ini akan membantu Anda menemukan tanaman herbal di sekitar TNBTS 
            berdasarkan <b>lokasi</b> (desa/kabupaten) dan <b>gejala penyakit</b> yang Anda alami.
        </p>
        <p><b>Contoh pertanyaan:</b><br>
        - "Tanaman untuk demam di Ngadisari"<br>
        - "Apa obat batuk di Malang?"<br>
        - "Tanaman antiradang di Pasuruan"<br>
        - "Saya sakit perut di Wonokitri"
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
            placeholder="Contoh: Tanaman untuk demam di Ngadisari",
            key="chat_input",
            label_visibility="collapsed"
        )
    with col_button:
        send_button = st.button("📤 Kirim", use_container_width=True)
    
    if send_button and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        response = generate_chatbot_response(user_input, df_tanaman, gdf_desa)
        
        highlighted = []
        if "**Rekomendasi Tanaman:**" in response:
            lines = response.split('\n')
            for line in lines:
                if '**' in line and 'nama_tanaman' in line:
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
                df_tanaman_filtered=df_tanaman,
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
    st.markdown(
        "Visualisasi sebaran **86 spesies tanaman herbal** di **8 kawasan ekologi** TNBTS."
    )

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
            highlight_points=None
        )
        folium_static(m, width=1200, height=640)
    except Exception as e:
        st.error(f"Error membuat peta: {e}")

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

    with tab2:
        st.markdown("### 📊 Data Desa dari File GeoJSON")
        if not gdf_desa.empty:
            st.success(f"✅ {len(gdf_desa)} desa berhasil dimuat")
            desa_df = gdf_desa.drop('geometry', axis=1, errors='ignore')
            st.dataframe(desa_df, use_container_width=True, height=500)
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
    with c2:
        st.markdown("### 💊 Top 10 Fungsi Tanaman")
        fungsi_counts = df_tanaman_filtered['fungsi_utama'].value_counts().head(10)
        st.bar_chart(fungsi_counts, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# MENU: INFORMASI
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## ℹ️ Informasi TNBTS")
    st.markdown("""
    <div class="info-box">
        <h4>🌋 Taman Nasional Bromo Tengger Semeru</h4>
        <p>TNBTS adalah kawasan konservasi di Jawa Timur dengan keanekaragaman hayati tinggi.
        WebGIS ini menampilkan <b>86 spesies tanaman herbal</b> yang teridentifikasi
        di <b>8 kawasan ekologi</b> berbeda.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    st.markdown("### 🏔️ 8 Kawasan Ekologi TNBTS")
    kw_cols_ui = st.columns(2)
    for i, (kw, col_h) in enumerate(KAWASAN_HEX.items()):
        cnt = len(df_tanaman[df_tanaman['kawasan'] == kw])
        with kw_cols_ui[i % 2]:
            st.markdown(
                f'<div style="border-left:5px solid {col_h};padding:.6rem 1rem;'
                f'margin-bottom:.6rem;background:#fafafa;border-radius:0 8px 8px 0;">'
                f'<b style="color:{col_h};">{kw}</b><br>'
                f'<small>🌿 {cnt} spesies</small></div>',
                unsafe_allow_html=True
            )

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
