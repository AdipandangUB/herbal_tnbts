import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import folium_static
import json
import os

# Konfigurasi halaman
st.set_page_config(
    page_title="WebGIS Tanaman TNBTS",
    page_icon="🌿",
    layout="wide"
)

# Title dan deskripsi aplikasi
st.title("🌿 WebGIS Sebaran Tanaman Herbal - Taman Nasional Bromo Tengger Semeru")
st.markdown("---")

# Sidebar untuk navigasi dan filter
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Mount_Bromo_at_sunrise.jpg/800px-Mount_Bromo_at_sunrise.jpg", 
             caption="Taman Nasional Bromo Tengger Semeru")
    
    st.header("📋 Menu Navigasi")
    
    menu_options = ["Peta Sebaran", "Data Tanaman", "Statistik", "Informasi"]
    menu_icons = ["🗺️", "📋", "📊", "ℹ️"]
    
    selected = st.radio(
        "Pilih Menu:",
        menu_options,
        format_func=lambda x: f"{menu_icons[menu_options.index(x)]} {x}",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.header("🔍 Filter Data")
    
    # Filter berdasarkan nama tanaman (86 spesies)
    semua_tanaman = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Air kuncup kecubung gunung', 'Akar sempretan', 'Daun kancing-kancing/semanggi liar', 
        'Daun-daunan hutan mirip garutan', 'Ranti', 'Rumput asystasia', 'Rumput hutan',
        'Rumput karpet', 'Rumput teki-tekian (nutrush)', 'Tumbuhan herba bawah (Amischotolype)',
        # 20 spesies tambahan batch 2 (61-80)
        'Sawi ireng', 'Semanggi', 'Sengganen/Senggani', 'Sirih', 'Snikir',
        'Stroberi tengger', 'Suplir', 'Suri pandak', 'Tapak liman', 'Teklan',
        'Tepung otot', 'Tirem', 'Trabasan', 'Vervain', 'Wedusan',
        'Ketumbar', 'Teh-tehan', 'Cemara besi', 'Simbaran', 'Kenikir',
        # 5 spesies tambahan batch 3 (81-85)
        'Tumbuhan herba bawah (Commelina)', 'Rumput ilalang', 'Paku sarang burung', 'Anggrek tanah', 'Jahe merah',
        # 1 spesies tambahan batch 4 (86)
        'Cemara gunung'
    ]
    
    selected_tanaman = st.multiselect(
        "Pilih Nama Tanaman", 
        options=["Semua"] + sorted(semua_tanaman),
        default=["Semua"]
    )
    
    st.markdown("---")
    st.header("🗂️ Layer Control")
    
    # Pilihan layer yang akan ditampilkan
    show_desa_geojson = st.checkbox("Tampilkan Batas Desa", value=True)
    show_tanaman = st.checkbox("Tampilkan Sebaran Tanaman", value=True)
    
    # Tampilkan informasi file
    st.markdown("---")
    st.caption(f"File GeoJSON: Desa_TNBTS.geojson")
    if os.path.exists('Desa_TNBTS.geojson'):
        st.caption("✅ File ditemukan")
    else:
        st.caption("❌ File tidak ditemukan")

