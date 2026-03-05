import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import geopandas as gpd
import json
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="WebGIS Tanaman Herbal TNBTS",
    page_icon="🌿",
    layout="wide"
)

# Inisialisasi session state untuk menyimpan status
if 'menu_selected' not in st.session_state:
    st.session_state.menu_selected = "Peta Sebaran"

# Custom CSS dengan header, sidebar, dan footer background gambar
st.markdown("""
<style>
    /* header dan title dengan background gambar */
    .main-header {
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), url('https://tunashijau.id/wp-content/uploads/2023/12/tnbts.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        padding: 2.5rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-weight: bold;
    }
    
    .main-header p {
        color: #E8F5E9;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        background: rgba(0,0,0,0.3);
        display: inline-block;
        padding: 0.3rem 1rem;
        border-radius: 30px;
        backdrop-filter: blur(5px);
    }
    
    /* tampilan sidebar dengan background gambar */
    [data-testid="stSidebar"] {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.7)), url('https://asset.kompas.com/crops/G4x25tAnC3TVtqQzc19Qi3y4fwo=/0x0:1200x800/1200x800/data/photo/2021/10/29/617b830f26293.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        background-color: rgba(255, 255, 255, 0.15);
        padding: 10px;
        border-radius: 10px;
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        background-color: transparent;
    }
    
    [data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] {
        color: white;
    }
    
    [data-testid="stSidebar"] .stSlider label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stCheckbox label {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stCheckbox div[data-testid="stMarkdownContainer"] {
        color: white !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
    [data-testid="stSidebar"] p {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Sidebar header baru dengan background gambar */
    .sidebar-header-new {
        background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.6)), url('https://asset.kompas.com/crops/G4x25tAnC3TVtqQzc19Qi3y4fwo=/0x0:1200x800/1200x800/data/photo/2021/10/29/617b830f26293.png');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        padding: 1.5rem 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        border: 2px solid rgba(255, 215, 0, 0.3);
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }
    
    .sidebar-header-new h3 {
        color: #FFD700 !important;
        margin: 0;
        font-size: 1.4rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
        font-weight: bold;
    }
    
    .sidebar-header-new p {
        color: #FFFFFF !important;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        font-style: italic;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.7);
        background: rgba(0,0,0,0.3);
        display: inline-block;
        padding: 0.2rem 1rem;
        border-radius: 20px;
        backdrop-filter: blur(3px);
    }
    
    /* tampilan metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .metric-card h3 {
        color: #2E7D32;
        margin: 0;
        font-size: 1.8rem;
        font-weight: bold;
    }
    
    .metric-card p {
        color: #666;
        margin: 0.2rem 0 0 0;
        font-size: 0.9rem;
        text-transform: uppercase;
    }
    
    /* tampilan tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: #f5f5f5;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    
    /* tampilan expander */
    .streamlit-expanderHeader {
        background-color: #f5f5f5;
        border-radius: 5px;
    }
    
    /* tampilan dataframe */
    .dataframe-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        background: white;
    }
    
    /* tampilan footer dengan background gambar */
    .footer {
        background: linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.7)), url('https://statik.tempo.co/data/2024/05/26/id_1305154/1305154_720.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .footer p {
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }
    
    .footer a {
        color: #FFD700;
        text-decoration: none;
        font-weight: bold;
    }
    
    .footer a:hover {
        text-decoration: underline;
        color: #FFA500;
    }
    
    /* tampilan badges untuk legenda */
    .legend-badge {
        display: inline-block;
        width: 20px;
        height: 20px;
        border-radius: 4px;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    .legend-item {
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .badge-pohon {
        background-color: #28a745;
    }
    
    .badge-semak {
        background-color: #90EE90;
    }
    
    .badge-herba {
        background-color: #5F9EA0;
    }
    
    .badge-bunga {
        background-color: #FF69B4;
    }
    
    .badge-rumput {
        background-color: #FFD700;
    }
    
    .badge-pakis {
        background-color: #006400;
    }
    
    .badge-lumut {
        background-color: #D3D3D3;
    }
    
    .badge-success {
        background-color: #4CAF50;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    .badge-warning {
        background-color: #FFC107;
        color: black;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    .badge-info {
        background-color: #2196F3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 0.5rem;
    }
    
    /* tampilan divider */
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent, #4CAF50, transparent);
        margin: 2rem 0;
    }
    
    /* tampilan image caption */
    .image-caption {
        text-align: center;
        font-style: italic;
        color: #666;
        margin-top: 0.3rem;
        font-size: 0.9rem;
    }
    
    /* tampilan button */
    .stButton > button {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* tampilan download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1976D2 0%, #2196F3 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: bold;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #0D47A1 0%, #1976D2 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* tampilan info boxes */
    .info-box {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 1.5rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .info-box h4 {
        color: #2E7D32;
        margin-top: 0;
        margin-bottom: 1rem;
    }
    
    .info-box ul {
        margin-bottom: 1rem;
    }
    
    /* tampilan status badges di sidebar */
    .status-badge {
        background: rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(5px);
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #FFD700;
        color: white;
    }
    
    .status-badge small {
        color: rgba(255, 255, 255, 0.8);
    }
    
    /* Styling untuk foto tim */
    .team-card {
        background: #f5f5f5;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        height: 420px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    
    .team-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .team-photo {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #4CAF50;
        margin-bottom: 1rem;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .team-name {
        color: #2E7D32;
        margin: 0.5rem 0 0.2rem 0;
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    .team-title {
        color: #666;
        margin: 0.2rem 0;
        font-size: 0.95rem;
    }
    
    .team-role {
        color: #666;
        font-style: italic;
        margin-top: 0.5rem;
        font-size: 0.9rem;
        background: rgba(76, 175, 80, 0.1);
        padding: 0.3rem;
        border-radius: 20px;
    }
    
    /* tampilan legenda */
    .legend-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-top: 15px;
    }
    
    .legend-section {
        flex: 1;
        min-width: 200px;
    }
    
    .legend-title {
        font-weight: bold;
        color: #2E7D32;
        margin-bottom: 10px;
        font-size: 16px;
    }
    
    /* Style untuk fungsi tanaman */
    .fungsi-card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4CAF50;
        transition: transform 0.2s;
    }
    
    .fungsi-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .fungsi-title {
        color: #2E7D32;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.8rem;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 0.3rem;
    }
    
    .tanaman-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        max-height: 300px;
        overflow-y: auto;
        padding: 0.5rem;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        background-color: #fafafa;
    }
    
    .tanaman-list:hover {
        overflow-y: auto;
    }
    
    .tanaman-badge {
        background: #E8F5E9;
        color: #2E7D32;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid #4CAF50;
        cursor: help;
        transition: all 0.2s;
    }
    
    .tanaman-badge:hover {
        background: #4CAF50;
        color: white;
        transform: scale(1.05);
    }
    
    /* Scrollbar styling */
    .tanaman-list::-webkit-scrollbar {
        width: 8px;
    }
    
    .tanaman-list::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .tanaman-list::-webkit-scrollbar-thumb {
        background: #4CAF50;
        border-radius: 10px;
    }
    
    .tanaman-list::-webkit-scrollbar-thumb:hover {
        background: #2E7D32;
    }
    
    /* Style untuk legenda */
    .legend-item {
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    /* Style untuk 3D map container */
    .map-3d-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
        background: #f0f0f0;
        min-height: 600px;
        position: relative;
    }
    
    /* Style untuk iframe Sketchfab */
    .sketchfab-embed-wrapper {
        position: relative;
        width: 100%;
        height: 0;
        padding-bottom: 56.25%; /* 16:9 Aspect Ratio */
        overflow: hidden;
        border-radius: 10px;
    }
    
    .sketchfab-embed-wrapper iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
    }
    
    .sketchfab-credit {
        text-align: center;
        font-size: 12px;
        margin-top: 8px;
        color: #666;
    }
    
    .sketchfab-credit a {
        color: #1CAAD9;
        text-decoration: none;
        font-weight: bold;
    }
    
    .sketchfab-credit a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Header dengan background gambar
st.markdown("""
<div class="main-header">
    <h1>🌿 WebGIS Resiliensi Kesehatan Terhadap Potensi Bencana Bromo - Kaldera Tengger - Semeru Melalui Konsumsi Tanaman Herbal</h1>
    <p>Taman Nasional Bromo Tengger Semeru (TNBTS) • 86 Spesies Tanaman • 41 Desa</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header-new">
        <h3>🏔️ Bromo - Tengger - Semeru</h3>
        <p>Saat Matahari Terbit</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Gambar dengan caption
    st.image("https://adipandang.wordpress.com/wp-content/uploads/2026/03/3ffcb908-4978-4464-bf12-178125ad26ec.jpg",
             use_container_width=True)
    st.markdown('<p class="image-caption" style="color: white !important;">Team Ekspedisi Penelitian</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Menu navigasi dengan radio button
    st.markdown("### 📋 Menu Navigasi")
    
    menu_options = ["Peta Sebaran", "Peta 3D Pegunungan", "Data Tanaman", "Statistik", "Informasi"]
    menu_icons = ["🗺️", "🏔️", "📋", "📊", "ℹ️"]
    
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed",
        key="menu_radio"
    )
    
    st.markdown("---")
    
    # Filter
    st.markdown("### 🔍 Filter Data")
    
    # Data tanaman untuk filter
    semua_tanaman = [
        'Adas', 'Ajeran putih', 'Alang-alang', 'Andong', 'Awar-awar',
        'Bakung', 'Bawang merah', 'Bawang putih', 'Beluntas', 'Bidara laut',
        'Buah klandingan', 'Bunga hariang', 'Bunga Matahari', 'Calingan', 'Cemplukan',
        'Daun dadap', 'Dringu', 'Ganjan', 'Ganyong', 'Jahe',
        'Jambu wer', 'Jarak', 'Jarak merah', 'Jenggot wesi', 'Jenis Talas',
        'Kayu Ampet', 'Kayu putih', 'Keladi tikus', 'Keladi/sente-sentean', 'Kencana Ungu',
        'Kencur', 'Keningar', 'Kesimbukan', 'Kunyit', 'Lengkuas',
        'Lili-lilian liar', 'Lobak', 'Lombok terong', 'Lombok udel', 'Paitan',
        'Pakis', 'Pakis (fern)', 'Pakis/paku pedang', 'Paku rane/paku kawat', 'Paku sigung',
        'Parijoto', 'Pecut kuda', 'Pisang', 'Pulosari', 'Purwoceng',
        'Air kuncup kecubung gunung', 'Akar sempretan', 'Daun kancing-kancing/semanggi liar', 
        'Daun-daunan hutan mirip garutan', 'Ranti', 'Rumput asystasia', 'Rumput hutan',
        'Rumput karpet', 'Rumput teki-tekian (nutrush)', 'Tumbuhan herba bawah (Amischotolype)',
        'Sawi ireng', 'Semanggi', 'Sengganen/Senggani', 'Sirih', 'Snikir',
        'Stroberi tengger', 'Suplir', 'Suri pandak', 'Tapak liman', 'Teklan',
        'Tepung otot', 'Tirem', 'Trabasan', 'Vervain', 'Wedusan',
        'Ketumbar', 'Teh-tehan', 'Cemara besi', 'Simbaran', 'Kenikir',
        'Tumbuhan herba bawah (Commelina)', 'Rumput ilalang', 'Paku sarang burung', 'Anggrek tanah', 'Jahe merah',
        'Cemara gunung'
    ]
    
    selected_tanaman = st.multiselect(
        "Pilih Nama Tanaman", 
        options=["Semua"] + sorted(semua_tanaman),
        default=["Semua"],
        help="Pilih satu atau lebih tanaman untuk ditampilkan di peta"
    )
    
    st.markdown("---")
    
    # Layer control
    st.markdown("### 🗂️ Layer Control")
    
    col1, col2 = st.columns(2)
    with col1:
        show_desa_geojson = st.checkbox("🏘️ Batas Desa", value=True)
    with col2:
        show_tanaman = st.checkbox("🌿 Tanaman", value=True)
    
    # Kontrol untuk iframe Sketchfab
    st.markdown("### 🏔️ Kontrol Tampilan 3D")
    
    map_height_3d = st.slider("Tinggi Iframe", 400, 800, 600, step=50)
    
    st.markdown("---")
    
    # Status file
    st.markdown("### 📁 Status File")
    
    status_container = st.container()
    with status_container:
        if os.path.exists('Desa_TNBTS.geojson'):
            file_size = os.path.getsize('Desa_TNBTS.geojson') / 1024
            st.markdown(f"""
            <div class="status-badge">
                ✅ <b>Desa_TNBTS.geojson</b><br>
                <small>{file_size:.1f} KB • 41 desa</small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-badge" style="border-left-color: #f44336;">
                ❌ <b>Desa_TNBTS.geojson</b><br>
                <small>File tidak ditemukan</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="status-badge">
            🌿 <b>Database Tanaman</b><br>
            <small>86 spesies teridentifikasi</small>
        </div>
        """, unsafe_allow_html=True)

# Load data functions
@st.cache_data
def load_tanaman_herbal_data():
    # Daftar nama tanaman (86 spesies)
    nama_tanaman = [
        'Adas', 'Ajeran putih', 'Alang-alang', 'Andong', 'Awar-awar',
        'Bakung', 'Bawang merah', 'Bawang putih', 'Beluntas', 'Bidara laut',
        'Buah klandingan', 'Bunga hariang', 'Bunga Matahari', 'Calingan', 'Cemplukan',
        'Daun dadap', 'Dringu', 'Ganjan', 'Ganyong', 'Jahe',
        'Jambu wer', 'Jarak', 'Jarak merah', 'Jenggot wesi', 'Jenis Talas',
        'Kayu Ampet', 'Kayu putih', 'Keladi tikus', 'Keladi/sente-sentean', 'Kencana Ungu',
        'Kencur', 'Keningar', 'Kesimbukan', 'Kunyit', 'Lengkuas',
        'Lili-lilian liar', 'Lobak', 'Lombok terong', 'Lombok udel', 'Paitan',
        'Pakis', 'Pakis (fern)', 'Pakis/paku pedang', 'Paku rane/paku kawat', 'Paku sigung',
        'Parijoto', 'Pecut kuda', 'Pisang', 'Pulosari', 'Purwoceng',
        'Air kuncup kecubung gunung', 'Akar sempretan', 'Daun kancing-kancing/semanggi liar', 
        'Daun-daunan hutan mirip garutan', 'Ranti', 'Rumput asystasia', 'Rumput hutan',
        'Rumput karpet', 'Rumput teki-tekian (nutrush)', 'Tumbuhan herba bawah (Amischotolype)',
        'Sawi ireng', 'Semanggi', 'Sengganen/Senggani', 'Sirih', 'Snikir',
        'Stroberi tengger', 'Suplir', 'Suri pandak', 'Tapak liman', 'Teklan',
        'Tepung otot', 'Tirem', 'Trabasan', 'Vervain', 'Wedusan',
        'Ketumbar', 'Teh-tehan', 'Cemara besi', 'Simbaran', 'Kenikir',
        'Tumbuhan herba bawah (Commelina)', 'Rumput ilalang', 'Paku sarang burung', 'Anggrek tanah', 'Jahe merah',
        'Cemara gunung'
    ]
    
    nama_latin = [
        'Foeniculum vulgare', 'Bidens pilosa L.', 'Imperata cylindrica L.', 'Cordyline fruticosa Linn', 'Ficus septica Burm.f.',
        'Crinum asiaticium L.', 'Allium cepa L.', 'Allium sativum', 'Pluchea indica', 'Strychnos lucida',
        'Lucas lavandulifolia', 'Begonia', 'Helianthus annuus', 'Centella asiatica L.', 'Physalis minima',
        'Erythrina variegata L.', 'Acorus calamus L.', 'Artemisia vulgaris', 'Canna indica L.', 'Zingiber Officinale Rocs',
        'Prunus persica', 'Jatropha curcas', 'Jatropha curcas L.', 'Usnea Barbata Fries', 'Homalomena sp.',
        'Alstonia macrophylla', 'Melaleuca leucadendra', 'Typhonium flagelliforme', 'Alocasia sp.', 'Ruellia',
        'Kaempferia galanga L.', 'Ageratina sp.', 'Paederia foetida', 'Curcuma domestica Rumph.', 'Alpinia galanga',
        'Molineria sp.', 'Raphanus sativus L.', 'Solanum torvum Sw.', 'Capsicum frutescens L.', 'Tithonia diversifolia',
        'Davallia', 'Phegopteris', 'Nephrolepis sp.', 'Selaginella sp.', 'Didymochlaena',
        'Medinilla speciosa', 'Stachytarpheta sp.', 'Musa paradisiaca', 'Alyxia reinwardtii Blume.', 'Pimpinella pruatjan',
        'Brugmansia candida', 'Mikania cordata', 'Desmodium sp.', 'Stachyphrynium sp.', 'Tinospora crispa L. Miers',
        'Asystasia sp.', 'Oplismenus sp.', 'Axonopus sp.', 'Scleria sp.', 'Amischotolype sp.',
        'Brassica juncea', 'Marsilea crenata', 'Melastoma malabathricum L.', 'Piper betle Linn', 'C. Caudatus',
        'Rubus Idaeus L.', 'Adiantum', 'Plantago mayor Linn.', 'Elephantopus scaber L.', 'Eupatorium riparium',
        'Borreria laevis', 'Chromolaena odoratum', 'Ageratum conyzoides', 'Stachytarpheta mutabilis Vahl', 'Ageratum conyzoides',
        'Coriandrum sativum Linn.', 'Eclipta prostrata Linn.', 'Casuarina junghuhniana Miq.', 'Peperomia sp.', 'Cosmos caudatus Kunth',
        'Commelina sp.', 'Imperata cylindrica', 'Asplenium nidus', 'Spathoglottis plicata', 'Zingiber officinale var. rubrum',
        'Casuarina junghuhniana'
    ]
    
    fungsi_utama = [
        'Pencernaan', 'Antiradang', 'Diuretik', 'Menghentikan pendarahan', 'Antiradang',
        'Mengurangi bengkak', 'Penurun demam', 'Menurunkan tekanan darah', 'Pencernaan', 'Pereda nyeri',
        'Batuk & pilek', 'Batuk', 'Penurun demam', 'Penyembuhan luka', 'Penurun demam',
        'Pereda nyeri', 'Pencernaan', 'Obat luka', 'Pencernaan', 'Pencernaan',
        'Diare', 'Pencahar', 'Obat luka', 'Antibakteri', 'Masuk angin',
        'Sakit perut', 'Masuk angin', 'Antikanker', 'Obat bisul', 'Penurun gula darah',
        'Batuk & pilek', 'Menghentikan pendarahan', 'Menghentikan pendarahan', 'Antiradang', 'Masuk angin',
        'Obat luka', 'Pencernaan', 'Tekanan darah tinggi', 'Menghangatkan tubuh', 'Penurun demam',
        'Pencernaan', 'Pencernaan', 'Diuretik', 'Melancarkan peredaran darah', 'Penyembuhan luka',
        'Kesuburan', 'Penurun demam', 'Diare', 'Batuk & pilek', 'Kesuburan',
        'Pereda nyeri, asma', 'Antiradang, diuretik', 'Anti radang, batuk', 'Obat luka', 'Antimalaria',
        'Anti radang', 'Anti radang', 'Obat luka', 'Diuretik', 'Obat luka',
        'Pencernaan', 'Melancarkan peredaran darah', 'Obat diare', 'Antiseptik', 'Penyembuhan luka',
        'Kesehatan darah', 'Batuk, darah tinggi', 'Penyembuhan luka', 'Penurun demam', 'Obat demam',
        'Pereda nyeri otot', 'Sakit perut', 'Obat luka', 'Penurun demam', 'Obat luka',
        'Pencernaan', 'Kesehatan hati', 'Penyembuhan luka', 'Penyembuhan luka', 'Antioksidan',
        'Obat luka', 'Diuretik', 'Obat luka', 'Antioksidan', 'Antiradang',
        'Penyembuhan luka'
    ]
    
    jenis = [
        'Herba', 'Herba', 'Rumput', 'Pohon', 'Pohon',
        'Herba', 'Herba', 'Herba', 'Semak', 'Pohon',
        'Pohon', 'Bunga', 'Bunga', 'Herba', 'Herba',
        'Pohon', 'Herba', 'Herba', 'Herba', 'Herba',
        'Pohon', 'Pohon', 'Pohon', 'Lumut', 'Herba',
        'Pohon', 'Pohon', 'Herba', 'Herba', 'Herba',
        'Herba', 'Herba', 'Herba', 'Herba', 'Herba',
        'Herba', 'Herba', 'Herba', 'Herba', 'Herba',
        'Pakis', 'Pakis', 'Pakis', 'Pakis', 'Pakis',
        'Herba', 'Herba', 'Pohon', 'Herba', 'Herba',
        'Perdu', 'Herba', 'Herba', 'Herba', 'Herba',
        'Herba', 'Rumput', 'Rumput', 'Rumput', 'Herba',
        'Herba', 'Pakis', 'Semak', 'Semak', 'Herba',
        'Perdu', 'Pakis', 'Herba', 'Herba', 'Herba',
        'Herba', 'Semak', 'Herba', 'Herba', 'Herba',
        'Herba', 'Herba', 'Pohon', 'Herba', 'Herba',
        'Herba', 'Rumput', 'Pakis', 'Bunga', 'Herba',
        'Pohon'
    ]
    
    lokasi = [
        'RPTN Jemplang, Senduro', 'Seluruh TNBTS', 'RPTN Patok Picis', 'RPTN Patok Picis', 'Desa Ngadas, Ranupani',
        'RPTN Patok Picis', 'Seluruh TNBTS', 'Seluruh TNBTS', 'RPTN Patok Picis', 'RPTN Senduro',
        'Desa Ngadas, Ranupani', 'RPTN Senduro', 'RPTN Patok Picis', 'Desa Argosari, Ngadas', 'Desa Argosari, Ngadas',
        'Desa Argosari, Ngadas', 'RPTN Ranu Darungan', 'RPTN Jemplang', 'RPTN Patok Picis, Senduro', 'Seluruh TNBTS',
        'Desa Argosari, Ngadas', 'RPTN Senduro', 'Desa Ngadas, Argosari', 'Desa Argosari, Ngadas', 'RPTN Ranu Darungan',
        'RPTN Jemplang', 'Desa Ranupani', 'RPTN Patok Picis', 'RPTN Ranu Darungan', 'RPTN Senduro',
        'Seluruh TNBTS', 'RPTN Ranu Darungan, Senduro', 'Seluruh TNBTS', 'Seluruh TNBTS', 'RPTN Patok Picis',
        'RPTN Ranu Darungan', 'Seluruh TNBTS', 'Desa Ranupani, Argosari', 'Desa Ranupani, Argosari', 'RPTN Jemplang',
        'RPTN Senduro', 'RPTN Senduro', 'RPTN Ranu Darungan, Senduro', 'RPTN Ranu Darungan', 'RPTN Senduro',
        'RPTN Pasrujambe', 'RPTN Ranu Darungan', 'RPTN Jemplang', 'Desa Ngadas, Ranupani', 'RPTN Ranupani, Senduro',
        'Blok Ireng-ireng, RPTN Senduro', 'Desa Ngadas', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'Desa Ngadas, Ranupani',
        'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan, Blok Ireng-ireng', 'RPTN Ranu Darungan',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'RPTN Patok Picis', 
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Blok Ireng-ireng, RPTN Senduro', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'RPTN Patok Picis', 'RPTN Patok Picis',
        'Desa Ngadas, RPTN Jemplang', 'Desa Ngadas, RPTN Jemplang', 'Desa Ngadas, RPTN Jemplang', 'RPTN Patok Picis', 'RPTN Patok Picis, Desa Ngadas, RPTN Jemplang',
        'Seluruh TNBTS', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Desa Ngadas, Cemoro Lawang, Ranupani, Argosari', 
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Desa Ngadas, Desa Cemoro Lawang',
        'RPTN Ranu Darungan', 'Seluruh TNBTS', 'RPTN Patok Picis', 'Desa Ranupani, Argosari', 'Seluruh TNBTS',
        'Seluruh TNBTS'
    ]
    
    desa = [
        'Argosari, Gubuklakah', 'Seluruh desa', 'Ngadas, Argosari', 'Tidak ada data', 'Ngadas, Ranupani',
        'Tidak ada data', 'Seluruh desa', 'Seluruh desa', 'Tidak ada data', 'Blok Ireng-ireng',
        'Ngadas, Ranupani', 'Blok Ireng-ireng', 'Tidak ada data', 'Argosari, Gubuklakah', 'Argosari, Gubuklakah',
        'Argosari, Gubuklakah', 'Argosari, Gubuklakah', 'Ngadas', 'Argosari, Gubuklakah', 'Seluruh desa',
        'Argosari, Gubuklakah', 'Blok Ireng-ireng', 'Ngadas, Argosari', 'Argosari, Gubuklakah', 'Tidak ada data',
        'Ngadas', 'Ranupani', 'Tidak ada data', 'Tidak ada data', 'Blok Ireng-ireng',
        'Seluruh desa', 'Blok Ireng-ireng', 'Seluruh desa', 'Seluruh desa', 'Tidak ada data',
        'Tidak ada data', 'Seluruh desa', 'Ranupani, Argosari', 'Ranupani, Argosari', 'Ngadas',
        'Blok Ireng-ireng', 'Blok Ireng-ireng', 'Blok Ireng-ireng', 'Tidak ada data', 'Blok Ireng-ireng',
        'Tidak ada data', 'Tidak ada data', 'Ngadas', 'Ngadas, Ranupani', 'Tidak ada data',
        'Tidak ada data', 'Ngadas', 'Tidak ada data', 'Tidak ada data', 'Ngadas, Ranupani',
        'Tidak ada data', 'Tidak ada data', 'Tidak ada data', 'Tidak ada data', 'Tidak ada data',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Tidak ada data',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Tidak ada data', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Tidak ada data', 'Tidak ada data',
        'Ngadas', 'Ngadas', 'Ngadas', 'Tidak ada data', 'Tidak ada data',
        'Seluruh desa', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Ngadas, Cemoro Lawang, Ranupani, Argosari',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Ngadas, Cemoro Lawang',
        'Tidak ada data', 'Seluruh desa', 'Tidak ada data', 'Ranupani, Argosari', 'Seluruh desa',
        'Seluruh desa'
    ]
    
    latitude = [
        -8.0333, -7.9500, -7.9167, -7.9167, -7.9400,
        -7.9167, -7.9500, -7.9500, -7.9167, -7.9250,
        -7.9400, -7.9250, -7.9167, -7.9400, -7.9400,
        -7.9400, -8.0167, -8.0333, -7.9167, -7.9500,
        -7.9400, -7.9250, -7.9400, -7.9400, -8.0167,
        -8.0333, -7.9333, -7.9167, -8.0167, -7.9250,
        -7.9500, -8.0167, -7.9500, -7.9500, -7.9167,
        -8.0167, -7.9500, -7.9333, -7.9333, -8.0333,
        -7.9250, -7.9250, -8.0167, -8.0167, -7.9250,
        -8.0833, -8.0167, -8.0333, -7.9400, -7.9333,
        -7.9250, -7.9400, -8.0167, -8.0167, -7.9400,
        -8.0167, -8.0167, -8.0167, -8.0167, -8.0167,
        -7.9400, -7.9400, -7.9400, -7.9167, -7.9400,
        -7.9400, -7.9250, -7.9400, -7.9167, -7.9167,
        -8.0333, -8.0333, -8.0333, -7.9167, -7.9167,
        -7.9500, -7.9400, -7.9400, -7.9400, -7.9400,
        -8.0167, -7.9500, -7.9167, -7.9333, -7.9500,
        -7.9500
    ]
    
    longitude = [
        113.0167, 112.9750, 112.9167, 112.9167, 112.9500,
        112.9167, 112.9750, 112.9750, 112.9167, 112.9550,
        112.9500, 112.9550, 112.9167, 112.9650, 112.9650,
        112.9650, 112.9833, 113.0000, 112.9167, 112.9750,
        112.9650, 112.9550, 112.9500, 112.9650, 112.9833,
        113.0000, 112.9500, 112.9167, 112.9833, 112.9550,
        112.9750, 112.9833, 112.9750, 112.9750, 112.9167,
        112.9833, 112.9750, 112.9500, 112.9500, 113.0000,
        112.9550, 112.9550, 112.9833, 112.9833, 112.9550,
        113.0333, 112.9833, 113.0000, 112.9750, 112.9500,
        112.9550, 112.9500, 112.9833, 112.9833, 112.9500,
        112.9833, 112.9833, 112.9833, 112.9833, 112.9833,
        112.9500, 112.9500, 112.9500, 112.9167, 112.9500,
        112.9500, 112.9550, 112.9500, 112.9167, 112.9167,
        113.0000, 113.0000, 113.0000, 112.9167, 112.9167,
        112.9750, 112.9500, 112.9500, 112.9500, 112.9500,
        112.9833, 112.9750, 112.9167, 112.9500, 112.9750,
        112.9750
    ]
    
    ketinggian = [
        1800, 2000, 1700, 1700, 2100,
        1700, 1900, 1900, 1700, 2000,
        2100, 2000, 1700, 2300, 2300,
        2300, 1900, 1800, 1700, 2000,
        2300, 2000, 2100, 2300, 1900,
        1800, 2200, 1700, 1900, 2000,
        2000, 1900, 2000, 2000, 1700,
        1900, 2000, 2200, 2200, 1800,
        2000, 2000, 1900, 1900, 2000,
        1700, 1900, 1800, 2100, 2200,
        2000, 2100, 1900, 1900, 2100,
        1900, 1900, 1900, 1900, 1900,
        2300, 2300, 2300, 1700, 2300,
        2300, 2000, 2300, 1700, 1700,
        1800, 1800, 1800, 1700, 1700,
        2000, 2300, 2300, 2300, 2300,
        1900, 1700, 1700, 2200, 2000,
        2000
    ]
    
    # Buat DataFrame
    df = pd.DataFrame({
        'id': list(range(1, 87)),
        'nama_tanaman': nama_tanaman,
        'nama_latin': nama_latin,
        'fungsi_utama': fungsi_utama,
        'jenis': jenis,
        'lokasi': lokasi,
        'desa': desa,
        'latitude': latitude,
        'longitude': longitude,
        'ketinggian': ketinggian
    })
    
    # kolom status konservasi
    df['status_konservasi'] = 'Umum'
    
    # Tanaman yang dilindungi
    tanaman_dilindungi = ['Purwoceng', 'Parijoto', 'Anggrek']
    for tanaman in tanaman_dilindungi:
        mask = df['nama_tanaman'].str.contains(tanaman, case=False, na=False)
        df.loc[mask, 'status_konservasi'] = 'Dilindungi'
    
    # kolom jumlah (estimasi)
    np.random.seed(42)
    df['jumlah'] = np.random.randint(10, 500, len(df))
    
    return df

@st.cache_data
def load_desa_geojson():
    """
    Memuat data desa dari file GeoJSON Desa_TNBTS.geojson
    """
    try:
        if not os.path.exists('Desa_TNBTS.geojson'):
            st.sidebar.error("❌ File Desa_TNBTS.geojson tidak ditemukan!")
            return gpd.GeoDataFrame()
        
        with open('Desa_TNBTS.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
        gdf.crs = "EPSG:4326"
        
        return gdf
        
    except Exception as e:
        st.sidebar.error(f"❌ Error loading GeoJSON: {e}")
        return gpd.GeoDataFrame()

# Load data
df_tanaman = load_tanaman_herbal_data()
gdf_desa = load_desa_geojson()

# Filter data tanaman
if "Semua" not in selected_tanaman and selected_tanaman:
    df_tanaman_filtered = df_tanaman[df_tanaman['nama_tanaman'].isin(selected_tanaman)]
else:
    df_tanaman_filtered = df_tanaman.copy()

# Fungsi untuk membuat peta
def create_tnbts_map():
    center_lat = -7.940
    center_lon = 112.950
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap',
        attr='OpenStreetMap contributors',
        name='OpenStreetMap'
    )
    
    # Tambahkan layer tile lainnya
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satelit'
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        attr='OpenTopoMap',
        name='Terrain'
    ).add_to(m)
    
    # Layer Desa
    if show_desa_geojson and not gdf_desa.empty:
        desa_group = folium.FeatureGroup(name='🏘️ Batas Desa')
        
        def style_function(feature):
            return {
                'fillColor': '#ffeda0',
                'color': '#f03b20',
                'weight': 2,
                'fillOpacity': 0.3
            }
        
        def highlight_function(feature):
            return {
                'fillColor': '#ffffb3',
                'color': '#bd0026',
                'weight': 3,
                'fillOpacity': 0.6
            }
        
        available_fields = []
        field_aliases = []
        
        if 'nama_kelur' in gdf_desa.columns:
            available_fields.append('nama_kelur')
            field_aliases.append('Desa:')
        if 'nama_kecam' in gdf_desa.columns:
            available_fields.append('nama_kecam')
            field_aliases.append('Kecamatan:')
        if 'nama_kabko' in gdf_desa.columns:
            available_fields.append('nama_kabko')
            field_aliases.append('Kabupaten:')
        if 'jumlah_pen' in gdf_desa.columns:
            available_fields.append('jumlah_pen')
            field_aliases.append('Penduduk:')
        
        folium.GeoJson(
            gdf_desa,
            name='Desa',
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=available_fields,
                aliases=field_aliases,
                localize=True,
                sticky=False
            ),
            popup=folium.GeoJsonPopup(
                fields=['nama_kelur', 'nama_kecam', 'nama_kabko', 'kode', 'jumlah_pen'],
                aliases=['Desa', 'Kecamatan', 'Kabupaten', 'Kode', 'Jumlah Penduduk'],
                localize=True,
                max_width=300
            )
        ).add_to(desa_group)
        
        desa_group.add_to(m)
    
    # Layer Tanaman
    if show_tanaman and not df_tanaman_filtered.empty:
        tanaman_group = folium.FeatureGroup(name='🌿 Tanaman Herbal')
        
        warna = {
            'Pohon': 'green', 
            'Semak': 'lightgreen', 
            'Perdu': 'lightgreen',
            'Herba': 'cadetblue',
            'Bunga': 'pink', 
            'Rumput': 'beige', 
            'Pakis': 'darkgreen', 
            'Lumut': 'lightgray'
        }
        
        for _, row in df_tanaman_filtered.iterrows():
            color = warna.get(row['jenis'], 'blue')
            
            popup_text = f"""
            <div style="font-family: Arial; min-width: 250px;">
                <b style="color: #27ae60; font-size: 16px;">{row['nama_tanaman']}</b><br>
                <i style="color: #7f8c8d;">{row['nama_latin']}</i>
                <hr style="margin: 5px 0;">
                <table style="font-size: 12px;">
                    <tr><td><b>Fungsi:</b></td><td>{row['fungsi_utama']}</td></tr>
                    <tr><td><b>Jenis:</b></td><td>{row['jenis']}</td></tr>
                    <tr><td><b>Lokasi:</b></td><td>{row['lokasi']}</td></tr>
                    <tr><td><b>Desa:</b></td><td>{row['desa']}</td></tr>
                    <tr><td><b>Status:</b></td><td>{row['status_konservasi']}</td></tr>
                    <tr><td><b>Ketinggian:</b></td><td>{row['ketinggian']} mdpl</td></tr>
                </table>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=row['nama_tanaman'],
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.8,
                weight=2
            ).add_to(tanaman_group)
        tanaman_group.add_to(m)
    
    folium.LayerControl().add_to(m)
    
    try:
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
    except:
        pass
    
    try:
        from folium.plugins import MeasureControl
        MeasureControl(
            position='bottomleft',
            primary_length_unit='kilometers',
            secondary_length_unit='meters'
        ).add_to(m)
    except:
        pass
    
    return m

# Halaman Peta Sebaran
if selected == "Peta Sebaran":
    st.markdown("## 🗺️ Peta Interaktif Tanaman Herbal TNBTS")
    st.markdown("Visualisasi sebaran 86 spesies tanaman herbal di kawasan TNBTS")
    
    # Metric cards dengan desain yang lebih baik
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(gdf_desa)}</h3>
            <p>🏘️ Total Desa</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(df_tanaman_filtered)}</h3>
            <p>🌿 Total Tanaman</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if not gdf_desa.empty and 'jumlah_pen' in gdf_desa.columns:
            total_penduduk = gdf_desa['jumlah_pen'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_penduduk:,}</h3>
                <p>👥 Total Penduduk</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>0</h3>
                <p>👥 Total Penduduk</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if not gdf_desa.empty:
            total_kecamatan = gdf_desa['nama_kecam'].nunique() if 'nama_kecam' in gdf_desa.columns else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total_kecamatan}</h3>
                <p>🗺️ Kecamatan</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>0</h3>
                <p>🗺️ Kecamatan</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Buat dan tampilkan peta
    try:
        m = create_tnbts_map()
        folium_static(m, width=1200, height=600)
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Menampilkan peta sederhana...")
        m = folium.Map(location=[-7.940, 112.950], zoom_start=10)
        folium_static(m)
    
    # Legenda dalam expander
    with st.expander("📖 Legenda Peta"):
        st.markdown("""
        ### 🗺️ Legenda Peta
        
        **🏘️ Batas Desa:** Polygon kuning dengan garis batas merah
        - Klik pada polygon untuk melihat informasi desa
        
        **🌿 Tanaman Herbal:** Marker berwarna berdasarkan jenis:
        - 🟢 **Hijau**: Pohon
        - 🟢 **Hijau muda**: Semak/Perdu  
        - 🔵 **Biru muda**: Herba
        - 💗 **Pink**: Bunga
        - 🟤 **Hijau tua**: Pakis
        - ⚪ **Abu-abu**: Lumut
        - 🟡 **Kuning**: Rumput
        
        **🛠️ Tools Peta:**
        - Gunakan layer control untuk memilih tampilan (Satelit, OpenStreetMap, Terrain)
        - Klik Fullscreen untuk layar penuh
        - Gunakan Measure Tool untuk mengukur jarak
        """)

# Halaman Peta 3D Pegunungan
elif selected == "Peta 3D Pegunungan":
    st.markdown("## 🏔️ Peta 3D Pegunungan TNBTS ")
    st.markdown("Visualisasi 3D interaktif pegunungan Bromo Tengger Semeru - Putar 360° dengan mouse/touch")
    
    # Informasi singkat
    st.info("""
    **🖱️ Cara menggunakan:**
    - **Putar 360°**: Klik kiri + drag ke segala arah
    - **Zoom**: Gulir mouse atau gunakan gesture pinch
    - **Fullscreen**: Klik ikon layar penuh di pojok kanan bawah
    - **Navigasi**: Gunakan kontrol di pojok kanan bawah untuk mode tur
    """)
    
    # Pilihan tampilan
    st.markdown("### 🌋 Model 3D Gunung Bromo dan Kaldera Tengger")
    
    # Tampilkan iframe Sketchfab
    with st.spinner("Memuat model 3D dari Sketchfab..."):
        st.markdown(f"""
        <div class="map-3d-container" style="height: {map_height_3d}px;">
            <div class="sketchfab-embed-wrapper" style="height: 100%; padding-bottom: 0;">
                <iframe 
                    title="Mount Bromo / Bromo Tengger Semeru National Park" 
                    frameborder="0" 
                    allowfullscreen 
                    mozallowfullscreen="true" 
                    webkitallowfullscreen="true" 
                    allow="autoplay; fullscreen; xr-spatial-tracking" 
                    xr-spatial-tracking 
                    execution-while-out-of-viewport 
                    execution-while-not-rendered 
                    web-share 
                    src="https://sketchfab.com/models/72f1c983ba4040eab89d75eb2b0d3e32/embed"
                    style="width: 100%; height: 100%; border: none; border-radius: 10px;">
                </iframe>
            </div>
        </div>
        """, unsafe_allow_html=True)
            
    # Statistik peta 3D
    st.markdown("### 📊 Statistik Kawasan TNBTS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>5</h3>
            <p>⛰️ Gunung</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>41</h3>
            <p>🏘️ Desa</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>86</h3>
            <p>🌿 Spesies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>3,676</h3>
            <p>📏 Tertinggi (mdpl)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Informasi tentang model
    with st.expander("ℹ️ Tentang Model 3D", expanded=False):
        st.markdown("""
        ### Tentang Model 3D Sketchfab
        
        Model 3D ini menampilkan **Gunung Bromo dan Kaldera Tengger** dengan detail:
        
        - **Gunung Bromo** (2.329 mdpl) - gunung berapi aktif
        - **Gunung Batok** (2.470 mdpl) - gunung non-aktif
        - **Gunung Kursi** (2.351 mdpl)
        - **Gunung Widodaren** (2.250 mdpl)
        - **Kaldera Tengger** - kawah raksasa dengan diameter 8-10 km
        - **Lautan Pasir** - hamparan pasir vulkanik seluas 5.250 hektar
        """)
    
    # Tips penggunaan
    with st.expander("🎮 Tips Navigasi 3D", expanded=False):
        st.markdown("""
        ### Tips Navigasi Model 3D
        
        **Kontrol Dasar:**
        - **Rotasi**: Klik kiri + drag
        - **Zoom**: Gulir mouse atau pinch gesture
        - **Pan**: Klik kanan + drag atau shift + drag
        
        **Kontrol Lanjutan:**
        - **Fullscreen**: Klik ikon layar penuh di pojok kanan bawah
        - **Reset View**: Klik ikon rumah
        - **Mode Tur**: Klik ikon joystick untuk mode tur otomatis
        - **VR Mode**: Jika tersedia, gunakan ikon VR untuk pengalaman realitas virtual
        
        **Tips:**
        - Gunakan fullscreen untuk pengalaman imersif
        - Putar model untuk melihat semua sisi gunung
        - Zoom in untuk melihat detail kaldera dan lautan pasir
        """)

# Halaman Data Tanaman
elif selected == "Data Tanaman":
    st.markdown("## 📋 Data Tanaman Herbal TNBTS")
    st.markdown("Database 86 spesies tanaman herbal yang teridentifikasi")
    
    tab1, tab2 = st.tabs(["🌿 Tanaman (86 Spesies)", "🏘️ Data Desa (GeoJSON)"])
    
    with tab1:
        search = st.text_input("🔍 Cari tanaman:", key="search", placeholder="Masukkan nama tanaman, fungsi, atau nama latin...")
        
        if search:
            df_search = df_tanaman_filtered[
                df_tanaman_filtered['nama_tanaman'].str.contains(search, case=False) |
                df_tanaman_filtered['fungsi_utama'].str.contains(search, case=False) |
                df_tanaman_filtered['nama_latin'].str.contains(search, case=False)
            ]
            st.info(f"Ditemukan {len(df_search)} hasil pencarian")
        else:
            df_search = df_tanaman_filtered
        
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        st.dataframe(
            df_search[['nama_tanaman', 'nama_latin', 'fungsi_utama', 'jenis', 'lokasi', 'status_konservasi']], 
            use_container_width=True, 
            height=500,
            column_config={
                "nama_tanaman": "Nama Tanaman",
                "nama_latin": "Nama Latin",
                "fungsi_utama": "Fungsi Utama",
                "jenis": "Jenis",
                "lokasi": "Lokasi",
                "status_konservasi": "Status"
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        csv = df_tanaman_filtered.to_csv(index=False)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                "📥 Download CSV Tanaman (86 Spesies)", 
                data=csv, 
                file_name="tanaman_herbal_tnbts_86.csv", 
                mime="text/csv",
                use_container_width=True
            )
    
    with tab2:
        st.markdown("### 📊 Data Desa dari File GeoJSON")
        
        if not gdf_desa.empty:
            st.success(f"✅ Total {len(gdf_desa)} desa berhasil dimuat")
            
            # Statistik desa
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{len(gdf_desa)}</h3>
                    <p>Total Desa</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if 'jumlah_pen' in gdf_desa.columns:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['jumlah_pen'].sum():,}</h3>
                        <p>Total Penduduk</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                if 'nama_kecam' in gdf_desa.columns:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['nama_kecam'].nunique()}</h3>
                        <p>Jumlah Kecamatan</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col4:
                if 'nama_kabko' in gdf_desa.columns:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['nama_kabko'].nunique()}</h3>
                        <p>Jumlah Kabupaten</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Tabel data desa
            st.markdown("### 📋 Tabel Data Desa")
            desa_df = gdf_desa.drop('geometry', axis=1) if 'geometry' in gdf_desa.columns else gdf_desa
            
            if 'jumlah_pen' in desa_df.columns:
                desa_df['jumlah_pen'] = desa_df['jumlah_pen'].apply(lambda x: f"{x:,}")
            
            st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
            st.dataframe(desa_df, use_container_width=True, height=500)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download data desa
            csv_desa = desa_df.to_csv(index=False)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    "📥 Download Data Desa (CSV)", 
                    data=csv_desa, 
                    file_name="data_desa_tnbts.csv", 
                    mime="text/csv",
                    use_container_width=True
                )
            
            # Informasi GeoJSON
            with st.expander("ℹ️ Informasi File GeoJSON", expanded=False):
                st.json({
                    "jumlah_fitur": len(gdf_desa),
                    "kolom_tersedia": list(gdf_desa.columns),
                    "sistem_koordinat": str(gdf_desa.crs),
                    "bounding_box": {
                        "min_x": gdf_desa.total_bounds[0],
                        "min_y": gdf_desa.total_bounds[1],
                        "max_x": gdf_desa.total_bounds[2],
                        "max_y": gdf_desa.total_bounds[3]
                    }
                })
        else:
            st.error("❌ Data desa tidak dapat dimuat. Pastikan file Desa_TNBTS.geojson tersedia.")
            
            st.info("📁 File dalam direktori saat ini:")
            files = os.listdir('.')
            for f in files:
                if f.endswith('.geojson'):
                    st.write(f"- {f}")

# Halaman Statistik
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal dan Desa")
    st.markdown("Analisis data sebaran tanaman herbal dan demografi desa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌿 Statistik Tanaman")
        if not df_tanaman_filtered.empty:
            # Fungsi tanaman
            st.markdown("**Fungsi Utama Tanaman (Top 10)**")
            fungsi_counts = df_tanaman_filtered['fungsi_utama'].value_counts().head(10)
            st.bar_chart(fungsi_counts, use_container_width=True)
            
            # Status konservasi
            st.markdown("**Status Konservasi**")
            status_counts = df_tanaman_filtered['status_konservasi'].value_counts()
            
            # Custom display untuk status
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                dilindungi = status_counts.get('Dilindungi', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{dilindungi}</h3>
                    <p>🔒 Dilindungi</p>
                </div>
                """, unsafe_allow_html=True)
            with col_stat2:
                umum = status_counts.get('Umum', 0)
                st.markdown(f"""
                <div class="metric-card">
                    <h3>{umum}</h3>
                    <p>🌿 Umum</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Total spesies
            st.markdown("**Total Spesies**")
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(df_tanaman_filtered)}</h3>
                <p>Spesies Tanaman</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Statistik Desa")
        if not gdf_desa.empty:
            # Distribusi desa per kecamatan
            if 'nama_kecam' in gdf_desa.columns:
                st.markdown("**Jumlah Desa per Kecamatan**")
                kecamatan_counts = gdf_desa['nama_kecam'].value_counts()
                st.bar_chart(kecamatan_counts, use_container_width=True)
            
            # Distribusi penduduk
            if 'jumlah_pen' in gdf_desa.columns:
                st.markdown("**Statistik Penduduk**")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['jumlah_pen'].mean():,.0f}</h3>
                        <p>Rata-rata</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_stats2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['jumlah_pen'].min():,}</h3>
                        <p>Minimum</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col_stats3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>{gdf_desa['jumlah_pen'].max():,}</h3>
                        <p>Maximum</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Statistik jenis tanaman
    st.markdown("### 📊 Jenis Tanaman")
    if not df_tanaman_filtered.empty:
        jenis_counts = df_tanaman_filtered['jenis'].value_counts()
        
        # Tampilkan dalam bentuk bar chart
        st.bar_chart(jenis_counts, use_container_width=True)
        
        # Tampilkan dalam tabel
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            jenis_df = pd.DataFrame({
                'Jenis': jenis_counts.index,
                'Jumlah': jenis_counts.values
            })
            st.dataframe(jenis_df, use_container_width=True, hide_index=True)
        
        # Statistik ketinggian
        st.markdown("### 📊 Ketinggian Tanaman")
        ketinggian_stats = df_tanaman_filtered['ketinggian'].describe()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{ketinggian_stats['min']:.0f}</h3>
                <p>Min (mdpl)</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{ketinggian_stats['max']:.0f}</h3>
                <p>Max (mdpl)</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{ketinggian_stats['mean']:.0f}</h3>
                <p>Rata-rata (mdpl)</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{ketinggian_stats['std']:.0f}</h3>
                <p>Std Dev (mdpl)</p>
            </div>
            """, unsafe_allow_html=True)

