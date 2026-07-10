import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import json
import os
from folium.plugins import MarkerCluster
import re
from datetime import datetime
import warnings
import base64
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURASI HALAMAN STREAMLIT
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
# CSS UNTUK MEMPERBAIKI TAMPILAN LAYER CONTROL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Perbaiki z-index untuk layer control */
    .folium-map {
        position: relative !important;
        z-index: 1 !important;
    }
    
    /* Pastikan layer control terlihat penuh */
    .leaflet-control-container .leaflet-top.leaflet-right {
        z-index: 1000 !important;
        position: relative !important;
    }
    
    .leaflet-control-container .leaflet-top.leaflet-right .leaflet-control {
        margin-right: 10px !important;
        margin-top: 10px !important;
    }
    
    /* Perbaiki ukuran container peta */
    .stFoliumContainer {
        position: relative !important;
        overflow: visible !important;
    }
    
    /* Pastikan iframe peta tidak terpotong */
    .stFoliumContainer iframe {
        width: 100% !important;
        height: 100% !important;
        min-height: 500px !important;
    }
    
    /* Perbaiki tampilan legend di sidebar */
    .leaflet-control-layers {
        background: white !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
        padding: 8px 12px !important;
        min-width: 180px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
    }
    
    .leaflet-control-layers label {
        font-size: 13px !important;
        padding: 2px 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 6px !important;
    }
    
    .leaflet-control-layers label input[type="checkbox"] {
        margin-right: 6px !important;
        width: 16px !important;
        height: 16px !important;
    }
    
    .leaflet-control-layers-base,
    .leaflet-control-layers-overlays {
        padding: 4px 0 !important;
    }
    
    .leaflet-control-layers-separator {
        border-top: 1px solid #ddd !important;
        margin: 6px 0 !important;
    }
    
    /* Perbaiki posisi layer control di mobile */
    @media (max-width: 768px) {
        .leaflet-control-container .leaflet-top.leaflet-right {
            top: 10px !important;
            right: 10px !important;
        }
        
        .leaflet-control-layers {
            min-width: 140px !important;
            font-size: 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA TANAMAN HERBAL LENGKAP (LANJUTAN DARI SEBELUMNYA)
# ─────────────────────────────────────────────────────────────────────────────
HERBAL_DETAIL_DATA = {
    "AJERAN PUTIH": {
        "nama_latin": "Bindens pilosa L.",
        "fungsi": "Obat luka dan menghentikan pendarahan, anti radang, anti bakteri dan antiseptik, mengatasi diare, menurunkan demam, mengatasi batuk-flu, rematik, pegal linu, menurunkan gula darah.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 15°C hingga 45°C. Ketinggian: tumbuh baik diketinggian 3600 mdpl. Penyiraman: curah hujan 500mm/th-3.600mm/th sangat tahan terhadap kekeringan. Tumbuh ideal pada tanah dengan pH 5,0 - 6,5",
        "cara_memanfaatkan": "Daun atau batang direbus, air rebusan diminum untuk mengatasi demam dan pencernaan, mata merah dan radang usus bunti. Daun dan bunga ajeran ditumbuk atau diblender hingga halus dan ditambahkan sedikit air hangat, pasta daun digunakan mengatasi kulit yang memar, luka ringan, atau bengkak.",
        "yang_dimanfaatkan": "Batang dan daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image1.png"
    },
    "ADAS": {
        "nama_latin": "Foeniculum vulgare",
        "fungsi": "Mengatasi masalah pencernaan (maag, kembung), batuk, kesehatan jantung, serta meringankan gejala menopause",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 15°C-20°C. Ketinggian: dataran tinggi 1.600-2.400 mdpl. Curah hujan 2.500 mm/th, membutuhkan cuaca sejuk dan cerah agar produksinya maksimal. Tumbuh ideal pada tanah dengan pH 5,3-7,8",
        "cara_memanfaatkan": "Biji adas direbus dengan air bersih selama 5-10 menit kemudian disaring airnya, dapat mengatasi perut kembung, mual, dan melancarkan pencernaan. Daun dan biji adas direbus untuk diambil kandungan minyak atsiri yang memiliki sifat ekspektoran yang dapat membantu mencernakan dahak, meredakan batuk dan pilek.",
        "yang_dimanfaatkan": "Daun, batang, dan biji",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Gubuklakah dan Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari Kab. Pasuruan).",
        "foto": "media/image2.jpeg"
    },
    "ALANG-ALANG": {
        "nama_latin": "Imperata cylindrical L.",
        "fungsi": "Batu ginjal, infeksi ginjal, hepatitis, kencing batu, buang air kecil tidak lancar, keputihan.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 20°C-40°C. Ketinggian: dataran rendah sampai di ketinggian 2.000 mdpl. Curah hujan 500-3.500 mm/th. Tumbuh ideal pada tanah dengan pH 4-7.5",
        "cara_memanfaatkan": "Akar alang-alang direbus, air rebusan digunakan meredakan panas, melancarkan urine dan mengatasi batu ginjal.",
        "yang_dimanfaatkan": "Akar",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image3.jpeg"
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA TANAMAN HERBAL (EMBEDDED - FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────
HERBAL_DATA_EMBEDDED = [
    (1, 'AJERAN PUTIH', 112.902096, -7.876545),
    (2, 'ADAS', 112.864227, -8.009353),
    (3, 'ADAS', 112.864227, -8.009353),
    (4, 'ALANG-ALANG', 112.950828, -7.930880),
    (5, 'ALANG-ALANG', 112.950828, -7.930880),
]

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNGSI GEOSPATIAL
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
        os.path.join(script_dir, '..', filename),
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
        os.path.join(script_dir, '..', filename),
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

# ── Data Desa kawasan TNBTS ────────────────────────────────────────────────
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
                return gpd.GeoDataFrame()
        return gdf
    return gpd.GeoDataFrame()

@st.cache_data
def load_herbal_geojson():
    """Membaca data sebaran tanaman herbal dari GeoJSON."""
    gdf = _load_geojson('sebaran_tanaman_herbal_TNBTS.geojson')
    if gdf.empty:
        return pd.DataFrame()

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        try:
            gdf = gdf.to_crs("EPSG:4326")
        except Exception as e:
            return pd.DataFrame()

    def _clean_str(v):
        if v is None:
            return ''
        if isinstance(v, float) and pd.isna(v):
            return ''
        return str(v).strip()

    records = []
    for i, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        lon, lat = geom.x, geom.y
        
        # Coba berbagai kemungkinan nama kolom
        nama = _clean_str(row.get('nama_tanaman', ''))
        if not nama:
            nama = _clean_str(row.get('nama', ''))
        if not nama:
            nama = _clean_str(row.get('NAMA', ''))
        if not nama or nama == 'NONE':
            continue
        
        nama = nama.upper()
        
        # Coba berbagai kemungkinan nama kolom untuk detail
        nama_latin = _clean_str(row.get('nama_ilmiah', ''))
        if not nama_latin:
            nama_latin = _clean_str(row.get('nama_latin', ''))
        
        fungsi = _clean_str(row.get('fungsi_manfaat', ''))
        if not fungsi:
            fungsi = _clean_str(row.get('fungsi', ''))
        
        potensi = _clean_str(row.get('potensi_sebaran', ''))
        if not potensi:
            potensi = _clean_str(row.get('potensi', ''))
        
        syarat = _clean_str(row.get('syarat_hidup', ''))
        cara = _clean_str(row.get('cara_memanfaatkan', ''))
        bagian = _clean_str(row.get('bagian_dimanfaatkan', ''))
        
        records.append({
            'No': i + 1,
            'Nama': nama,
            'X': lon,
            'Y': lat,
            'NamaLatin': nama_latin,
            'Fungsi': fungsi,
            'PotensiSebaran': potensi,
            'SyaratHidup': syarat,
            'CaraMemanfaatkan': cara,
            'BagianDimanfaatkan': bagian,
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    st.sidebar.success(
        f"✅ Memuat {len(df)} titik / {df['Nama'].nunique()} spesies dari "
        f"sebaran_tanaman_herbal_TNBTS.geojson"
    )
    return df

@st.cache_data
def load_herbal_data():
    """Membaca data sebaran tanaman herbal."""
    df_geojson = load_herbal_geojson()
    if not df_geojson.empty:
        return df_geojson

    # Coba baca dari file Excel
    filenames = ['Titik Rapihin.xlsx', 'Titik Rapihin.xls', 'Titik Rapihin.csv']
    
    for filename in filenames:
        filepath = _find_file(filename)
        if filepath:
            try:
                if filename.endswith('.xlsx') or filename.endswith('.xls'):
                    df = pd.read_excel(filepath, engine='openpyxl')
                else:
                    df = pd.read_csv(filepath)
                
                df.columns = df.columns.str.strip()
                
                x_col, y_col, name_col = None, None, None
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in ['x', 'lon', 'longitude', 'long']:
                        x_col = col
                    elif col_lower in ['y', 'lat', 'latitude']:
                        y_col = col
                    elif col_lower in ['nama', 'name', 'jenis', 'spesies', 'tanaman']:
                        name_col = col
                
                if x_col is None and len(df.columns) >= 3:
                    if 'no' in str(df.columns[0]).lower() and 'nama' in str(df.columns[1]).lower():
                        name_col = df.columns[1]
                        x_col = df.columns[2]
                        y_col = df.columns[3]
                    else:
                        name_col = df.columns[1]
                        x_col = df.columns[2]
                        y_col = df.columns[3]
                
                if x_col and y_col and name_col:
                    df[x_col] = pd.to_numeric(df[x_col], errors='coerce')
                    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
                    df = df.dropna(subset=[x_col, y_col])
                    
                    result_df = pd.DataFrame({
                        'No': df.index + 1,
                        'Nama': df[name_col].astype(str),
                        'X': df[x_col],
                        'Y': df[y_col]
                    })
                    
                    st.sidebar.success(f"✅ Memuat {len(result_df)} data dari {filename}")
                    return result_df
            except Exception as e:
                continue
    
    st.sidebar.info(f"📊 Menggunakan data tanaman herbal embedded ({len(HERBAL_DATA_EMBEDDED)} titik)")
    df = pd.DataFrame(HERBAL_DATA_EMBEDDED, columns=['No', 'Nama', 'X', 'Y'])
    return df

def get_plant_detail(plant_name, row=None):
    """Mendapatkan detail tanaman berdasarkan nama."""
    plant_name_clean = plant_name.upper().strip()

    if row is None and 'df_herbal' in globals() and not df_herbal.empty and 'NamaLatin' in df_herbal.columns:
        match = df_herbal[df_herbal['Nama'] == plant_name_clean]
        if not match.empty:
            row = match.iloc[0]

    detail_from_row = None
    if row is not None:
        candidate = {
            'nama_latin': row.get('NamaLatin', ''),
            'fungsi': row.get('Fungsi', ''),
            'syarat_hidup': row.get('SyaratHidup', ''),
            'cara_memanfaatkan': row.get('CaraMemanfaatkan', ''),
            'yang_dimanfaatkan': row.get('BagianDimanfaatkan', ''),
            'potensi_sebaran': row.get('PotensiSebaran', ''),
        }
        candidate = {k: v for k, v in candidate.items() if v}
        if candidate:
            detail_from_row = candidate

    # Detail dari dictionary embedded
    detail_embedded = None
    for key in HERBAL_DETAIL_DATA:
        if key == plant_name_clean or plant_name_clean in key or key in plant_name_clean:
            detail_embedded = HERBAL_DETAIL_DATA[key]
            break

    if detail_from_row and detail_embedded:
        merged = dict(detail_from_row)
        if detail_embedded.get('foto'):
            merged['foto'] = detail_embedded['foto']
        return merged

    return detail_from_row or detail_embedded

def create_plant_popup_html(plant_name, lat, lon, no, is_highlighted=False, row=None):
    """Membuat HTML popup untuk peta dengan detail lengkap tanaman."""
    detail = get_plant_detail(plant_name, row=row)
    
    border_color = '#D32F2F' if is_highlighted else '#2E7D32'
    header_gradient = 'linear-gradient(135deg, #D32F2F, #E53935)' if is_highlighted else 'linear-gradient(135deg, #2E7D32, #43A047)'
    star_icon = '⭐ ' if is_highlighted else '🌿 '
    
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; 
                max-width: 380px; line-height: 1.6; background: #FAFAFA; 
                border-radius: 10px; padding: 0; overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                border: 2px solid {border_color};">
        
        <div style="background: {header_gradient}; 
                    color: white; padding: 12px 16px; border-radius: 10px 10px 0 0;">
            <h4 style="margin: 0; font-size: 16px; font-weight: bold; display: flex; align-items: center; gap: 8px;">
                <span>{star_icon}</span> {plant_name}
                {f'<span style="background: #FFD700; color: #333; font-size: 10px; padding: 2px 8px; border-radius: 12px; margin-left: auto;">⭐ REKOMENDASI</span>' if is_highlighted else ''}
            </h4>
        </div>
        
        <div style="padding: 12px 16px;">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
                <tr style="border-bottom: 1px solid #E0E0E0;">
                    <td style="padding: 4px 0; font-weight: bold; color: #555; width: 35%;">No. Urut:</td>
                    <td style="padding: 4px 0; text-align: right;">{no}</td>
                </tr>
                <tr style="border-bottom: 1px solid #E0E0E0;">
                    <td style="padding: 4px 0; font-weight: bold; color: #555;">Koordinat:</td>
                    <td style="padding: 4px 0; text-align: right; font-family: monospace;">{lat:.6f}, {lon:.6f}</td>
                </tr>
    """
    
    if detail:
        if detail.get('nama_latin'):
            html += f"""
                <tr style="border-bottom: 1px solid #E0E0E0;">
                    <td style="padding: 4px 0; font-weight: bold; color: #555;">Nama Latin:</td>
                    <td style="padding: 4px 0; text-align: right; font-style: italic;">{detail['nama_latin']}</td>
                </tr>
            """
        
        html += f"""
                <tr>
                    <td style="padding: 4px 0; font-weight: bold; color: #555; vertical-align: top;">Fungsi:</td>
                    <td style="padding: 4px 0; text-align: left; font-size: 12px;">{detail.get('fungsi', '-')[:200]}{'...' if len(detail.get('fungsi', '')) > 200 else ''}</td>
                </tr>
            """
        html += """
            </table>
            
            <div style="margin-top: 8px; border-top: 2px solid #E8F5E9; padding-top: 8px;">
                <details style="cursor: pointer;">
                    <summary style="font-weight: bold; color: #2E7D32; font-size: 13px;">
                        📋 Detail Lengkap
                    </summary>
                    <div style="margin-top: 6px; font-size: 12px;">
        """
        
        if detail.get('syarat_hidup'):
            html += f"""
                        <div style="margin-bottom: 4px;">
                            <span style="font-weight: bold;">🌱 Syarat Hidup:</span><br>
                            <span style="color: #444;">{detail['syarat_hidup'][:300]}{'...' if len(detail['syarat_hidup']) > 300 else ''}</span>
                        </div>
            """
        
        if detail.get('cara_memanfaatkan'):
            html += f"""
                        <div style="margin-bottom: 4px;">
                            <span style="font-weight: bold;">🔬 Cara Memanfaatkan:</span><br>
                            <span style="color: #444;">{detail['cara_memanfaatkan'][:300]}{'...' if len(detail['cara_memanfaatkan']) > 300 else ''}</span>
                        </div>
            """
        
        if detail.get('yang_dimanfaatkan'):
            html += f"""
                        <div style="margin-bottom: 4px;">
                            <span style="font-weight: bold;">✂️ Yang Dimanfaatkan:</span>
                            <span style="color: #444;">{detail['yang_dimanfaatkan']}</span>
                        </div>
            """
        
        if detail.get('potensi_sebaran'):
            html += f"""
                        <div style="margin-bottom: 4px;">
                            <span style="font-weight: bold;">📍 Potensi Sebaran:</span><br>
                            <span style="color: #444; font-size: 11px;">{detail['potensi_sebaran']}</span>
                        </div>
            """
        
        if detail.get('foto'):
            html += f"""
                        <div style="margin-top: 6px;">
                            <span style="font-weight: bold;">📷 Foto:</span><br>
                            <span style="color: #888; font-size: 11px;">{detail['foto']}</span>
                        </div>
            """
        
        html += """
                    </div>
                </details>
            </div>
        """
    else:
        html += """
            </table>
            <div style="margin-top: 8px; border-top: 2px solid #FFCDD2; padding-top: 8px; color: #C62828; font-size: 12px;">
                ⚠️ Data detail tanaman tidak tersedia
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html

# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI UNTUK MEMBUAT LINK GeoJSON Viewer
# ─────────────────────────────────────────────────────────────────────────────
def create_geojson_viewer_link(geojson_file):
    """
    Membuat link untuk membuka GeoJSON di geojson.io
    """
    import urllib.parse
    
    # Baca file GeoJSON
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    # Konversi ke string JSON
    json_str = json.dumps(geojson_data)
    
    # Encode untuk URL
    encoded_json = urllib.parse.quote(json_str)
    
    # Buat URL geojson.io dengan parameter
    url = f"https://geojson.io/#data=data:application/json,{encoded_json}"
    
    return url

# ─────────────────────────────────────────────────────────────────────────────
# CSS UTAMA
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
    
    .status-badge {
        background: rgba(0,0,0,0.4);
        padding: 10px 14px;
        border-radius: 8px;
        color: white;
        border-left: 3px solid #4CAF50;
    }
    .status-badge small {
        color: rgba(255,255,255,0.7);
    }
    
    .highlight-badge {
        background: #D32F2F;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-left: 8px;
    }

    /* Perbaiki container peta agar layer control terlihat penuh */
    .stFoliumContainer {
        position: relative;
        z-index: 1;
    }
    
    .stFoliumContainer iframe {
        width: 100% !important;
        min-height: 600px !important;
    }
    
    /* Layer control di pojok kanan atas */
    .leaflet-control-container .leaflet-top.leaflet-right {
        z-index: 9999 !important;
    }
    
    .leaflet-control-layers {
        background: white !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2) !important;
        padding: 10px 14px !important;
        max-height: 70vh !important;
        overflow-y: auto !important;
        min-width: 200px !important;
    }
    
    .leaflet-control-layers label {
        font-size: 13px !important;
        padding: 3px 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    
    .leaflet-control-layers input[type="checkbox"],
    .leaflet-control-layers input[type="radio"] {
        margin-right: 8px !important;
        width: 16px !important;
        height: 16px !important;
        flex-shrink: 0 !important;
    }
    
    .leaflet-control-layers-selector {
        margin-right: 8px !important;
    }
    
    /* Responsif untuk mobile */
    @media (max-width: 768px) {
        .leaflet-control-layers {
            min-width: 150px !important;
            font-size: 12px !important;
            padding: 6px 10px !important;
        }
    }
    
    /* Styling untuk GeoJSON Viewer section */
    .geojson-viewer-box {
        background: #f0f8ff;
        border: 2px solid #2196F3;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.15);
    }
    
    .geojson-viewer-box h3 {
        color: #0D47A1;
        margin-top: 0;
    }
    
    .geojson-viewer-box .btn-primary {
        background: #2196F3;
        color: white;
        padding: 12px 30px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(33, 150, 243, 0.3);
    }
    
    .geojson-viewer-box .btn-primary:hover {
        background: #1976D2;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.4);
    }
    
    .geojson-stats {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
        margin: 10px 0;
    }
    
    .geojson-stats .stat-item {
        background: white;
        padding: 8px 16px;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
        font-size: 14px;
    }
    
    .geojson-stats .stat-item strong {
        color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MUSIK (Floating Player)
# ─────────────────────────────────────────────────────────────────────────────
video_id = "NVY60XJuGKs"
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
df_herbal = load_herbal_data()

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
        '<p style="color:white!important; text-align:center; font-size:12px; opacity:0.8;">Tim Ekspedisi Penelitian</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.markdown("### 📋 Menu Navigasi")
    menu_options = ["Peta Sebaran", "WebGIS Analytics Potensi Tanaman Herbal", "Tanya Mbah Dukun Herbal Digital", "Peta 3D Pegunungan", "Data Tanaman", "Statistik", "Informasi"]
    menu_icons   = ["🗺️", "🌐", "🤖", "🏔️", "📋", "📊", "ℹ️"]
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed",
        key="menu_radio"
    )
    st.markdown("---")

    # Filter data
    st.markdown("### 🔍 Filter Data")
    semua_tanaman = sorted(df_herbal['Nama'].unique())
    selected_tanaman = st.multiselect(
        "Pilih Nama Tanaman",
        options=["Semua"] + semua_tanaman,
        default=["Semua"],
        help="Pilih satu atau lebih tanaman"
    )

    st.markdown("---")
    st.markdown("### 🗂️ Layer Control")
    c1, c2 = st.columns(2)
    with c1:
        show_desa_geojson  = st.checkbox("🏘️ Batas Desa",         value=True)
    with c2:
        show_tanaman       = st.checkbox("🌿 Tanaman",             value=True)
        show_kabupaten     = st.checkbox("🗺️ Batas Kabupaten",     value=True)
    show_batas_tnbts   = st.checkbox("🔲 Batas TNBTS",         value=True)

    st.markdown("### 🏔️ Kontrol Tampilan 3D")
    map_height_3d = st.slider("Tinggi Iframe", 400, 800, 600, step=50)

    st.markdown("---")
    st.markdown("### 📁 Status Data")
    st.markdown(f"""
    <div class="status-badge">
        ✅ <b>Data Tanaman</b><br>
        <small>{len(df_herbal)} titik • {df_herbal['Nama'].nunique()} spesies</small>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FILTER DATA
# ─────────────────────────────────────────────────────────────────────────────
if "Semua" not in selected_tanaman and selected_tanaman:
    df_herbal_filtered = df_herbal[df_herbal['Nama'].isin(selected_tanaman)]
else:
    df_herbal_filtered = df_herbal.copy()

# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI CHATBOT AI (SINGKAT)
# ─────────────────────────────────────────────────────────────────────────────
def extract_symptoms_from_text(text):
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
    symptom_plant_map = {
        'demam': ['AJERAN PUTIH', 'PAITAN', 'PECUT KUDA', 'GANJAN', 'CIPLUKAN'],
        'batuk': ['ADAS', 'SURI PANDAK', 'SIMBARAN', 'TEKLAN', 'JENGGOT WESI'],
        'nyeri': ['DAUN OTOT', 'TEPUNG OTOT', 'AWAR-AWAR', 'SURI PANDAK'],
        'luka': ['CALINGAN', 'GANJAN', 'BAKUNG', 'SIMBARAN', 'ANDONG'],
        'pencernaan': ['ADAS', 'ALANG-ALANG', 'AWAR-AWAR', 'GANYONG', 'SAWI IRENG', 'CIPLUKAN'],
        'darah': ['KENCANA UNGU', 'STROBERI TENGGER', 'BIT MERAH', 'BUAH DELIMA'],
        'antiradang': ['AJERAN PUTIH', 'AWAR-AWAR', 'TEPUNG OTOT', 'DAUN KANCING'],
        'diuretik': ['ALANG-ALANG', 'KETIUW', 'TEKLAN'],
        'antiseptik': ['SIRIH', 'PUTIHAN', 'PAKU RANE'],
        'antioksidan': ['BUAH DELIMA', 'STROBERI TENGGER', 'TERONG BELANDA', 'PEPAYA GUNUNG']
    }
    
    matched_plants = set()
    for symptom in symptoms:
        if symptom in symptom_plant_map:
            matched_plants.update(symptom_plant_map[symptom])
    
    if matched_plants:
        return df_herbal[df_herbal['Nama'].isin(matched_plants)]
    
    results = []
    for plant in df_herbal['Nama'].unique():
        plant_lower = plant.lower()
        for symptom in symptoms:
            if symptom in plant_lower:
                results.append(plant)
                break
    
    if results:
        return df_herbal[df_herbal['Nama'].isin(results)]
    
    return df_herbal.head(0)

def generate_chatbot_response_herbal(user_input, df_herbal):
    user_input_lower = user_input.lower()
    
    greetings = ['halo', 'hai', 'hello', 'hi', 'selamat pagi', 'selamat siang', 'selamat sore', 'selamat malam']
    if any(greeting in user_input_lower for greeting in greetings):
        return "🌿 **Halo!** Saya adalah Mbah Dukun Herbal Digital TNBTS. Saya dapat membantu Anda menemukan tanaman herbal berdasarkan gejala penyakit yang Anda alami. Coba tanyakan: 'Tanaman untuk demam' atau 'Apa obat batuk?'"
    
    if 'bantuan' in user_input_lower or 'help' in user_input_lower:
        return """
        🤖 **Cara Menggunakan Tanya Mbah Dukun Herbal Digital:**
        
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
        
        Untuk menggunakan tanya mbah dukun herbal ini, silakan sebutkan:
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
    
    recommended_plants = []
    
    response += "**Rekomendasi Tanaman:**\n"
    for i, (_, row) in enumerate(results.head(5).iterrows()):
        plant_name = row['Nama']
        recommended_plants.append(plant_name)
        
        response += f"\n{i+1}. **{plant_name}**\n"
        response += f"   - Koordinat: {row['Y']:.6f}, {row['X']:.6f}\n"
        
        detail = get_plant_detail(plant_name)
        if detail:
            if detail.get('fungsi'):
                response += f"   - Fungsi: {detail['fungsi'][:100]}...\n"
            if detail.get('cara_memanfaatkan'):
                response += f"   - Cara: {detail['cara_memanfaatkan'][:100]}...\n"
    
    if len(results) > 5:
        response += f"\n📋 **{len(results)-5} tanaman lainnya** dapat dilihat di Data Tanaman."
    
    response += "\n\n💡 **Catatan:** Selalu konsultasikan dengan ahli kesehatan sebelum mengonsumsi tanaman herbal."
    
    st.session_state.recommended_plants = recommended_plants
    
    return response

# ─────────────────────────────────────────────────────────────────────────────
# FUNGSI BUAT PETA
# ─────────────────────────────────────────────────────────────────────────────
def create_tnbts_map(
    show_desa_geojson, show_kabupaten, show_batas_tnbts, show_tanaman,
    gdf_desa, gdf_kabupaten, gdf_batas, df_tanaman_filtered, 
    highlight_points=None, show_only_highlighted=False
):
    """
    Membuat peta interaktif TNBTS dengan Layer Control yang terlihat penuh.
    """
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
        if show_only_highlighted and highlight_points:
            df_to_show = df_tanaman_filtered[df_tanaman_filtered['Nama'].isin(highlight_points)]
            cluster_name = "⭐ Tanaman yang Direkomendasikan"
        else:
            df_to_show = df_tanaman_filtered
            cluster_name = "🌿 Sebaran Tanaman Herbal"
        
        if not df_to_show.empty:
            herbal_cluster = MarkerCluster(
                name=cluster_name,
                overlay=True,
                control=True,
                show=True
            )
            
            highlight_set = set(highlight_points) if highlight_points else set()
            
            for idx, row in df_to_show.iterrows():
                lat = row['Y']
                lon = row['X']
                nama = row['Nama']
                no = row['No']
                
                is_highlighted = nama in highlight_set
                
                if is_highlighted:
                    icon_color = 'red'
                    icon_icon = 'star'
                else:
                    icon_color = 'green'
                    icon_icon = 'leaf'
                
                popup_html = create_plant_popup_html(nama, lat, lon, no, is_highlighted, row=row)
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=f"{'⭐ ' if is_highlighted else ''}{nama}",
                    icon=folium.Icon(color=icon_color, icon=icon_icon, prefix='fa')
                ).add_to(herbal_cluster)
                
            herbal_cluster.add_to(m)

    folium.LayerControl(collapsed=False, position='topright').add_to(m)
    return m

# ─────────────────────────────────────────────────────────────────────────────
# MENU: WEBGIS SDM POTENSI HERBAL (LINK EKSTERNAL)
# ─────────────────────────────────────────────────────────────────────────────
if selected == "WebGIS Analytics Potensi Tanaman Herbal":
    st.markdown("## 🌐 WebGIS Analytics — Potensi Tumbuh Tanaman Herbal TNBTS")
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0f5132,#146c43);
                    padding:28px; border-radius:16px; text-align:center;
                    box-shadow:0 4px 14px rgba(0,0,0,0.25); margin-bottom:20px;">
            <h3 style="color:#FFD700; margin:0 0 10px 0;">🌿 Species Distribution Modelling (SDM)</h3>
            <p style="color:#FFFFFF; font-size:15px; margin:0 0 18px 0;">
                Jelajahi peta prediksi kesesuaian tumbuh tiap jenis tanaman herbal di
                kawasan TNBTS berdasarkan 8 layer lingkungan (ketinggian, curah hujan,
                suhu permukaan, kelerengan, kelembapan, NDVI, jarak pemukiman, dan
                jenis tanah) pada aplikasi WebGIS Analytics terpisah.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "🚀 Buka WebGIS Analytics Potensi Tanaman Herbal",
        "https://potensi-herbal-tnbts.streamlit.app/",
        width='stretch',
        type="primary",
    )

# ─────────────────────────────────────────────────────────────────────────────
# MENU: CHATBOT HERBAL
# ─────────────────────────────────────────────────────────────────────────────
elif selected == "Tanya Mbah Dukun Herbal Digital":
    st.markdown("## 🤖 Mbah Dukun Herbal Digital TNBTS")
    
    if 'recommended_plants' not in st.session_state:
        st.session_state.recommended_plants = []
    
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
        send_button = st.button("📤 Kirim", width='stretch')
    
    if send_button and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        response = generate_chatbot_response_herbal(user_input, df_herbal)
        st.session_state.chat_history.append({'role': 'bot', 'content': response})
        st.rerun()
    
    if st.button("🗑️ Hapus Riwayat Chat"):
        st.session_state.chat_history = []
        st.session_state.recommended_plants = []
        st.rerun()
    
    if st.session_state.recommended_plants:
        st.markdown("---")
        st.markdown("### 🗺️ Peta Sebaran Tanaman yang Direkomendasikan")
        st.markdown("""
        <div style="background: #FFF3E0; border-left: 4px solid #D32F2F; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">
            <span style="font-weight: bold; color: #D32F2F;">⭐ Titik berwarna MERAH dengan BINTANG</span>
            <span style="color: #555;"> adalah tanaman yang direkomendasikan berdasarkan pertanyaan Anda.</span>
            <br>
            <span style="color: #888; font-size: 13px;">
                Hanya menampilkan <b>{len(st.session_state.recommended_plants)}</b> jenis tanaman yang direkomendasikan.
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        df_recommended = df_herbal[df_herbal['Nama'].isin(st.session_state.recommended_plants)]
        
        if not df_recommended.empty:
            try:
                m = create_tnbts_map(
                    show_desa_geojson=show_desa_geojson,
                    show_kabupaten=show_kabupaten,
                    show_batas_tnbts=show_batas_tnbts,
                    show_tanaman=show_tanaman,
                    gdf_desa=gdf_desa,
                    gdf_kabupaten=gdf_kabupaten,
                    gdf_batas=gdf_batas,
                    df_tanaman_filtered=df_recommended,
                    highlight_points=st.session_state.recommended_plants,
                    show_only_highlighted=True
                )
                st_folium(m, width=1200, height=500, returned_objects=[])
                
                with st.expander("📋 Daftar Tanaman yang Direkomendasikan"):
                    for plant in st.session_state.recommended_plants:
                        detail = get_plant_detail(plant)
                        plant_data = df_recommended[df_recommended['Nama'] == plant]
                        st.markdown(f"""
                        <div style="background: #f8f9fa; border-radius: 8px; padding: 12px 16px; 
                                    margin: 6px 0; border-left: 4px solid #D32F2F;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-weight: bold; font-size: 15px; color: #1B5E20;">⭐ {plant}</span>
                                    <span style="font-size: 12px; color: #666; margin-left: 8px;">
                                        ({len(plant_data)} titik sebaran)
                                    </span>
                                </div>
                                <span style="font-size: 11px; color: #D32F2F; background: #FFEBEE; padding: 2px 10px; border-radius: 12px;">
                                    REKOMENDASI
                                </span>
                            </div>
                            {f'<div style="font-size: 13px; color: #555; margin-top: 4px;">💊 {detail["fungsi"][:150]}{"..." if len(detail["fungsi"]) > 150 else ""}</div>' if detail and detail.get('fungsi') else ''}
                            <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                Koordinat: {plant_data.iloc[0]['Y']:.6f}, {plant_data.iloc[0]['X']:.6f}
                                {f" (+{len(plant_data)-1} lokasi lainnya)" if len(plant_data) > 1 else ""}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error membuat peta: {e}")
        else:
            st.info("Tidak ada data lokasi untuk tanaman yang direkomendasikan.")

# ─────────────────────────────────────────────────────────────────────────────
# MENU: PETA SEBARAN
# ─────────────────────────────────────────────────────────────────────────────
elif selected == "Peta Sebaran":
    st.markdown("## 🗺️ Peta Interaktif Tanaman Herbal TNBTS")
    
    st.markdown(
        f"Visualisasi sebaran **{len(df_herbal_filtered)} titik tanaman herbal** "
        f"dari **{df_herbal['Nama'].nunique()} spesies** di kawasan TNBTS."
    )

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
        "Klik titik untuk melihat **detail lengkap** tanaman termasuk fungsi, syarat hidup, dan cara memanfaatkan.\n\n"
        "Gunakan **Layer Control** di pojok kanan atas peta untuk mengatur tampilan."
    )

    try:
        m = create_tnbts_map(
            show_desa_geojson=show_desa_geojson,
            show_kabupaten=show_kabupaten,
            show_batas_tnbts=show_batas_tnbts,
            show_tanaman=show_tanaman,
            gdf_desa=gdf_desa,
            gdf_kabupaten=gdf_kabupaten,
            gdf_batas=gdf_batas,
            df_tanaman_filtered=df_herbal_filtered,
            highlight_points=None,
            show_only_highlighted=False
        )
        # Gunakan st_folium dengan parameter untuk memastikan layer control terlihat
        st_folium(
            m, 
            width="100%", 
            height=640, 
            returned_objects=[],
            key="main_map"
        )
    except Exception as e:
        st.error(f"Error membuat peta: {e}")

# ======================== TAMBAHAN: VISUALISASI GEOJSON ========================
    st.markdown("---")
    st.markdown("## 📊 Visualisasi Data GeoJSON")
    st.markdown("Lihat data sebaran tanaman herbal dan batas kawasan TNBTS dalam format GeoJSON menggunakan GeoJSON Viewer online.")
    
    # Buat tab untuk memisahkan visualisasi
    tab_herbal, tab_batas = st.tabs(["🌿 Data Tanaman Herbal", "🗺️ Batas TNBTS"])
    
    with tab_herbal:
        # Cari file GeoJSON Tanaman Herbal
        geojson_file = _find_geojson('sebaran_tanaman_herbal_TNBTS.geojson')
        
        if geojson_file:
            try:
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Hitung statistik
                total_features = len(geojson_data.get('features', []))
                
                # Hitung jumlah tanaman unik
                unique_plants = set()
                for feature in geojson_data.get('features', []):
                    props = feature.get('properties', {})
                    nama = props.get('nama_tanaman', '')
                    if nama:
                        unique_plants.add(nama)
                
                st.markdown(f"""
                <div class="geojson-viewer-box">
                    <h3>🌿 Data Tanaman Herbal</h3>
                    <div class="geojson-stats">
                        <div class="stat-item"><strong>📁 File:</strong> sebaran_tanaman_herbal_TNBTS.geojson</div>
                        <div class="stat-item"><strong>📍 Total Fitur:</strong> {total_features} titik</div>
                        <div class="stat-item"><strong>🌱 Spesies Unik:</strong> {len(unique_plants)}</div>
                    </div>
                    <p style="margin: 12px 0; color: #555;">
                        Klik tombol di bawah untuk membuka data GeoJSON di <strong>geojson.io</strong> 
                        — platform interaktif untuk melihat, mengedit, dan menganalisis data geospasial.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Buat tombol untuk membuka di GeoJSON Viewer
                url = create_geojson_viewer_link(geojson_file)
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f'''
                    <div style="text-align: center;">
                        <a href="{url}" target="_blank" style="text-decoration: none;">
                            <button style="
                                background: linear-gradient(135deg, #2196F3, #1565C0);
                                color: white;
                                padding: 16px 40px;
                                border: none;
                                border-radius: 10px;
                                font-size: 18px;
                                font-weight: bold;
                                cursor: pointer;
                                box-shadow: 0 4px 15px rgba(33, 150, 243, 0.4);
                                transition: all 0.3s ease;
                                width: 100%;
                            "
                            onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(33, 150, 243, 0.5)';"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(33, 150, 243, 0.4)';">
                                🌐 Buka di GeoJSON Viewer
                            </button>
                        </a>
                        <p style="margin-top: 8px; font-size: 12px; color: #888;">
                            🔗 Akan terbuka di tab baru • geojson.io
                        </p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Tampilkan preview data
                with st.expander("📋 Preview Data GeoJSON (5 data pertama)"):
                    preview_data = []
                    for i, feature in enumerate(geojson_data.get('features', [])[:5]):
                        props = feature.get('properties', {})
                        geom = feature.get('geometry', {})
                        coords = geom.get('coordinates', [0, 0])
                        preview_data.append({
                            'No': i + 1,
                            'Nama Tanaman': props.get('nama_tanaman', '-'),
                            'Nama Ilmiah': props.get('nama_ilmiah', '-') or '-',
                            'Fungsi': (props.get('fungsi_manfaat', '-') or '-')[:50] + '...' if len((props.get('fungsi_manfaat', '-') or '-')) > 50 else (props.get('fungsi_manfaat', '-') or '-'),
                            'Koordinat': f"{coords[1]:.6f}, {coords[0]:.6f}",
                            'Ada Data': '✅' if props.get('ada_data_deskriptif') == 'Ya' else '❌'
                        })
                    st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
                
                # Tombol download GeoJSON
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    geojson_content = f.read()
                
                st.download_button(
                    label="📥 Download GeoJSON Tanaman Herbal",
                    data=geojson_content,
                    file_name="sebaran_tanaman_herbal_TNBTS.geojson",
                    mime="application/json",
                    key="download_geojson_herbal"
                )
                
            except Exception as e:
                st.warning(f"⚠️ Gagal membaca file GeoJSON: {e}")
                st.info("Pastikan file 'sebaran_tanaman_herbal_TNBTS.geojson' berada di direktori yang benar.")
        else:
            st.warning("⚠️ File 'sebaran_tanaman_herbal_TNBTS.geojson' tidak ditemukan.")
            st.info("Pastikan file GeoJSON berada di direktori yang sama dengan aplikasi.")
    
    with tab_batas:
        # Cari file Batas TNBTS GeoJSON
        batas_geojson_file = _find_geojson('Batas_TNBTS.geojson')
        
        if batas_geojson_file:
            try:
                with open(batas_geojson_file, 'r', encoding='utf-8') as f:
                    batas_geojson_data = json.load(f)
                
                # Hitung statistik
                total_features_batas = len(batas_geojson_data.get('features', []))
                
                # Hitung total area (approximasi dari jumlah polygon)
                total_polygons = 0
                for feature in batas_geojson_data.get('features', []):
                    geom = feature.get('geometry', {})
                    if geom.get('type') == 'MultiPolygon':
                        total_polygons += len(geom.get('coordinates', []))
                    elif geom.get('type') == 'Polygon':
                        total_polygons += 1
                
                # Dapatkan keterangan dari properti
                keterangan = ""
                for feature in batas_geojson_data.get('features', []):
                    props = feature.get('properties', {})
                    if props.get('Keterangan'):
                        keterangan = props.get('Keterangan')
                        break
                
                st.markdown(f"""
                <div class="geojson-viewer-box" style="border-color: #B71C1C;">
                    <h3 style="color: #B71C1C;">🏔️ Batas Taman Nasional Bromo Tengger Semeru</h3>
                    <div class="geojson-stats">
                        <div class="stat-item"><strong>📁 File:</strong> Batas_TNBTS.geojson</div>
                        <div class="stat-item"><strong>📐 Total Fitur:</strong> {total_features_batas}</div>
                        <div class="stat-item"><strong>🔷 Total Polygon:</strong> {total_polygons}</div>
                    </div>
                    <p style="margin: 12px 0; color: #555;">
                        <strong>📝 Keterangan:</strong> {keterangan if keterangan else 'Batas Taman Nasional Bromo Tengger Semeru'}
                    </p>
                    <p style="margin: 12px 0; color: #555;">
                        Klik tombol di bawah untuk membuka data batas TNBTS di <strong>geojson.io</strong> 
                        — platform interaktif untuk melihat, mengedit, dan menganalisis data geospasial.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Buat tombol untuk membuka Batas TNBTS di GeoJSON Viewer
                url_batas = create_geojson_viewer_link(batas_geojson_file)
                
                col1_b, col2_b, col3_b = st.columns([1, 2, 1])
                with col2_b:
                    st.markdown(f'''
                    <div style="text-align: center;">
                        <a href="{url_batas}" target="_blank" style="text-decoration: none;">
                            <button style="
                                background: linear-gradient(135deg, #B71C1C, #D32F2F);
                                color: white;
                                padding: 16px 40px;
                                border: none;
                                border-radius: 10px;
                                font-size: 18px;
                                font-weight: bold;
                                cursor: pointer;
                                box-shadow: 0 4px 15px rgba(183, 28, 28, 0.4);
                                transition: all 0.3s ease;
                                width: 100%;
                            "
                            onmouseover="this.style.transform='translateY(-3px)'; this.style.boxShadow='0 6px 20px rgba(183, 28, 28, 0.5)';"
                            onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(183, 28, 28, 0.4)';">
                                🗺️ Buka Batas TNBTS di GeoJSON Viewer
                            </button>
                        </a>
                        <p style="margin-top: 8px; font-size: 12px; color: #888;">
                            🔗 Akan terbuka di tab baru • geojson.io
                        </p>
                    </div>
                    ''', unsafe_allow_html=True)
                
                # Tampilkan preview data batas
                with st.expander("📋 Preview Data Batas TNBTS (3 data pertama)"):
                    preview_batas_data = []
                    for i, feature in enumerate(batas_geojson_data.get('features', [])[:3]):
                        props = feature.get('properties', {})
                        geom = feature.get('geometry', {})
                        geom_type = geom.get('type', '-')
                        
                        # Hitung jumlah koordinat
                        coords_count = 0
                        if geom_type == 'MultiPolygon':
                            for polygon in geom.get('coordinates', []):
                                for ring in polygon:
                                    coords_count += len(ring)
                        elif geom_type == 'Polygon':
                            for ring in geom.get('coordinates', []):
                                coords_count += len(ring)
                        
                        preview_batas_data.append({
                            'No': i + 1,
                            'Keterangan': props.get('Keterangan', '-'),
                            'Tipe Geometri': geom_type,
                            'Jumlah Koordinat': coords_count,
                        })
                    st.dataframe(pd.DataFrame(preview_batas_data), use_container_width=True, hide_index=True)
                
                # Tombol download Batas TNBTS GeoJSON
                with open(batas_geojson_file, 'r', encoding='utf-8') as f:
                    batas_geojson_content = f.read()
                
                st.download_button(
                    label="📥 Download Batas TNBTS GeoJSON",
                    data=batas_geojson_content,
                    file_name="Batas_TNBTS.geojson",
                    mime="application/json",
                    key="download_batas_geojson"
                )
                
            except Exception as e:
                st.warning(f"⚠️ Gagal membaca file Batas TNBTS GeoJSON: {e}")
                st.info("Pastikan file 'Batas_TNBTS.geojson' berada di direktori yang benar.")
        else:
            st.warning("⚠️ File 'Batas_TNBTS.geojson' tidak ditemukan.")
            st.info("Pastikan file GeoJSON batas TNBTS berada di direktori yang sama dengan aplikasi.")

    detail_cols = [c for c in ['NamaLatin', 'Fungsi', 'PotensiSebaran',
                                'SyaratHidup', 'CaraMemanfaatkan', 'BagianDimanfaatkan']
                   if c in df_herbal_filtered.columns]

    if not df_herbal_filtered.empty:
        agg_dict = {'X': 'count'}
        for c in detail_cols:
            agg_dict[c] = 'first'

        df_spesies_filtered = (
            df_herbal_filtered
            .groupby('Nama', as_index=False)
            .agg(agg_dict)
            .rename(columns={'X': 'Jumlah Titik'})
            .sort_values('Nama')
            .reset_index(drop=True)
        )
        cols_order = ['Nama', 'Jumlah Titik'] + detail_cols
        df_spesies_filtered = df_spesies_filtered[cols_order]
    else:
        df_spesies_filtered = df_herbal_filtered

    with st.expander(f"📋 Daftar {len(df_spesies_filtered)} Spesies Tanaman yang Ditampilkan"):
        st.dataframe(
            df_spesies_filtered,
            use_container_width=True, height=350, hide_index=True
        )
# ─────────────────────────────────────────────────────────────────────────────
# MENU: PETA 3D
# ─────────────────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────────────────
# MENU: DATA TANAMAN
# ─────────────────────────────────────────────────────────────────────────────
elif selected == "Data Tanaman":
    st.markdown("## 📋 Data Tanaman Herbal TNBTS")
    
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
        
        st.markdown("### 📋 Data Tanaman dengan Detail Lengkap")
        st.markdown("Klik nama tanaman untuk melihat detail fungsi, syarat hidup, dan cara memanfaatkan.")
        
        unique_plants = sorted(df_show['Nama'].unique())
        
        if len(unique_plants) > 0:
            cols_per_row = 2
            for i in range(0, len(unique_plants), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(unique_plants):
                        plant_name = unique_plants[idx]
                        with col:
                            with st.expander(f"🌿 {plant_name}", expanded=False):
                                detail = get_plant_detail(plant_name)
                                
                                if detail:
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; border-radius: 10px; padding: 16px; 
                                                border: 1px solid #e0e0e0; margin-bottom: 10px;">
                                        <div style="display: flex; justify-content: space-between; align-items: center; 
                                                    border-bottom: 2px solid #2E7D32; padding-bottom: 8px; margin-bottom: 12px;">
                                            <h4 style="margin: 0; color: #1B5E20; font-size: 16px;">🌿 {plant_name}</h4>
                                            <span style="font-style: italic; color: #666; font-size: 13px;">{detail.get('nama_latin', '')}</span>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    if detail.get('fungsi'):
                                        st.markdown(f"""
                                        <div style="background: #E8F5E9; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #2E7D32;">
                                            <span style="font-weight: bold; color: #1B5E20; font-size: 14px;">💊 Fungsi:</span><br>
                                            <span style="font-size: 13px; color: #333; line-height: 1.6;">{detail['fungsi']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if detail.get('syarat_hidup'):
                                        st.markdown(f"""
                                        <div style="background: #FFF8E1; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #F57F17;">
                                            <span style="font-weight: bold; color: #E65100; font-size: 14px;">🌱 Syarat Hidup:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.6;">{detail['syarat_hidup']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if detail.get('cara_memanfaatkan'):
                                        st.markdown(f"""
                                        <div style="background: #E3F2FD; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #0D47A1;">
                                            <span style="font-weight: bold; color: #0D47A1; font-size: 14px;">🔬 Cara Memanfaatkan:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.6;">{detail['cara_memanfaatkan']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    col_info1, col_info2 = st.columns(2)
                                    
                                    with col_info1:
                                        if detail.get('yang_dimanfaatkan'):
                                            st.markdown(f"""
                                            <div style="background: #F3E5F5; border-radius: 8px; padding: 10px 14px; 
                                                        margin: 6px 0; border-left: 4px solid #6A1B9A;">
                                                <span style="font-weight: bold; color: #4A148C; font-size: 13px;">✂️ Yang Dimanfaatkan:</span><br>
                                                <span style="font-size: 13px; color: #555;">{detail['yang_dimanfaatkan']}</span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    with col_info2:
                                        if detail.get('foto'):
                                            st.markdown(f"""
                                            <div style="background: #ECEFF1; border-radius: 8px; padding: 10px 14px; 
                                                        margin: 6px 0; border-left: 4px solid #455A64;">
                                                <span style="font-weight: bold; color: #37474F; font-size: 13px;">📷 Foto:</span><br>
                                                <span style="font-size: 12px; color: #666; word-break: break-all;">{detail['foto']}</span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    
                                    if detail.get('potensi_sebaran'):
                                        st.markdown(f"""
                                        <div style="background: #E0F7FA; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #00695C;">
                                            <span style="font-weight: bold; color: #00695C; font-size: 13px;">📍 Potensi Sebaran:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.5;">{detail['potensi_sebaran']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    plant_points = df_show[df_show['Nama'] == plant_name]
                                    if len(plant_points) > 0:
                                        st.markdown(f"""
                                        <div style="background: #F5F5F5; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border: 1px solid #ddd;">
                                            <span style="font-weight: bold; color: #555; font-size: 13px;">📍 Jumlah titik sebaran: {len(plant_points)}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.dataframe(
                                            plant_points[['No', 'X', 'Y']],
                                            use_container_width=True,
                                            hide_index=True,
                                            height=150
                                        )
                                else:
                                    st.warning(f"⚠️ Data detail untuk '{plant_name}' tidak tersedia")
                                    
                                    plant_points = df_show[df_show['Nama'] == plant_name]
                                    if len(plant_points) > 0:
                                        st.markdown(f"**📍 Jumlah titik sebaran:** {len(plant_points)}")
                                        st.dataframe(
                                            plant_points[['No', 'X', 'Y']],
                                            use_container_width=True,
                                            hide_index=True,
                                            height=150
                                        )
        else:
            st.info("Tidak ada data tanaman yang ditemukan")
        
        col_download1, col_download2, col_download3 = st.columns([1, 2, 1])
        with col_download2:
            st.download_button(
                "📥 Download CSV Data Tanaman",
                data=df_herbal.to_csv(index=False),
                file_name="data_tanaman_herbal_tnbts.csv",
                mime="text/csv",
                width='stretch'
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
            st.markdown("#### Ringkasan")
            st.metric("Total Spesies Unik", df_herbal['Nama'].nunique())
            st.metric("Total Titik Data", len(df_herbal))
            detailed_count = len([n for n in df_herbal['Nama'].unique() if get_plant_detail(n) is not None])
            st.metric("Tanaman dengan Data Detail", detailed_count)

# ─────────────────────────────────────────────────────────────────────────────
# MENU: STATISTIK
# ─────────────────────────────────────────────────────────────────────────────
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal TNBTS")
    
    st.markdown("### 🌿 Sebaran Spesies Tanaman")
    
    top_counts = df_herbal['Nama'].value_counts().head(15)
    st.bar_chart(top_counts, use_container_width=True)
    
    st.markdown("### 📋 Detail Tanaman Teratas")
    
    top_plants_list = top_counts.head(10).index.tolist()
    
    for plant_name in top_plants_list:
        with st.expander(f"🌿 {plant_name} ({top_counts[plant_name]} titik)", expanded=False):
            detail = get_plant_detail(plant_name)
            if detail:
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 8px; padding: 12px; margin: 4px 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <div style="grid-column: 1 / -1;">
                            <span style="font-weight: bold;">💊 Fungsi:</span>
                            <span style="font-size: 13px;">{detail.get('fungsi', '-')}</span>
                        </div>
                        <div>
                            <span style="font-weight: bold;">🌱 Syarat Hidup:</span><br>
                            <span style="font-size: 12px; color: #555;">{detail.get('syarat_hidup', '-')[:150]}{'...' if len(detail.get('syarat_hidup', '')) > 150 else ''}</span>
                        </div>
                        <div>
                            <span style="font-weight: bold;">🔬 Cara Memanfaatkan:</span><br>
                            <span style="font-size: 12px; color: #555;">{detail.get('cara_memanfaatkan', '-')[:150]}{'...' if len(detail.get('cara_memanfaatkan', '')) > 150 else ''}</span>
                        </div>
                        <div>
                            <span style="font-weight: bold;">✂️ Yang Dimanfaatkan:</span>
                            <span style="font-size: 13px;">{detail.get('yang_dimanfaatkan', '-')}</span>
                        </div>
                        <div>
                            <span style="font-weight: bold;">📍 Potensi Sebaran:</span><br>
                            <span style="font-size: 11px; color: #555;">{detail.get('potensi_sebaran', '-')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("Data detail tidak tersedia untuk tanaman ini")
    
    st.markdown("### 📋 Detail Statistik")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Spesies", df_herbal['Nama'].nunique())
    with col2:
        st.metric("Total Titik Data", len(df_herbal))
    with col3:
        avg = len(df_herbal) / df_herbal['Nama'].nunique()
        st.metric("Rata-rata per Spesies", f"{avg:.1f}")

# ─────────────────────────────────────────────────────────────────────────────
# HALAMAN: INFORMASI - DENGAN KATEGORISASI PENYAKIT (MENGGUNAKAN df_herbal)
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("## ℹ️ Informasi TNBTS")

    total_penduduk = gdf_desa['jumlah_pen'].sum() if not gdf_desa.empty and 'jumlah_pen' in gdf_desa.columns else 0
    total_kecamatan = gdf_desa['nama_kecam'].nunique() if not gdf_desa.empty and 'nama_kecam' in gdf_desa.columns else 0
    total_kabupaten = gdf_desa['nama_kabko'].nunique() if not gdf_desa.empty and 'nama_kabko' in gdf_desa.columns else 0
    total_detailed = len([n for n in df_herbal['Nama'].unique() if get_plant_detail(n) is not None])

    st.markdown(f"""
    <div class="info-box">
        <h4>🌋 Taman Nasional Bromo Tengger Semeru</h4>
        <p>TNBTS adalah kawasan konservasi di Jawa Timur dengan keanekaragaman hayati tinggi.
        WebGIS ini menampilkan <b>{df_herbal['Nama'].nunique()} spesies tanaman herbal</b> yang teridentifikasi
        di <b>8 kawasan ekologi</b> berbeda, dari savana vulkanik Bromo (±2.000 mdpl)
        hingga lereng atas Semeru (±2.500 mdpl) dan hutan primer Blok Ireng-Ireng.</p>
        <p>📋 <b>{total_detailed}</b> spesies memiliki data detail lengkap (fungsi, syarat hidup, cara memanfaatkan).</p>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── KATEGORISASI PENYAKIT ──────────────────────────────────────────────
    st.markdown("### 💊 Kategorisasi Tanaman Herbal Berdasarkan Ragam Penyakit")
    
    # Definisikan 12 kategori penyakit dan kata kunci pencariannya
    disease_categories = {
        "🫀 Penyakit Jantung & Pembuluh Darah": {
            "keywords": ["jantung", "tekanan darah", "hipertensi", "kolesterol", "stroke", "darah tinggi", "darah rendah", "pembuluh darah", "kardiovaskular"],
            "plants": []
        },
        "🫁 Pernapasan & Batuk": {
            "keywords": ["batuk", "pilek", "flu", "influenza", "radang tenggorokan", "bronkitis", "asma", "pernapasan", "dahak", "tenggorokan", "sesak", "nafas", "amandel"],
            "plants": []
        },
        "🌡️ Demam & Infeksi": {
            "keywords": ["demam", "panas", "meriang", "malaria", "infeksi", "antibakteri", "antiseptik", "antimikroba", "antijamur", "anti bakteri", "anti jamur"],
            "plants": []
        },
        "🧬 Pencernaan & Lambung": {
            "keywords": ["pencernaan", "perut", "kembung", "diare", "mual", "muntah", "sembelit", "maag", "asam lambung", "magh", "konstipasi", "cacing", "cacingan", "disentri"],
            "plants": []
        },
        "🦴 Sendi, Otot & Nyeri": {
            "keywords": ["nyeri", "pegal", "linu", "rematik", "asam urat", "sendi", "otot", "keseleo", "memar", "bengkak", "rematik", "nyeri otot", "pegal linu", "kram"],
            "plants": []
        },
        "🩸 Gula Darah & Metabolisme": {
            "keywords": ["gula darah", "diabetes", "kolesterol", "metabolisme", "obesitas", "berat badan", "trigliserida", "gula", "glukosa"],
            "plants": []
        },
        "🧴 Kulit & Luka": {
            "keywords": ["luka", "kulit", "bisul", "borok", "gatal", "jerawat", "eksim", "kurap", "herpes", "bakar", "luka bakar", "memar", "ruam", "kudis", "infeksi kulit"],
            "plants": []
        },
        "🧠 Saraf & Stres": {
            "keywords": ["saraf", "stres", "insomnia", "susah tidur", "kejang", "epilepsi", "menenangkan", "cemas", "tidur", "nyenyak", "gelisah"],
            "plants": []
        },
        "🤰 Kesehatan Wanita & Kesuburan": {
            "keywords": ["haid", "menstruasi", "keputihan", "kesuburan", "hamil", "pasca persalinan", "ASI", "menopause", "kewanitaan", "persalinan", "kandungan", "kehamilan"],
            "plants": []
        },
        "🧪 Ginjal & Saluran Kemih": {
            "keywords": ["ginjal", "kencing", "urine", "batu ginjal", "diuretik", "saluran kemih", "kencing batu", "buang air kecil", "kemih"],
            "plants": []
        },
        "🛡️ Imunitas & Antioksidan": {
            "keywords": ["imun", "daya tahan", "antioksidan", "kanker", "tumor", "radikal bebas", "vitamin", "kekebalan", "imunitas", "penuaan", "antioksidan"],
            "plants": []
        },
        "🌿 Antiradang & Detoksifikasi": {
            "keywords": ["antiradang", "anti inflamasi", "detoksifikasi", "pembersih darah", "tonik", "stamina", "anti-inflamasi", "radang", "peradangan", "detoks", "antiinflamasi"],
            "plants": []
        }
    }
    
    # Ambil semua tanaman unik dari df_herbal (bukan dari HERBAL_DETAIL_DATA)
    all_plants = sorted(df_herbal['Nama'].unique())
    
    # Kategorikan setiap tanaman dari df_herbal
    for plant_name in all_plants:
        # Dapatkan detail dari df_herbal melalui get_plant_detail
        detail = get_plant_detail(plant_name)
        if not detail:
            # Jika tidak ada detail di HERBAL_DETAIL_DATA, coba cari di df_herbal langsung
            plant_row = df_herbal[df_herbal['Nama'] == plant_name]
            if not plant_row.empty:
                row = plant_row.iloc[0]
                fungsi = row.get('Fungsi', '')
                bagian = row.get('BagianDimanfaatkan', '')
            else:
                continue
        else:
            fungsi = detail.get('fungsi', '')
            bagian = detail.get('yang_dimanfaatkan', '')
        
        fungsi_lower = fungsi.lower()
        
        # Periksa kecocokan dengan setiap kategori
        matched_categories = []
        for category, info in disease_categories.items():
            for keyword in info["keywords"]:
                if keyword.lower() in fungsi_lower:
                    info["plants"].append({
                        "name": plant_name,
                        "fungsi": fungsi,
                        "bagian": bagian
                    })
                    matched_categories.append(category)
                    break
        
        # Jika tidak masuk kategori manapun, masukkan ke "Antiradang & Detoksifikasi"
        if not matched_categories and fungsi:
            disease_categories["🌿 Antiradang & Detoksifikasi"]["plants"].append({
                "name": plant_name,
                "fungsi": fungsi,
                "bagian": bagian
            })
    
    # Hapus kategori yang tidak memiliki tanaman
    disease_categories = {
        k: v for k, v in disease_categories.items() 
        if v["plants"]
    }
    
    # Tampilkan statistik kategorisasi
    st.markdown("#### 📊 Statistik Kategorisasi")
    
    total_spesies = len(all_plants)
    total_kategorisasi = sum(len(info["plants"]) for info in disease_categories.values())
    active_categories = len(disease_categories)
    avg_per_category = total_kategorisasi / active_categories if active_categories > 0 else 0
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total Spesies", total_spesies)
    with col_stat2:
        st.metric("Total Kategorisasi", f"{total_kategorisasi}")
    with col_stat3:
        st.metric("Kategori Aktif", active_categories)
    with col_stat4:
        st.metric("Rata-rata per Kategori", f"{avg_per_category:.1f}")
    
    # Tampilkan jumlah per kategori dalam bar
    st.markdown("#### 📈 Jumlah Tanaman per Kategori")
    category_counts = {cat: len(info["plants"]) for cat, info in disease_categories.items()}
    # Buat DataFrame untuk bar chart
    df_categories = pd.DataFrame({
        'Kategori': list(category_counts.keys()),
        'Jumlah': list(category_counts.values())
    })
    st.bar_chart(df_categories.set_index('Kategori'), use_container_width=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # ── TAMPILAN KATEGORI ──────────────────────────────────────────────────
    st.markdown("#### 🌿 Daftar Tanaman Berdasarkan Kategori Penyakit")
    st.markdown("Klik setiap kategori untuk melihat daftar tanaman yang dapat membantu mengatasinya.")
    
    # Sortir kategori berdasarkan jumlah tanaman terbanyak
    sorted_categories = sorted(
        disease_categories.items(),
        key=lambda x: len(x[1]["plants"]),
        reverse=True
    )
    
    # Tampilkan setiap kategori sebagai expander
    for category_name, info in sorted_categories:
        plants = info["plants"]
        if not plants:
            continue
            
        with st.expander(f"{category_name} ({len(plants)} spesies)", expanded=False):
            # Tampilkan dalam grid 2 kolom
            cols_per_row = 2
            for i in range(0, len(plants), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(plants):
                        plant = plants[idx]
                        with col:
                            fungsi_short = plant['fungsi'][:120] + ('...' if len(plant['fungsi']) > 120 else '')
                            st.markdown(f"""
                            <div style="background: #f8f9fa; border-radius: 8px; padding: 12px 14px; 
                                        border-left: 4px solid #2E7D32; 
                                        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
                                        margin-bottom: 8px; height: 100%;">
                                <div style="font-weight: bold; color: #1B5E20; font-size: 14px;">
                                    🌿 {plant['name']}
                                </div>
                                <div style="font-size: 12px; color: #555; margin: 4px 0; line-height: 1.4;">
                                    {fungsi_short}
                                </div>
                                <div style="font-size: 11px; color: #888; margin-top: 4px;">
                                    ✂️ {plant['bagian'] if plant['bagian'] else 'Tidak tersedia'}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Tombol Lihat di Peta
                            if st.button(
                                f"📍 Lihat di Peta", 
                                key=f"view_inf_{plant['name']}_{idx}_{category_name[:5]}"
                            ):
                                st.session_state.menu_selected = "Peta Sebaran"
                                st.session_state.highlighted_plants = [plant['name']]
                                st.session_state.show_highlighted = True
                                st.rerun()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── Tim peneliti ──────────────────────────────────────────────────────────
    st.markdown("### 👥 Tim Peneliti")
    tm_cols = st.columns(4)
    team = [
        ("https://prasetya.ub.ac.id/wp-content/uploads/2023/10/BU-TYAS-405x270.jpg",
         "Dr Eng Turniningtyas Ayu R.", "ST., MT", "Ketua Tim"),
        ("https://img.inews.co.id/files/networks/2022/11/03/e9d8d_prof-sasmito-djati.jpg",
         "Prof.Dr.Ir. Moch. Sasmito Djati", "M.S.", "Pakar Tanaman Herbal"),
        ("https://i1.rgstatic.net/ii/profile.image/296334033735682-1447662947469_Q512/Adipandang-Yudono.jpg",
         "Adipandang Yudono", "S.Si., M.U.R.P., Ph.D", "Pakar GIS & WebGIS Analytics"),
        ("https://sau.ub.ac.id/storage/foto/96Ptjb7GPiCz32JQkveQ3Hr7p5hk5C78biQvobo5.png",
         "Dr. Ir. Arief Andy Soebroto", "S.T., M.Kom.", "Pakar AI & IoT"),
    ]
    for (photo, name, title, role), col in zip(team, tm_cols):
        with col:
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 10px; padding: 16px; text-align: center;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 12px; height: 100%;">
                <img src="{photo}" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover;
                            border: 3px solid #2E7D32; margin-bottom: 8px;" 
                            onerror="this.onerror=null; this.src='https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=2E7D32&color=fff&size=100';">
                <h4 style="margin: 4px 0; color: #1B5E20; font-size: 14px;">{name}</h4>
                <p style="margin: 2px 0; font-size: 13px; color: #555;">{title}</p>
                <p style="margin: 2px 0; font-size: 12px; color: #2E7D32; font-weight: bold;">{role}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # ── Sumber Data ──────────────────────────────────────────────────────────
    st.markdown("""
    ### 📍 Sumber Data
    - **Data Tanaman:** Hasil survei lapangan Tim Peneliti UB (2026) — 133 spesies, 246 titik temuan sebaran tanaman herbal di TNBTS
    - **Data Detail Tanaman:** Dokumentasi lengkap fungsi, syarat hidup, dan cara pemanfaatan
    - **Koordinat Kawasan:** Batas ekologi TNBTS berdasarkan survei GPS lapangan & interpretasi citra satelit
    - **Data Desa:** GeoJSON BIG/BPS (41 desa penyangga TNBTS)
    - **Peta Basemap:** OpenStreetMap, Esri World Imagery (Satelit), OpenTopoMap
    - **Model 3D:** Sketchfab — smartmAPPS
    """)