# Data tanaman herbal TNBTS - 86 spesies
@st.cache_data
def load_tanaman_herbal_data():
    # Daftar nama tanaman (86 spesies)
    nama_tanaman = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Air kuncup kecubung gunung', 'Akar sempretan', 'Daun kancing-kancing/semanggi liar', 
        'Daun-daunan hutan mirip garutan', 'Ranti', 'Rumput asystasia', 'Rumput hutan',
        'Rumput karpet', 'Rumput teki-tekian (nutrush)', 'Tumbuhan herba bawah (Amischotolype)',
        # 20 spesies tambahan batch 2 (61-80)
        'Sawi ireng', 'Semanggi', 'Sengganen/Senggani', 'Sirih', 'Snikir',
        'Stroberi tengger', 'Suplir', 'Suri pandak', 'Tapak liman', 'Teklan',
        'Tepung otot', 'Tirem', 'Trabasan', 'Vervain', 'Wedusan',
        'Ketumbar', 'Teh-tehan', 'Cemara besi', 'Simbaran', 'Kenikir',
        # 5 spesies tambahan batch 3 (81-85)
        'Tumbuhan herba bawah (Commelina)', 'Rumput ilalang', 'Paku sarang burung', 'Anggrek tanah', 'Jahe merah',
        # 1 spesies tambahan batch 4 (86)
        'Cemara gunung'
    ]
    
    # Daftar nama latin (86 spesies)
    nama_latin = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Brugmansia candida', 'Mikania cordata', 'Desmodium sp.', 'Stachyphrynium sp.', 'Tinospora crispa L. Miers',
        'Asystasia sp.', 'Oplismenus sp.', 'Axonopus sp.', 'Scleria sp.', 'Amischotolype sp.',
        # 20 spesies tambahan batch 2 (61-80)
        'Brassica juncea', 'Marsilea crenata', 'Melastoma malabathricum L.', 'Piper betle Linn', 'C. Caudatus',
        'Rubus Idaeus L.', 'Adiantum', 'Plantago mayor Linn.', 'Elephantopus scaber L.', 'Eupatorium riparium',
        'Borreria laevis', 'Chromolaena odoratum', 'Ageratum conyzoides', 'Stachytarpheta mutabilis Vahl', 'Ageratum conyzoides',
        'Coriandrum sativum Linn.', 'Eclipta prostrata Linn.', 'Casuarina junghuhniana Miq.', 'Peperomia sp.', 'Cosmos caudatus Kunth',
        # 5 spesies tambahan batch 3 (81-85)
        'Commelina sp.', 'Imperata cylindrica', 'Asplenium nidus', 'Spathoglottis plicata', 'Zingiber officinale var. rubrum',
        # 1 spesies tambahan batch 4 (86)
        'Casuarina junghuhniana'
    ]
    
    # Daftar fungsi utama (86 spesies)
    fungsi_utama = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Pereda nyeri, asma', 'Antiradang, diuretik', 'Anti radang, batuk', 'Obat luka', 'Antimalaria',
        'Anti radang', 'Anti radang', 'Obat luka', 'Diuretik', 'Obat luka',
        # 20 spesies tambahan batch 2 (61-80)
        'Pencernaan', 'Melancarkan peredaran darah', 'Obat diare', 'Antiseptik', 'Penyembuhan luka',
        'Kesehatan darah', 'Batuk, darah tinggi', 'Penyembuhan luka', 'Penurun demam', 'Obat demam',
        'Pereda nyeri otot', 'Sakit perut', 'Obat luka', 'Penurun demam', 'Obat luka',
        'Pencernaan', 'Kesehatan hati', 'Penyembuhan luka', 'Penyembuhan luka', 'Antioksidan',
        # 5 spesies tambahan batch 3 (81-85)
        'Obat luka', 'Diuretik', 'Obat luka', 'Antioksidan', 'Antiradang',
        # 1 spesies tambahan batch 4 (86)
        'Penyembuhan luka'
    ]
    
    # Daftar jenis (86 spesies)
    jenis = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Perdu', 'Herba', 'Herba', 'Herba', 'Herba',
        'Herba', 'Rumput', 'Rumput', 'Rumput', 'Herba',
        # 20 spesies tambahan batch 2 (61-80)
        'Herba', 'Pakis', 'Semak', 'Semak', 'Herba',
        'Perdu', 'Pakis', 'Herba', 'Herba', 'Herba',
        'Herba', 'Semak', 'Herba', 'Herba', 'Herba',
        'Herba', 'Herba', 'Pohon', 'Herba', 'Herba',
        # 5 spesies tambahan batch 3 (81-85)
        'Herba', 'Rumput', 'Pakis', 'Bunga', 'Herba',
        # 1 spesies tambahan batch 4 (86)
        'Pohon'
    ]
    
    # Daftar lokasi (86 spesies)
    lokasi = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Blok Ireng-ireng, RPTN Senduro', 'Desa Ngadas', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'Desa Ngadas, Ranupani',
        'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan', 'RPTN Ranu Darungan, Blok Ireng-ireng', 'RPTN Ranu Darungan',
        # 20 spesies tambahan batch 2 (61-80)
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'RPTN Patok Picis', 
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Blok Ireng-ireng, RPTN Senduro', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'RPTN Patok Picis', 'RPTN Patok Picis',
        'Desa Ngadas, RPTN Jemplang', 'Desa Ngadas, RPTN Jemplang', 'Desa Ngadas, RPTN Jemplang', 'RPTN Patok Picis', 'RPTN Patok Picis, Desa Ngadas, RPTN Jemplang',
        'Seluruh TNBTS', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Desa Ngadas, Cemoro Lawang, Ranupani, Argosari', 
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Desa Ngadas, Desa Cemoro Lawang',
        # 5 spesies tambahan batch 3 (81-85)
        'RPTN Ranu Darungan', 'Seluruh TNBTS', 'RPTN Patok Picis', 'Desa Ranupani, Argosari', 'Seluruh TNBTS',
        # 1 spesies tambahan batch 4 (86)
        'Seluruh TNBTS'
    ]
    
    # Daftar desa (86 spesies)
    desa = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        'Tidak ada data', 'Ngadas', 'Tidak ada data', 'Tidak ada data', 'Ngadas, Ranupani',
        'Tidak ada data', 'Tidak ada data', 'Tidak ada data', 'Tidak ada data', 'Tidak ada data',
        # 20 spesies tambahan batch 2 (61-80)
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Tidak ada data',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo',
        'Tidak ada data', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Tidak ada data', 'Tidak ada data',
        'Ngadas', 'Ngadas', 'Ngadas', 'Tidak ada data', 'Tidak ada data',
        'Seluruh desa', 'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Ngadas, Cemoro Lawang, Ranupani, Argosari',
        'Argosari, Gubuklakah, Ngadas, Ngadisari, Wonokitri, Mororejo', 'Ngadas, Cemoro Lawang',
        # 5 spesies tambahan batch 3 (81-85)
        'Tidak ada data', 'Seluruh desa', 'Tidak ada data', 'Ranupani, Argosari', 'Seluruh desa',
        # 1 spesies tambahan batch 4 (86)
        'Seluruh desa'
    ]
    
    # Daftar latitude (86 spesies)
    latitude = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        -7.9250, -7.9400, -8.0167, -8.0167, -7.9400,
        -8.0167, -8.0167, -8.0167, -8.0167, -8.0167,
        # 20 spesies tambahan batch 2 (61-80)
        -7.9400, -7.9400, -7.9400, -7.9167, -7.9400,
        -7.9400, -7.9250, -7.9400, -7.9167, -7.9167,
        -8.0333, -8.0333, -8.0333, -7.9167, -7.9167,
        -7.9500, -7.9400, -7.9400, -7.9400, -7.9400,
        # 5 spesies tambahan batch 3 (81-85)
        -8.0167, -7.9500, -7.9167, -7.9333, -7.9500,
        # 1 spesies tambahan batch 4 (86)
        -7.9500
    ]
    
    # Daftar longitude (86 spesies)
    longitude = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        112.9550, 112.9500, 112.9833, 112.9833, 112.9500,
        112.9833, 112.9833, 112.9833, 112.9833, 112.9833,
        # 20 spesies tambahan batch 2 (61-80)
        112.9500, 112.9500, 112.9500, 112.9167, 112.9500,
        112.9500, 112.9550, 112.9500, 112.9167, 112.9167,
        113.0000, 113.0000, 113.0000, 112.9167, 112.9167,
        112.9750, 112.9500, 112.9500, 112.9500, 112.9500,
        # 5 spesies tambahan batch 3 (81-85)
        112.9833, 112.9750, 112.9167, 112.9500, 112.9750,
        # 1 spesies tambahan batch 4 (86)
        112.9750
    ]
    
    # Daftar ketinggian (86 spesies)
    ketinggian = [
        # 50 spesies awal
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
        # 10 spesies tambahan batch 1 (51-60)
        2000, 2100, 1900, 1900, 2100,
        1900, 1900, 1900, 1900, 1900,
        # 20 spesies tambahan batch 2 (61-80)
        2300, 2300, 2300, 1700, 2300,
        2300, 2000, 2300, 1700, 1700,
        1800, 1800, 1800, 1700, 1700,
        2000, 2300, 2300, 2300, 2300,
        # 5 spesies tambahan batch 3 (81-85)
        1900, 1700, 1700, 2200, 2000,
        # 1 spesies tambahan batch 4 (86)
        2000
    ]
    
    # Verifikasi panjang semua list (debug)
    print(f"Panjang list - nama_tanaman: {len(nama_tanaman)}")
    print(f"Panjang list - nama_latin: {len(nama_latin)}")
    print(f"Panjang list - fungsi_utama: {len(fungsi_utama)}")
    print(f"Panjang list - jenis: {len(jenis)}")
    print(f"Panjang list - lokasi: {len(lokasi)}")
    print(f"Panjang list - desa: {len(desa)}")
    print(f"Panjang list - latitude: {len(latitude)}")
    print(f"Panjang list - longitude: {len(longitude)}")
    print(f"Panjang list - ketinggian: {len(ketinggian)}")
    
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