# Halaman Informasi
else:
    st.markdown("## ℹ️ Informasi TNBTS")
    
    # Hitung statistik
    total_penduduk = gdf_desa['jumlah_pen'].sum() if not gdf_desa.empty and 'jumlah_pen' in gdf_desa.columns else 0
    total_kecamatan = gdf_desa['nama_kecam'].nunique() if not gdf_desa.empty and 'nama_kecam' in gdf_desa.columns else 0
    total_kabupaten = gdf_desa['nama_kabko'].nunique() if not gdf_desa.empty and 'nama_kabko' in gdf_desa.columns else 0
    tanaman_dilindungi = len(df_tanaman[df_tanaman['status_konservasi'] == 'Dilindungi'])
    
    # Header informasi
    st.markdown("""
    <div class="info-box">
        <h3>🌋 Taman Nasional Bromo Tengger Semeru</h3>
        <p>Taman Nasional Bromo Tengger Semeru (TNBTS) adalah kawasan konservasi yang terletak di Jawa Timur, Indonesia. 
        Kawasan ini memiliki keanekaragaman hayati yang tinggi, termasuk berbagai spesies tanaman herbal yang 
        dimanfaatkan oleh masyarakat sekitar untuk pengobatan tradisional.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Statistik dalam tabel yang lebih menarik
    st.markdown("### 📊 Data dan Statistik")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background-color: #4CAF50; color: white;">
                <th style="padding: 10px; border-radius: 5px 0 0 0;">Kategori</th>
                <th style="padding: 10px; border-radius: 0 5px 0 0;">Jumlah</th>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">🏘️ Desa</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{}</b> desa</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">🗺️ Kecamatan</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{}</b> kecamatan</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">🗺️ Kabupaten</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{}</b> kabupaten</td>
            </tr>
        </table>
        """.format(len(gdf_desa), total_kecamatan, total_kabupaten), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <table style="width:100%; border-collapse: collapse;">
            <tr style="background-color: #4CAF50; color: white;">
                <th style="padding: 10px; border-radius: 5px 0 0 0;">Kategori</th>
                <th style="padding: 10px; border-radius: 0 5px 0 0;">Jumlah</th>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">👥 Penduduk</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{:,}</b> jiwa</td>
            </tr>
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">🌿 Tanaman Herbal</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{}</b> spesies</td>
            </tr>
            <tr style="background-color: #f5f5f5;">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">🔒 Tanaman Dilindungi</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{}</b> spesies</td>
            </tr>
        </table>
        """.format(total_penduduk, len(df_tanaman), tanaman_dilindungi), unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Fungsi utama tanaman dengan nama tanamannya
    st.markdown("### 💊 Fungsi Utama Tanaman")
    
    # Kelompokkan fungsi
    fungsi_pencernaan = ['Pencernaan', 'Diare', 'Sakit perut', 'Masuk angin']
    fungsi_antiradang = ['Antiradang', 'Anti radang', 'Anti radang, batuk', 'Antiradang, diuretik']
    fungsi_penurun_demam = ['Penurun demam', 'Obat demam']
    fungsi_pereda_nyeri = ['Pereda nyeri', 'Pereda nyeri, asma', 'Pereda nyeri otot']
    fungsi_obat_luka = ['Obat luka', 'Penyembuhan luka', 'Menghentikan pendarahan', 'Obat bisul']
    fungsi_batuk = ['Batuk & pilek', 'Batuk', 'Batuk, darah tinggi']
    fungsi_lainnya = ['Diuretik', 'Antiseptik', 'Kesuburan', 'Antikanker', 'Antibakteri', 
                     'Menurunkan tekanan darah', 'Tekanan darah tinggi', 'Penurun gula darah',
                     'Melancarkan peredaran darah', 'Kesehatan darah', 'Kesehatan hati',
                     'Menghangatkan tubuh', 'Mengurangi bengkak', 'Antimalaria', 'Antioksidan', 'Pencahar']
    
    # Fungsi untuk mendapatkan tanaman berdasarkan fungsi
    def get_tanaman_by_fungsi(fungsi_list, df):
        tanaman = []
        for fungsi in fungsi_list:
            # Pisahkan jika ada koma
            if ',' in fungsi:
                fungsi_parts = [f.strip() for f in fungsi.split(',')]
                for f in fungsi_parts:
                    tanaman.extend(df[df['fungsi_utama'].str.contains(f, case=False, na=False)]['nama_tanaman'].tolist())
            else:
                tanaman.extend(df[df['fungsi_utama'].str.contains(fungsi, case=False, na=False)]['nama_tanaman'].tolist())
        # Hapus duplikat
        return list(dict.fromkeys(tanaman))
    
    # Buat layout grid untuk fungsi tanaman
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Pencernaan
        tanaman_pencernaan = get_tanaman_by_fungsi(fungsi_pencernaan, df_tanaman)
        tanaman_pencernaan_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_pencernaan])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🫀 Pencernaan ({len(tanaman_pencernaan)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_pencernaan_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Antiradang
        tanaman_antiradang = get_tanaman_by_fungsi(fungsi_antiradang, df_tanaman)
        tanaman_antiradang_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_antiradang])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🔥 Antiradang ({len(tanaman_antiradang)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_antiradang_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Penurun Demam
        tanaman_demam = get_tanaman_by_fungsi(fungsi_penurun_demam, df_tanaman)
        tanaman_demam_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_demam])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🤒 Penurun Demam ({len(tanaman_demam)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_demam_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Pereda Nyeri
        tanaman_nyeri = get_tanaman_by_fungsi(fungsi_pereda_nyeri, df_tanaman)
        tanaman_nyeri_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_nyeri])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">💊 Pereda Nyeri ({len(tanaman_nyeri)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_nyeri_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Obat Luka
        tanaman_luka = get_tanaman_by_fungsi(fungsi_obat_luka, df_tanaman)
        tanaman_luka_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_luka])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🩹 Obat Luka ({len(tanaman_luka)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_luka_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Batuk & Pilek
        tanaman_batuk = get_tanaman_by_fungsi(fungsi_batuk, df_tanaman)
        tanaman_batuk_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_batuk])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🌡️ Batuk & Pilek ({len(tanaman_batuk)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_batuk_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Fungsi Lainnya
        tanaman_lainnya = get_tanaman_by_fungsi(fungsi_lainnya, df_tanaman)
        tanaman_lainnya_html = "".join([f'<span class="tanaman-badge" title="{df_tanaman[df_tanaman["nama_tanaman"]==t]["fungsi_utama"].values[0] if len(df_tanaman[df_tanaman["nama_tanaman"]==t])>0 else ""}">{t}</span>' for t in tanaman_lainnya])
        
        st.markdown(f"""
        <div class="fungsi-card">
            <div class="fungsi-title">🌿 Fungsi Lainnya ({len(tanaman_lainnya)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_lainnya_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tanaman Dilindungi
        tanaman_dilindungi_list = df_tanaman[df_tanaman['status_konservasi'] == 'Dilindungi']['nama_tanaman'].tolist()
        tanaman_dilindungi_html = "".join([f'<span class="tanaman-badge" style="background: #FFEBEE; color: #c62828; border-color: #c62828;" title="Status Dilindungi">{t}</span>' for t in tanaman_dilindungi_list])
        
        st.markdown(f"""
        <div class="fungsi-card" style="border-left-color: #f44336;">
            <div class="fungsi-title">🔒 Tanaman Dilindungi ({len(tanaman_dilindungi_list)} spesies)</div>
            <div class="tanaman-list">
                {tanaman_dilindungi_html}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Informasi tambahan tentang fungsi
    st.info("💡 **Tips:** Arahkan kursor ke nama tanaman untuk melihat fungsi spesifiknya. Scroll pada setiap kotak untuk melihat semua tanaman. Klik pada peta untuk melihat detail lengkap tanaman.")
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Tim peneliti dengan foto
    st.markdown("### 👥 Tim Peneliti")
    
    # Baris pertama (3 orang)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="team-card">
            <img src="https://prasetya.ub.ac.id/wp-content/uploads/2023/10/BU-TYAS-405x270.jpg" 
                 class="team-photo"
                 alt="Dr Eng Turniningtyas Ayu R."
                 onerror="this.src='https://via.placeholder.com/150?text=Dr.+Turniningtyas'">
            <h4 class="team-name">Dr Eng Turniningtyas Ayu R.</h4>
            <p class="team-title">ST., MT</p>
            <p class="team-role">Ketua Tim</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="team-card">
            <img src="https://img.inews.co.id/files/networks/2022/11/03/e9d8d_prof-sasmito-djati.jpg" 
                 class="team-photo"
                 alt="Prof.Dr.Ir. Moch. Sasmito Djati"
                 onerror="this.src='https://via.placeholder.com/150?text=Prof.+Sasmito+Djati'">
            <h4 class="team-name">Prof.Dr.Ir. Moch. Sasmito Djati</h4>
            <p class="team-title">M.S.</p>
            <p class="team-role">Pakar Tanaman Herbal</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="team-card">
            <img src="https://i1.rgstatic.net/ii/profile.image/296334033735682-1447662947469_Q512/Adipandang-Yudono.jpg" 
                 class="team-photo"
                 alt="Adipandang Yudono"
                 onerror="this.src='https://via.placeholder.com/150?text=Adipandang+Yudono'">
            <h4 class="team-name">Adipandang Yudono</h4>
            <p class="team-title">S.Si., M.U.R.P., Ph.D</p>
            <p class="team-role">Pakar GIS dan WebGIS Analytics</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Baris kedua (1 orang di tengah)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="team-card">
            <img src="https://file-filkom.ub.ac.id/fileupload/assets/uploads/foto/crop/arief_andy_soebroto.jpg" 
                 class="team-photo"
                 alt="Dr. Ir. Arief Andy Soebroto"
                 onerror="this.src='https://via.placeholder.com/150?text=Dr.+Arief+Andy'">
            <h4 class="team-name">Dr. Ir. Arief Andy Soebroto</h4>
            <p class="team-title">ST.,M.Kom.</p>
            <p class="team-role">Pakar Pembangunan Platform AI dan IoT</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Sumber data
    st.markdown("### 📍 Sumber Data")
    st.markdown("""
    <ul>
        <li><b>Data Desa:</b> File GeoJSON dari BIG/BPS (41 desa)</li>
        <li><b>Data Tanaman:</b> Hasil penelitian Tim Peneliti UB (2026) - 86 spesies</li>
        <li><b>Peta Basemap:</b> OpenStreetMap, Esri World Imagery (Satelit), OpenTopoMap</li>
        <li><b>Peta 3D:</b> Model 3D dari Sketchfab oleh smartmAPPS</li>
    </ul>
    """, unsafe_allow_html=True)

# Footer dengan background gambar
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">🌿 WebGIS Resiliensi Kesehatan Terhadap Potensi Bencana Bromo-Kaldera Tengger-Semeru Melalui Konsumsi Tanaman Herbal di TNBTS</p>
    <p style="margin-bottom: 0.5rem;">© Ekspedisi Tanaman Herbal di Kawasan Taman Nasional Bromo Tengger Semeru untuk Health Security pada Masyarakat Terdampak Letusan Gunung Bromo - 2026</p>
    <p style="font-size: 0.9rem; opacity: 0.9;">Distribusi Spasial Tanaman Herbal di TNBTS • 86 Spesies • 41 Desa</p>
    <p style="font-size: 0.5rem; opacity: 0.5;">© Credit: Scrypt & WebGIS Developer - Adipandang Yudono (2026)</p>
</div>
""", unsafe_allow_html=True)
