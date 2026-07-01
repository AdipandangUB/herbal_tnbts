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
# DATA TANAMAN HERBAL (EMBEDDED - FALLBACK)
# ─────────────────────────────────────────────────────────────────────────────
# Data dari file Titik Rapihin.xlsx yang di-embed sebagai fallback
HERBAL_DATA_EMBEDDED = [
    (1, 'DELIMA', 112.801975, -8.046787),
    (2, 'JAMBU', 112.801975, -8.046787),
    (3, 'SEMBUKAN', 112.801975, -8.046787),
    (4, 'DELIMA', 112.801975, -8.046787),
    (5, 'JAMBU BIJI', 112.801975, -8.046787),
    (6, 'KESIMBUKAN', 112.801975, -8.046870),
    (7, 'CABE GENDOT', 112.806081, -7.901768),
    (8, 'LAOS', 112.808256, -8.051149),
    (9, 'CABE GENDOT', 112.830632, -7.919994),
    (10, 'TEPUNG OTOT', 112.846877, -8.015389),
    (11, 'GANJAN', 112.846877, -8.015389),
    (12, 'KECUBUNG PUTIH', 112.847416, -7.922730),
    (13, 'PAITAN', 112.848401, -8.015110),
    (14, 'JAHE', 112.850199, -8.014977),
    (15, 'LABU SIAM', 112.850204, -8.015127),
    (16, 'MANISA HITAM', 112.850204, -8.015127),
    (17, 'MANISA HITAM', 112.850208, -8.015127),
    (18, 'JAMBU', 112.856939, -7.919631),
    (19, 'JAMBU BIJI', 112.856939, -7.919631),
    (20, 'DAUN MANGKOK MERAH/BAYAM MERAH', 112.864016, -8.009914),
    (21, 'ADAS', 112.864227, -8.009353),
    (22, 'ADAS', 112.864227, -8.009353),
    (23, 'SEREH', 112.864250, -8.009797),
    (24, 'JARAK MERAH', 112.865075, -7.918463),
    (25, 'MANISA HITAM', 112.880200, -7.919971),
    (26, 'TERONG BELANDA', 112.880537, -7.919971),
    (27, 'TERONG BELANDA', 112.880590, -7.920100),
    (28, 'LOMBOK TERONG', 112.880632, -7.919999),
    (29, 'CARICA', 112.880852, -7.919954),
    (30, 'CARICA', 112.880857, -7.919554),
    (31, 'JAHE', 112.890991, -7.951751),
    (32, 'LOMBOK TERONG', 112.896981, -7.901768),
    (33, 'GANJAN', 112.896997, -7.901751),
    (34, 'ARBEI', 112.897021, -7.902696),
    (35, 'ARBEI', 112.897021, -7.902696),
    (36, 'CARICA', 112.898502, -7.988507),
    (37, 'CARICA', 112.898502, -7.988507),
    (38, 'CARICA', 112.898502, -7.988507),
    (39, 'CARICA', 112.898802, -7.988507),
    (40, 'PAITAN', 112.901323, -7.895460),
    (41, 'PAHITAN', 112.901323, -7.895460),
    (42, 'PAITAN', 112.901323, -7.895460),
    (43, 'JARAK MERAH', 112.901614, -7.883742),
    (44, 'JARAK MERAH', 112.901614, -7.883742),
    (45, 'AJERAN PUTIH', 112.902096, -7.876545),
    (46, 'GANJAN', 112.905667, -7.952630),
    (47, 'ARBEI', 112.906334, -7.984777),
    (48, 'ARBEI', 112.906334, -7.984777),
    (49, 'BUAH PEPINO', 112.906345, -7.985210),
    (50, 'AIR KUNCUP KECUBUNG GUNUNG', 112.906433, -7.984717),
    (51, 'TERONG BELANDA', 112.906433, -7.984717),
    (52, 'BIT MERAH', 112.906453, -7.985204),
    (53, 'BIT MERAH', 112.906453, -7.985204),
    (54, 'JARAK MERAH', 112.906554, -7.985286),
    (55, 'JARAK MERAH', 112.906554, -7.985286),
    (56, 'JARAK HITAM', 112.906554, -7.985286),
    (57, 'JARAK MERAH', 112.906554, -7.985286),
    (58, 'ADAS', 112.907053, -7.985087),
    (59, 'GANJAN', 112.911370, -7.896581),
    (60, 'JAMBU WER', 112.911490, -7.896698),
    (61, 'JAMBU WER', 112.911490, -7.906698),
    (62, 'CERI GUNUNG', 112.911540, -7.895863),
    (63, 'SURI PANDAK', 112.912578, -8.045221),
    (64, 'JAHEWONO/PURWOCENG', 112.912883, -8.046042),
    (65, 'JARAK HIJAU', 112.915327, -7.979138),
    (66, 'JARAK', 112.915327, -7.979138),
    (67, 'JENGGOT WESI', 112.916632, -8.040489),
    (68, 'CALINGAN', 112.922384, -7.971914),
    (69, 'CALINGAN', 112.924369, -7.996918),
    (70, 'JENGGOT WESI', 112.928867, -8.037286),
    (71, 'KAYU AMPET', 112.929233, -8.035871),
    (72, 'GEMBOKAN', 112.931855, -8.039685),
    (73, 'CIPLUKAN', 112.933274, -8.030870),
    (74, 'KRANGEAN', 112.933517, -8.032445),
    (75, 'TEPUNG OTOT', 112.935605, -8.023313),
    (76, 'TIREM', 112.939092, -8.002598),
    (77, 'GODAG', 112.940496, -7.998516),
    (78, 'AWAR-AWAR', 112.940877, -7.995191),
    (79, 'DAUN KANCING/SEMANGGI LIAR', 112.941457, -8.015665),
    (80, 'ANTING PUTRI/FUCHSIA MERAH', 112.941545, -7.994942),
    (81, 'GANYONG', 112.941746, -8.000256),
    (82, 'RANGGITAN', 112.942222, -8.021389),
    (83, 'STROBERI HUTAN', 112.943040, -8.022686),
    (84, 'SURENGAN/SELADA LIAR', 112.943409, -7.997615),
    (85, 'KETUL', 112.944211, -8.001242),
    (86, 'LILI-LILIAN LIAR', 112.944995, -8.000340),
    (87, 'AKAR SEMPRETAN', 112.945833, -8.002366),
    (88, 'CALINGAN', 112.946141, -8.002254),
    (89, 'ADAS', 112.947492, -7.979090),
    (90, 'ADAS', 112.947540, -7.979791),
    (91, 'BAKUNG', 112.948793, -8.011198),
    (92, 'TOMAT CERI', 112.950278, -8.013333),
    (93, 'TOMAT CERI', 112.950278, -8.013333),
    (94, 'BAKUNG', 112.950278, -8.013333),
    (95, 'TOMAT CERI', 112.950278, -8.012778),
    (96, 'AJERAN PUTIH', 112.950682, -8.009019),
    (97, 'ALANG-ALANG', 112.950828, -7.930880),
    (98, 'ALANG-ALANG', 112.950828, -7.930880),
    (99, 'TEPUNG OTOT', 112.950908, -7.930724),
    (100, 'JARINGAN', 112.950960, -7.930678),
    (101, 'PUTIHAN', 112.950980, -7.930804),
    (102, 'KEMLANDINGAN/KLANDINGAN', 112.951197, -7.930200),
    (103, 'KEMLANDINGAN', 112.951206, -7.930210),
    (104, 'EDELWEIS', 112.951276, -7.931024),
    (105, 'ALANG-ALANG', 112.951282, -7.930039),
    (106, 'EDELWEIS', 112.951327, -7.939024),
    (107, 'PASOTE', 112.951343, -7.931000),
    (108, 'ALANG-ALANG', 112.951787, -7.930879),
    (109, 'AJERAN PUTIH', 112.955549, -7.953053),
    (110, 'TEMPUYUNG/KETIUW', 112.959908, -7.930724),
    (111, 'JARAK HIJAU', 112.961040, -7.922386),
    (112, 'CEMARA GUNUNG SEMAK', 112.961342, -7.921251),
    (113, 'CEMARA GUNUNG SEMAK', 112.961382, -7.971251),
    (114, 'ADAS', 112.964345, -7.922273),
    (115, 'AIR KUNCUP KECUBUNG GUNUNG', 112.964372, -7.922737),
    (116, 'KECUBUNG PUTIH', 112.964474, -7.922857),
    (117, 'AIR KUNCUP KECUBUNG GUNUNG', 112.964474, -7.922857),
    (118, 'CIPLUKAN', 112.964490, -7.922893),
    (119, 'CIPLUKAN', 112.964490, -7.922893),
    (120, 'JARAK HIJAU', 112.966104, -7.922386),
    (121, 'JAMUR LINGZHI', 112.974959, -8.032646),
    (122, 'AJERAN PUTIH', 112.975606, -7.980074),
    (123, 'AWAR-AWAR', 112.978188, -7.974912),
    (124, 'AWAR-AWAR', 112.979085, -8.037856),
    (125, 'PAKIS SEJATI', 112.980115, -8.018784),
    (126, 'PAKIS (DAVALLIA)', 112.980267, -8.032115),
    (127, 'ADAS', 112.983153, -7.915076),
    (128, 'SELEDRI', 112.983340, -7.914567),
    (129, 'KECUBUNG KUNING', 112.983371, -7.914381),
    (130, 'TERONG BELANDA', 112.983948, -7.914695),
    (131, 'DRINGU', 112.983977, -7.914867),
    (132, 'DRINGU', 112.983977, -7.914867),
    (133, 'CARICA', 112.984027, -7.915494),
    (134, 'CARICA', 112.984027, -7.915494),
    (135, 'PAKU PURBA', 112.986718, -8.031921),
    (136, 'TEKLAN', 112.989008, -8.094180),
    (137, 'SIMBARAN', 112.990639, -8.018076),
    (138, 'JARINGAN', 112.990960, -7.930678),
    (139, 'PAKU RANE/PAKU KAWAT', 112.992477, -8.021199),
    (140, 'KESEK', 112.995600, -7.968400),
    (141, 'KIRINYUH', 112.995600, -7.968400),
    (142, 'AJERAN PUTIH', 112.996344, -8.027946),
    (143, 'BLUBUK', 112.996600, -7.968000),
    (144, 'BLUBUK', 112.996600, -7.968000),
    (145, 'KAYU AMPET', 112.996800, -7.968200),
    (146, 'KAYU AMPET', 112.996800, -7.968200),
    (147, 'ADAS', 112.999300, -7.965800),
    (148, 'KECUBUNG KUNING', 112.999455, -7.965901),
    (149, 'AIR KUNCUP KECUBUNG GUNUNG', 112.999455, -7.965901),
    (150, 'ADAS', 112.999457, -7.965879),
    (151, 'EDELWEIS', 112.999516, -7.956060),
    (152, 'CIPLUKAN', 112.999910, -7.967044),
    (153, 'SENGGANEN/SENGGANI', 113.000200, -7.967600),
    (154, 'PUTIHAN', 113.000200, -7.967600),
    (155, 'PUTIHAN', 113.000200, -7.967600),
    (156, 'SENGGANEN/SENGGANI', 113.000200, -7.967600),
    (157, 'PRONOJIWO', 113.004192, -8.029210),
    (158, 'SIRIH HUTAN/CABE JAWA', 113.004444, -8.029722),
    (159, 'CABE JAWA', 113.004444, -8.029722),
    (160, 'AJERAN PUTIH', 113.005054, -8.048948),
    (161, 'CALINGAN', 113.005141, -8.030703),
    (162, 'KAPULAGA', 113.005441, -8.064376),
    (163, 'PULOSARI', 113.006030, -8.029182),
    (164, 'SLIMPAT/SELIMPAT', 113.006889, -8.049956),
    (165, 'KECUBUNG PUTIH', 113.007500, -8.033611),
    (166, 'JENGGOT WESI', 113.007500, -8.038333),
    (167, 'ANTING-ANTING', 113.007500, -8.038333),
    (168, 'AIR KUNCUP KECUBUNG GUNUNG', 113.007500, -8.038611),
    (169, 'ANTING PUTRI/FUCHSIA MERAH', 113.007500, -8.038333),
    (170, 'JAMUR LINGZHI', 113.009718, -8.037503),
    (171, 'MENIRAN', 113.011480, -8.080804),
    (172, 'PISANG HUTAN', 113.012222, -8.040000),
    (173, 'KECUBUNG KUNING', 113.015691, -7.986493),
    (174, 'MARKISA', 113.015691, -7.986493),
    (175, 'TOMAT', 113.015714, -7.986501),
    (176, 'DAUN BAWANG', 113.015732, -7.986502),
    (177, 'SELEDRI', 113.015742, -7.986405),
    (178, 'SELEDRI', 113.015742, -7.986405),
    (179, 'SEMANGGI LIAR', 113.015752, -7.986413),
    (180, 'SEMANGGI LIAR', 113.015752, -7.986413),
    (181, 'SAWI HITAM', 113.015757, -7.986393),
    (182, 'SAWI IRENG', 113.015757, -7.986393),
    (183, 'KETUMBAR', 113.015759, -7.986485),
    (184, 'SENIKIR', 113.015759, -7.986458),
    (185, 'BUNGA TAHI AYAM/GEMITIR/MARISELA', 113.015759, -7.986458),
    (186, 'KESEK', 113.015760, -7.986488),
    (187, 'WORTEL', 113.015774, -7.986418),
    (188, 'GANJAN', 113.016111, -7.986944),
    (189, 'KOPI ARABIKA', 113.016111, -7.986944),
    (190, 'KACANG BABI', 113.016111, -7.986944),
    (191, 'PECUT KUDA', 113.017233, -7.960574),
    (192, 'DAUN KANCING/SEMANGGI LIAR', 113.018173, -7.971436),
    (193, 'KUNYIT', 113.023762, -7.978400),
    (194, 'KETUMBAR', 113.023817, -7.978630),
    (195, 'DRINGU', 113.024150, -7.978630),
    (196, 'DAUN BAWANG', 113.025098, -7.975778),
    (197, 'PAITAN', 113.025278, -8.013611),
    (198, 'PAITAN', 113.025278, -8.013611),
    (199, 'TEBU IRENG', 113.025370, -7.973474),
    (200, 'PARIJOTO', 113.026874, -8.024953),
    (201, 'AWAR-AWAR', 113.026885, -7.995636),
    (202, 'JAMUR LINGZHI', 113.027076, -8.048771),
    (203, 'DAUN SENDOK/SANGKUAH', 113.027605, -8.051614),
    (204, 'PAKIS GARUDA', 113.028600, -8.053304),
    (205, 'KENCANA UNGU', 113.028632, -8.021287),
    (206, 'KETUMBAR', 113.028632, -8.021287),
    (207, 'RANTI', 113.028845, -8.049922),
    (208, 'KECUBUNG PUTIH', 113.031111, -8.052500),
    (209, 'AIR KUNCUP KECUBUNG GUNUNG', 113.031111, -8.052500),
    (210, 'ANDONG', 113.051111, -8.067778),
    (211, 'ANDONG', 113.051111, -8.067778),
    (212, 'SEMANGGI', 113.052808, -7.991959),
    (213, 'PATIKAN KEBO', 113.096769, -8.128499),
    (214, 'EDELWEIS', 113.964478, -7.973473),
]

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
def load_herbal_data():
    """
    Membaca data sebaran tanaman herbal dari berkas Excel.
    Jika file tidak ditemukan, gunakan data embedded.
    """
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
                
                # Bersihkan data
                df.columns = df.columns.str.strip()
                
                # Cari kolom yang sesuai
                x_col, y_col, name_col = None, None, None
                for col in df.columns:
                    col_lower = col.lower().strip()
                    if col_lower in ['x', 'lon', 'longitude', 'long']:
                        x_col = col
                    elif col_lower in ['y', 'lat', 'latitude']:
                        y_col = col
                    elif col_lower in ['nama', 'name', 'jenis', 'spesies', 'tanaman']:
                        name_col = col
                
                # Jika tidak ditemukan, gunakan indeks
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
                st.sidebar.warning(f"⚠️ Gagal membaca {filename}: {e}")
                continue
    
    # Jika file tidak ditemukan, gunakan data embedded
    st.sidebar.info("📊 Menggunakan data tanaman herbal embedded (214 titik)")
    df = pd.DataFrame(HERBAL_DATA_EMBEDDED, columns=['No', 'Nama', 'X', 'Y'])
    return df


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
        ✅ <b>Data Tanaman</b><br><small>{len(df_herbal)} titik • {df_herbal['Nama'].nunique()} spesies</small>
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
# FUNGSI CHATBOT AI
# ─────────────────────────────────────────────────────────────────────────────
def extract_symptoms_from_text(text):
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
    # Mapping gejala ke tanaman (hardcoded untuk sementara)
    symptom_plant_map = {
        'demam': ['AJERAN PUTIH', 'BAWANG MERAH', 'BUNGA MATAHARI', 'PAITAN', 'PECUT KUDA', 'TAPAK LIMAN', 'VERVAIN'],
        'batuk': ['ADAS', 'BUAH KLANDINGAN', 'BUNGA HARIANG', 'KENIKIR', 'PULOSARI', 'SUPLIR'],
        'nyeri': ['BIDARA LAUT', 'DAUN DADAP', 'JAMBU WER', 'SURI PANDAK'],
        'luka': ['CALINGAN', 'GANJAN', 'GEMBOKAN', 'JARAK MERAH', 'KIRINYUH', 'PAKU SIGUNG', 'SIMBARAN', 'TRABASAN', 'WEDUSAN'],
        'pencernaan': ['ADAS', 'ALANG-ALANG', 'AWAR-AWAR', 'BELUNTAS', 'DRINGU', 'GANYONG', 'JAHE', 'KETUMBAR', 'LAOS', 'LOBAK', 'SAWI IRENG'],
        'darah': ['BAWANG PUTIH', 'KENCANA UNGU', 'STROBERI TENGGER', 'SUPLIR'],
        'antiradang': ['AJERAN PUTIH', 'AWAR-AWAR', 'KUNYIT', 'SEMANGGI', 'TEPUNG OTOT'],
        'diuretik': ['ALANG-ALANG', 'RUMPUT TEKI-TEKIAN'],
        'antiseptik': ['SIRIH'],
        'antioksidan': ['KENIKIR', 'ANGGREK TANAH', 'BIDARA LAUT']
    }
    
    matched_plants = set()
    for symptom in symptoms:
        if symptom in symptom_plant_map:
            matched_plants.update(symptom_plant_map[symptom])
    
    if matched_plants:
        return df_herbal[df_herbal['Nama'].isin(matched_plants)]
    
    # Jika tidak ada yang cocok, cari berdasarkan substring
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
    """Generate response from chatbot based on user input."""
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
    show_desa_geojson, show_kabupaten, show_batas_tnbts, show_tanaman,
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
                    <tr>
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
            st.markdown("#### Ringkasan")
            st.metric("Total Spesies Unik", df_herbal['Nama'].nunique())
            st.metric("Total Titik Data", len(df_herbal))

# ═════════════════════════════════════════════════════════════════════════════
# MENU: STATISTIK
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal TNBTS")
    
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
        avg = len(df_herbal) / df_herbal['Nama'].nunique()
        st.metric("Rata-rata per Spesies", f"{avg:.1f}")

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
