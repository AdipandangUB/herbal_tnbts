import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import json
import os

# Konfigurasi halaman - HARUS menjadi perintah Streamlit pertama
st.set_page_config(
    page_title="WebGIS Tanaman TNBTS",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi session state untuk menyimpan status
if 'menu_selected' not in st.session_state:
    st.session_state.menu_selected = "Peta Sebaran"

# Custom CSS untuk memperbaiki tampilan
st.markdown("""
<style>
    /* Memperbaiki header dan title */
    .main-header {
        background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.2rem;
    }
    
    .main-header p {
        color: #E8F5E9;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Memperbaiki tampilan sidebar */
    .css-1d391kg {
        background-color: #f5f5f5;
    }
    
    .sidebar-header {
        background-color: #2E7D32;
        padding: 1rem;
        border-radius: 5px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Memperbaiki tampilan metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #2E7D32;
        margin-bottom: 1rem;
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
    
    /* Memperbaiki tampilan tabs */
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
    
    /* Memperbaiki tampilan expander */
    .streamlit-expanderHeader {
        background-color: #f5f5f5;
        border-radius: 5px;
    }
    
    /* Memperbaiki tampilan dataframe */
    .dataframe-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        background: white;
    }
    
    /* Memperbaiki tampilan footer */
    .footer {
        background: linear-gradient(135deg, #2E7D32 0%, #1B5E20 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-top: 2rem;
    }
    
    .footer a {
        color: #FFD700;
        text-decoration: none;
    }
    
    .footer a:hover {
        text-decoration: underline;
    }
    
    /* Memperbaiki tampilan badges untuk legenda */
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
    
    /* Memperbaiki tampilan divider */
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent, #4CAF50, transparent);
        margin: 2rem 0;
    }
    
    /* Memperbaiki tampilan image caption */
    .image-caption {
        text-align: center;
        font-style: italic;
        color: #666;
        margin-top: 0.3rem;
        font-size: 0.9rem;
    }
    
    /* Memperbaiki tampilan button */
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
    
    /* Memperbaiki tampilan download button */
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
    
    /* Memperbaiki tampilan info boxes */
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
    
    /* Memperbaiki tampilan status badges di sidebar */
    .status-badge {
        background: white;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.3rem 0;
        border-left: 3px solid #4CAF50;
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
    
    /* Memperbaiki tampilan legenda */
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
    
    /* Styling untuk fungsi tanaman */
    .fungsi-container {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        background-color: #fafafa;
    }
    
    .fungsi-item {
        margin-bottom: 15px;
        padding: 10px;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .fungsi-item:last-child {
        border-bottom: none;
    }
    
    .fungsi-header {
        background-color: #4CAF50;
        color: white;
        padding: 8px 12px;
        border-radius: 5px;
        margin-bottom: 10px;
        font-weight: bold;
    }
    
    .tanaman-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .tanaman-tag {
        background-color: #e8f5e9;
        color: #2E7D32;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        border: 1px solid #c8e6c9;
    }
</style>
""", unsafe_allow_html=True)

# Header dengan desain yang lebih menarik
st.markdown("""
<div class="main-header">
    <h1>🌿 WebGIS Sebaran Tanaman Herbal</h1>
    <p>Taman Nasional Bromo Tengger Semeru (TNBTS) • 86 Spesies Tanaman • 41 Desa</p>
</div>
""", unsafe_allow_html=True)

# Sidebar dengan desain yang lebih baik
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h3>🌋 Bromo Tengger Semeru</h3>
        <p>Taman Nasional</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Gambar dengan caption
    st.image("https://www.journeyera.com/wp-content/uploads/2018/11/mount-bromo-without-a-tour-king-kong-hill-0600.jpg",
             use_container_width=True)
    st.markdown('<p class="image-caption">Gunung Bromo saat sunrise</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Menu navigasi dengan radio button yang lebih rapi
    st.markdown("### 📋 Menu Navigasi")
    
    menu_options = ["Peta Sebaran", "Data Tanaman", "Statistik", "Informasi", "Fungsi Tanaman"]
    menu_icons = ["🗺️", "📋", "📊", "ℹ️", "💊"]
    
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed",
        key="menu_radio"
    )
    
    st.markdown("---")
    
    # Filter dengan desain yang lebih baik
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
    
    # Layer control dengan desain yang lebih baik
    st.markdown("### 🗂️ Layer Control")
    
    col1, col2 = st.columns(2)
    with col1:
        show_desa_geojson = st.checkbox("🏘️ Batas Desa", value=True)
    with col2:
        show_tanaman = st.checkbox("🌿 Tanaman", value=True)
    
    st.markdown("---")
    
    # Status file dengan desain yang lebih baik
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

# Load data
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
    
    # Tambahkan kolom status konservasi
    df['status_konservasi'] = 'Umum'
    
    # Tanaman yang dilindungi
    tanaman_dilindungi = ['Purwoceng', 'Parijoto', 'Anggrek']
    for tanaman in tanaman_dilindungi:
        mask = df['nama_tanaman'].str.contains(tanaman, case=False, na=False)
        df.loc[mask, 'status_konservasi'] = 'Dilindungi'
    
    # Tambahkan kolom jumlah (estimasi)
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

# Fungsi untuk mendapatkan tanaman berdasarkan fungsi
@st.cache_data
def get_tanaman_by_fungsi():
    df = load_tanaman_herbal_data()
    
    # Kategorisasi fungsi
    kategori_fungsi = {
        'Pencernaan': ['Pencernaan', 'Diare', 'Sakit perut', 'Masuk angin', 'Pencahar'],
        'Antiradang & Nyeri': ['Antiradang', 'Pereda nyeri', 'Pereda nyeri otot', 'Pereda nyeri, asma', 'Anti radang', 'Anti radang, batuk', 'Antiradang, diuretik'],
        'Demam & Batuk': ['Penurun demam', 'Obat demam', 'Batuk & pilek', 'Batuk', 'Batuk, darah tinggi'],
        'Luka & Pendarahan': ['Obat luka', 'Penyembuhan luka', 'Menghentikan pendarahan', 'Obat bisul'],
        'Kardiovaskular & Darah': ['Menurunkan tekanan darah', 'Tekanan darah tinggi', 'Melancarkan peredaran darah', 'Kesehatan darah'],
        'Lainnya': ['Diuretik', 'Antiseptik', 'Kesuburan', 'Antikanker', 'Antibakteri', 
                   'Penurun gula darah', 'Kesehatan hati', 'Menghangatkan tubuh', 
                   'Mengurangi bengkak', 'Antimalaria', 'Antioksidan']
    }
    
    hasil = {}
    
    for kategori, keywords in kategori_fungsi.items():
        tanaman_list = []
        for keyword in keywords:
            if '&' in keyword:
                keyword_parts = keyword.replace('&', '|')
                mask = df['fungsi_utama'].str.contains(keyword_parts, case=False, na=False)
            else:
                mask = df['fungsi_utama'].str.contains(keyword, case=False, na=False)
            tanaman = df[mask]['nama_tanaman'].tolist()
            tanaman_list.extend(tanaman)
        
        # Hapus duplikat
        tanaman_list = list(dict.fromkeys(tanaman_list))
        hasil[kategori] = {
            'jumlah': len(tanaman_list),
            'tanaman': sorted(tanaman_list)
        }
    
    return hasil

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
elif selected == "Informasi":
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
    
    # Tim peneliti dengan foto
    st.markdown("### 👥 Tim Peneliti")
    
    # Baris pertama (3 orang)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="team-card">
            <img src="https://prasetya.ub.ac.id/wp-content/uploads/2023/10/BU-TYAS-405x270-1.jpg" 
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
    </ul>
    """, unsafe_allow_html=True)

# Halaman Fungsi Tanaman (BARU)
elif selected == "Fungsi Tanaman":
    st.markdown("## 💊 Fungsi Utama Tanaman Herbal TNBTS")
    st.markdown("Klasifikasi tanaman berdasarkan fungsi pengobatan tradisional")
    
    # Metric cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>86</h3>
            <p>🌿 Total Spesies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>6</h3>
            <p>💊 Kategori Fungsi</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        tanaman_dilindungi = len(df_tanaman[df_tanaman['status_konservasi'] == 'Dilindungi'])
        st.markdown(f"""
        <div class="metric-card">
            <h3>{tanaman_dilindungi}</h3>
            <p>🔒 Dilindungi</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Dapatkan data tanaman berdasarkan fungsi
    fungsi_data = get_tanaman_by_fungsi()
    
    # Tampilkan dalam tab
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🫀 Pencernaan", 
        "🔥 Antiradang & Nyeri", 
        "🤒 Demam & Batuk",
        "🩹 Luka & Pendarahan",
        "❤️ Kardiovaskular",
        "🌿 Lainnya"
    ])
    
    with tab1:
        data = fungsi_data['Pencernaan']
        st.markdown(f"""
        <div class="fungsi-header">
            🫀 Fungsi Pencernaan - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman yang berkhasiat untuk mengatasi masalah pencernaan seperti diare, sakit perut, masuk angin, dan melancarkan pencernaan.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        data = fungsi_data['Antiradang & Nyeri']
        st.markdown(f"""
        <div class="fungsi-header">
            🔥 Fungsi Antiradang & Pereda Nyeri - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman yang berkhasiat untuk mengatasi peradangan, mengurangi rasa nyeri, dan sakit otot.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        data = fungsi_data['Demam & Batuk']
        st.markdown(f"""
        <div class="fungsi-header">
            🤒 Fungsi Penurun Demam & Batuk - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman yang berkhasiat untuk menurunkan demam, mengatasi batuk, pilek, dan masalah pernapasan.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    with tab4:
        data = fungsi_data['Luka & Pendarahan']
        st.markdown(f"""
        <div class="fungsi-header">
            🩹 Fungsi Penyembuhan Luka & Menghentikan Pendarahan - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman yang berkhasiat untuk menyembuhkan luka, menghentikan pendarahan, dan mengobati bisul.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    with tab5:
        data = fungsi_data['Kardiovaskular & Darah']
        st.markdown(f"""
        <div class="fungsi-header">
            ❤️ Fungsi Kardiovaskular & Kesehatan Darah - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman yang berkhasiat untuk mengatur tekanan darah, melancarkan peredaran darah, dan menjaga kesehatan jantung.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    with tab6:
        data = fungsi_data['Lainnya']
        st.markdown(f"""
        <div class="fungsi-header">
            🌿 Fungsi Lainnya - {data['jumlah']} Spesies
        </div>
        """, unsafe_allow_html=True)
        st.markdown("Tanaman dengan berbagai fungsi lainnya seperti diuretik, antiseptik, kesuburan, antikanker, dan antioksidan.")
        
        # Tampilkan dalam grid
        tanaman_list = data['tanaman']
        cols = st.columns(3)
        for i, tanaman in enumerate(tanaman_list):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="tanaman-tag" style="margin-bottom: 8px; text-align: center;">
                    {tanaman}
                </div>
                """, unsafe_allow_html=True)
    
    # Ringkasan fungsi
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📊 Ringkasan Fungsi Tanaman")
    
    ringkasan_df = pd.DataFrame({
        'Kategori Fungsi': list(fungsi_data.keys()),
        'Jumlah Spesies': [data['jumlah'] for data in fungsi_data.values()]
    })
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(ringkasan_df.set_index('Kategori Fungsi'), use_container_width=True)
    with col2:
        st.dataframe(ringkasan_df, use_container_width=True, hide_index=True)

# Footer yang lebih menarik
st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="footer">
    <p style="font-size: 1.2rem; margin-bottom: 0.5rem;">🌿 WebGIS Sebaran Tanaman Herbal TNBTS</p>
    <p style="margin-bottom: 0.5rem;">© 2026 Tim Peneliti Universitas Brawijaya</p>
    <p style="font-size: 0.9rem; opacity: 0.9;">Distribusi Spasial Tanaman Herbal di TNBTS • 86 Spesies • 41 Desa</p>
    <p style="font-size: 0.8rem; margin-top: 1rem; opacity: 0.7;">
        <a href="#" style="color: #FFD700;">Tentang</a> • 
        <a href="#" style="color: #FFD700;">Kontak</a> • 
        <a href="#" style="color: #FFD700;">Dokumentasi</a>
    </p>
</div>
""", unsafe_allow_html=True)