# Fungsi untuk load data desa dari file GeoJSON lengkap
@st.cache_data
def load_desa_geojson():
    """
    Memuat data desa dari file GeoJSON Desa_TNBTS.geojson
    File ini berisi 39 desa di sekitar TNBTS
    """
    try:
        # Cek apakah file exists
        if not os.path.exists('Desa_TNBTS.geojson'):
            st.error("File Desa_TNBTS.geojson tidak ditemukan!")
            return gpd.GeoDataFrame()
        
        # Baca file GeoJSON
        with open('Desa_TNBTS.geojson', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        
        # Konversi ke GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
        gdf.crs = "EPSG:4326"  # Set CRS ke WGS84
        
        # Tampilkan informasi jumlah desa
        st.sidebar.success(f"✅ Loaded {len(gdf)} desa dari GeoJSON")
        
        return gdf
        
    except Exception as e:
        st.error(f"Error loading GeoJSON: {e}")
        return gpd.GeoDataFrame()

# Load data tanaman herbal
df_tanaman = load_tanaman_herbal_data()

# Load data desa dari file GeoJSON
gdf_desa = load_desa_geojson()

# Filter data tanaman
if "Semua" not in selected_tanaman and selected_tanaman:
    df_tanaman_filtered = df_tanaman[df_tanaman['nama_tanaman'].isin(selected_tanaman)]
else:
    df_tanaman_filtered = df_tanaman.copy()

# Fungsi untuk membuat peta dengan semua layer
def create_tnbts_map():
    # Koordinat pusat TNBTS
    center_lat = -7.940
    center_lon = 112.950
    
    # Buat peta dengan default tiles OpenStreetMap (hanya sekali)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        tiles='OpenStreetMap',
        attr='OpenStreetMap contributors',
        name='OpenStreetMap'  # Beri nama untuk layer control
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
    
    # Layer Desa dari GeoJSON (SEMUA DESA) - TANPA MARKER CENTROID
    if show_desa_geojson and not gdf_desa.empty:
        desa_group = folium.FeatureGroup(name='🏘️ Batas Desa')
        
        # Style untuk polygon desa
        def style_function(feature):
            return {
                'fillColor': '#ffeda0',
                'color': '#f03b20',
                'weight': 2,
                'fillOpacity': 0.3
            }
        
        # Highlight function
        def highlight_function(feature):
            return {
                'fillColor': '#ffffb3',
                'color': '#bd0026',
                'weight': 3,
                'fillOpacity': 0.6
            }
        
        # Tentukan fields untuk tooltip berdasarkan kolom yang tersedia
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
        
        # Tambahkan GeoJSON ke peta
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
        
        # Warna untuk setiap jenis
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
    
    # Tambahkan layer control
    folium.LayerControl().add_to(m)
    
    # Plugin Fullscreen
    try:
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
    except:
        pass
    
    # Tambahkan scale bar
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
    st.header("🗺️ Peta Interaktif Tanaman Herbal TNBTS")
    st.caption("🌍 Default peta menggunakan mode **OpenStreetMap** (dapat diganti ke Satelit atau Terrain)")
    
    # Tampilkan statistik dengan data yang diperbarui sesuai screenshot
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏘️ Total Desa", f"{len(gdf_desa)} desa")
    with col2:
        st.metric("🌿 Total Tanaman", f"{len(df_tanaman_filtered)} spesies")
    with col3:
        if not gdf_desa.empty and 'jumlah_pen' in gdf_desa.columns:
            total_penduduk = gdf_desa['jumlah_pen'].sum()
            st.metric("👥 Total Penduduk", f"{total_penduduk:,}")
    with col4:
        if not gdf_desa.empty:
            total_kecamatan = gdf_desa['nama_kecam'].nunique() if 'nama_kecam' in gdf_desa.columns else 0
            st.metric("🗺️ Kecamatan", f"{total_kecamatan} kecamatan")
    
    # Buat dan tampilkan peta
    try:
        m = create_tnbts_map()
        folium_static(m, width=1200, height=600)
    except Exception as e:
        st.error(f"Error: {e}")
        st.info("Menampilkan peta sederhana...")
        m = folium.Map(location=[-7.940, 112.950], zoom_start=10)
        folium_static(m)
    
    with st.expander("📖 Legenda Peta"):
        st.markdown("""
        ### 🗺️ Legenda Peta
        
        **🏘️ Batas Desa:** Polygon kuning dengan garis batas merah
        - Klik pada polygon untuk melihat informasi desa
        
        **🌿 Tanaman Herbal:** Marker berwarna berdasarkan jenis:
        - 🟢 **Hijau tua**: Pohon
        - 🟢 **Hijau muda**: Semak/Perdu
        - 🔵 **Biru muda**: Herba
        - 💗 **Pink**: Bunga
        - 🟤 **Hijau tua**: Pakis
        - ⚪ **Abu-abu**: Lumut
        - 🟡 **Krem**: Rumput
        
        **🛠️ Tools Peta:**
        - Gunakan layer control (ikon kotak di pojok kanan atas) untuk memilih tampilan peta (OpenStreetMap, Satelit, Terrain)
        - Klik ikon layar penuh (⛶) untuk mode fullscreen
        - Gunakan ikon penggaris di pojok kiri bawah untuk mengukur jarak
        """)

# Halaman Data Tanaman
elif selected == "Data Tanaman":
    st.header("📋 Data Tanaman Herbal TNBTS")
    
    tab1, tab2 = st.tabs(["🌿 Tanaman (86 Spesies)", "🏘️ Data Desa (GeoJSON)"])
    
    with tab1:
        search = st.text_input("🔍 Cari tanaman:", key="search")
        if search:
            df_search = df_tanaman_filtered[
                df_tanaman_filtered['nama_tanaman'].str.contains(search, case=False) |
                df_tanaman_filtered['fungsi_utama'].str.contains(search, case=False) |
                df_tanaman_filtered['nama_latin'].str.contains(search, case=False)
            ]
        else:
            df_search = df_tanaman_filtered
        
        st.dataframe(df_search[['nama_tanaman', 'nama_latin', 'fungsi_utama', 'jenis', 'lokasi', 'status_konservasi']], 
                    use_container_width=True, height=500)
        
        csv = df_tanaman_filtered.to_csv(index=False)
        st.download_button("📥 Download CSV Tanaman (86 Spesies)", data=csv, file_name="tanaman_herbal_tnbts_86.csv", mime="text/csv")
    
    with tab2:
        st.subheader("📊 Data Desa dari File GeoJSON")
        
        if not gdf_desa.empty:
            st.success(f"✅ Total {len(gdf_desa)} desa berhasil dimuat")
            
            # Tampilkan statistik desa
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Desa", len(gdf_desa))
            with col2:
                if 'jumlah_pen' in gdf_desa.columns:
                    st.metric("Total Penduduk", f"{gdf_desa['jumlah_pen'].sum():,}")
            with col3:
                if 'nama_kecam' in gdf_desa.columns:
                    st.metric("Jumlah Kecamatan", gdf_desa['nama_kecam'].nunique())
            with col4:
                if 'nama_kabko' in gdf_desa.columns:
                    st.metric("Jumlah Kabupaten", gdf_desa['nama_kabko'].nunique())
            
            # Tampilkan data desa dalam bentuk tabel
            st.subheader("📋 Tabel Data Desa")
            desa_df = gdf_desa.drop('geometry', axis=1) if 'geometry' in gdf_desa.columns else gdf_desa
            
            # Format angka untuk tampilan
            if 'jumlah_pen' in desa_df.columns:
                desa_df['jumlah_pen'] = desa_df['jumlah_pen'].apply(lambda x: f"{x:,}")
            
            st.dataframe(desa_df, use_container_width=True, height=500)
            
            # Download data desa
            csv_desa = desa_df.to_csv(index=False)
            st.download_button(
                "📥 Download Data Desa (CSV)", 
                data=csv_desa, 
                file_name="data_desa_tnbts.csv", 
                mime="text/csv"
            )
            
            # Tampilkan informasi GeoJSON
            with st.expander("ℹ️ Informasi File GeoJSON"):
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
            
            # Tampilkan daftar file di direktori untuk debugging
            st.info("📁 File dalam direktori saat ini:")
            files = os.listdir('.')
            for f in files:
                if f.endswith('.geojson'):
                    st.write(f"- {f}")

# Halaman Statistik
elif selected == "Statistik":
    st.header("📊 Statistik Tanaman Herbal dan Desa")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌿 Statistik Tanaman (86 Spesies)")
        if not df_tanaman_filtered.empty:
            # Fungsi tanaman
            st.markdown("**Fungsi Utama Tanaman (Top 10)**")
            fungsi_counts = df_tanaman_filtered['fungsi_utama'].value_counts().head(10)
            st.bar_chart(fungsi_counts)
            
            # Status konservasi
            st.markdown("**Status Konservasi**")
            status_counts = df_tanaman_filtered['status_konservasi'].value_counts()
            st.dataframe(status_counts)
            
            # Total tanaman
            st.metric("Total Spesies", len(df_tanaman_filtered))
    
    with col2:
        st.subheader("📊 Statistik Desa")
        if not gdf_desa.empty:
            # Distribusi desa per kecamatan
            if 'nama_kecam' in gdf_desa.columns:
                st.markdown("**Jumlah Desa per Kecamatan**")
                kecamatan_counts = gdf_desa['nama_kecam'].value_counts()
                st.bar_chart(kecamatan_counts)
            
            # Distribusi penduduk
            if 'jumlah_pen' in gdf_desa.columns:
                st.markdown("**Statistik Penduduk**")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Rata-rata", f"{gdf_desa['jumlah_pen'].mean():,.0f}")
                with col_stats2:
                    st.metric("Minimum", f"{gdf_desa['jumlah_pen'].min():,}")
                with col_stats3:
                    st.metric("Maximum", f"{gdf_desa['jumlah_pen'].max():,}")
    
    # Statistik jenis tanaman
    st.subheader("📊 Jenis Tanaman")
    if not df_tanaman_filtered.empty:
        jenis_counts = df_tanaman_filtered['jenis'].value_counts()
        st.dataframe(jenis_counts)
        
        # Statistik ketinggian
        st.subheader("📊 Ketinggian Tanaman")
        ketinggian_stats = df_tanaman_filtered['ketinggian'].describe()
        st.dataframe(ketinggian_stats)

# Halaman Informasi
else:
    st.header("ℹ️ Informasi TNBTS")
    
    # Hitung statistik
    total_penduduk = gdf_desa['jumlah_pen'].sum() if not gdf_desa.empty and 'jumlah_pen' in gdf_desa.columns else 0
    total_kecamatan = gdf_desa['nama_kecam'].nunique() if not gdf_desa.empty and 'nama_kecam' in gdf_desa.columns else 0
    total_kabupaten = gdf_desa['nama_kabko'].nunique() if not gdf_desa.empty and 'nama_kabko' in gdf_desa.columns else 0
    tanaman_dilindungi = len(df_tanaman[df_tanaman['status_konservasi'] == 'Dilindungi'])
    
    st.markdown(f"""
    ### 🌋 Taman Nasional Bromo Tengger Semeru
    
    Taman Nasional Bromo Tengger Semeru (TNBTS) adalah kawasan konservasi yang terletak di Jawa Timur, Indonesia. 
    Kawasan ini memiliki keanekaragaman hayati yang tinggi, termasuk berbagai spesies tanaman herbal yang 
    dimanfaatkan oleh masyarakat sekitar untuk pengobatan tradisional.
    
    ---
    
    ### 📊 Data dan Statistik
    
    | Kategori | Jumlah | Keterangan |
    |----------|--------|------------|
    | **🏘️ Desa** | {len(gdf_desa)} desa | Tersebar di {total_kecamatan} kecamatan, {total_kabupaten} kabupaten |
    | **👥 Penduduk** | {total_penduduk:,} jiwa | Data dari BPS |
    | **🌿 Tanaman Herbal** | {len(df_tanaman)} spesies | 86 spesies teridentifikasi |
    | **🔒 Tanaman Dilindungi** | {tanaman_dilindungi} spesies | Purwoceng, Parijoto, Anggrek |
    
    ---
    
    ### 💊 Fungsi Utama Tanaman
    
    Berdasarkan data yang terkumpul, tanaman herbal di TNBTS memiliki berbagai fungsi pengobatan:
    
    * **Pencernaan** - Adas, Jahe, Kunyit, Lobak, Ketumbar, dll
    * **Antiradang** - Ajeran putih, Awar-awar, Kesimbukan, Trabasan, Jahe merah, dll
    * **Penurun demam** - Bawang merah, Bunga Matahari, Paitan, Tapak liman, dll
    * **Pereda nyeri** - Bidara laut, Daun dadap, Tepung otot, dll
    * **Obat luka** - Ganjan, Jarak merah, Wedusan, Tirem, Paku sarang burung, Cemara gunung, dll
    * **Batuk & pilek** - Buah klandingan, Kencur, Pulosari, Suplir, dll
    * **Kesuburan** - Purwoceng, Parijoto
    * **Diuretik** - Alang-alang, Pakis/paku pedang, Rumput teki-tekian, Rumput ilalang, dll
    * **Antiseptik** - Sirih, Vervain, dll
    
    ---
    
    ### 📍 Sumber Data
    
    * **Data Desa:** File GeoJSON dari BIG/BPS ({len(gdf_desa)} desa)
    * **Data Tanaman:** Hasil penelitian Tim Peneliti UB (2026) - 86 spesies
    * **Peta Basemap:** OpenStreetMap, Esri World Imagery (Satelit), OpenTopoMap
    
    ---
    
    ### 👥 Tim Peneliti
    
      * **Ketua Tim:** Dr Eng Turniningtyas Ayu R., ST., MT
    * **Anggota:**
      1.    Prof.Dr.Ir. Moch. Sasmito Djati, M.S. - (Pakar Tanaman Herbal)
      2.    Adipandang Yudono, S.Si., M.U.R.P., Ph.D - (Pakar GIS dan WebGIS Analytics)
      3.    Dr. Ir. Arief Andy Soebroto ST.,M.Kom. - (Pakar Pembangunan AI Platform)
    * **Tahun:** 2026
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 10px;'>
    © 2026 Team Peneliti UB untuk Distribusi Spasial Tanaman Herbal di TNBTS<br>
    Data: 86 spesies tanaman herbal | 41 desa di sekitar TNBTS
</div>
""", unsafe_allow_html=True)

# Tampilkan informasi di sidebar
with st.sidebar:
    st.markdown("---")
    st.caption("📁 **Status File**")
    if os.path.exists('Desa_TNBTS.geojson'):
        file_size = os.path.getsize('Desa_TNBTS.geojson') / 1024  # KB
        st.caption(f"✅ Desa_TNBTS.geojson ({file_size:.1f} KB)")
        st.caption(f"📊 {len(gdf_desa)} desa dimuat")
    else:
        st.caption("❌ Desa_TNBTS.geojson tidak ditemukan")
    
    st.caption(f"🌿 {len(df_tanaman)} spesies tanaman (86 spesies)")
    st.caption(f"🔍 Filter: {len(df_tanaman_filtered)} spesies")
