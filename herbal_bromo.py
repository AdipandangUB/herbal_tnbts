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
# DATA TANAMAN HERBAL LENGKAP DARI FILE
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
    },
    "ANDONG": {
        "nama_latin": "cordyline fruticosa Linn",
        "fungsi": "Menghentikan pendarahan, obat luka, mengatasi diare, mengatasi batuk dan sakit tenggorokan, obat gangguan haid, mengatasi radang, menurunkan demam.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 15°C-35°C. Ketinggian: tumbuh di dataran rendah hingga dataran tinggi 1.900 mdpl. Tumbuh pada wilayah dengan curah hujan 300-2.500 mm/th. Tumbuh optimal pada pH 5.5-6.5",
        "cara_memanfaatkan": "Daun dan akar direbus, air rebusan membantu meredakan infeksi pencernaan (diare dan disentri), batuk darah, haid berlebihan, dan wasir. Daun ditumbuk menjadi pasta, dioleskan pada kulit yang mengalami luka bakar dan bengkak karena sengatan binatang berbisa.",
        "yang_dimanfaatkan": "Daun dan akar",
        "potensi_sebaran": "RPTN Patok Picis (Bidang 1 SPTN Wilayah 2)",
        "foto": "media/image4.jpeg"
    },
    "AWAR-AWAR": {
        "nama_latin": "Ficus septica Burm. F.",
        "fungsi": "Anti radang dan pereda nyeri, mengobati bisul (pemakaian luar), antibakteri alami, penurun demam, gangguan pencernaan ringan, masalah pernapasan.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 28°C-30°C. Tumbuh optimal di dataran rendah hingga ketinggian 1.200 mdpl, dapat juga tumbuh di 1.800 mdpl. Tumbuh pada wilayah dengan curah hujan 300-2.500 mm/th. Menyukai tanah lembap dan subur dengan pH ideal 6.0 - 7.0.",
        "cara_memanfaatkan": "Daun ditumbuk hingga menjadi pasta, dioleskan pada kulit bisul dan gatal. Getah awar-awar dioleskan pada kulit yang terkena kurap atau herpes. Daun awar-awar direbus, air diminum untuk meredakan perut mulas dan diare, kompres saat demam.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Ngadas (Kecamatan Poncokusumo, Malang), Desa Ranupani (Kecamatan Senduro, Lumajang), Desa Cemoro Lawang (Kecamatan Sukapura, Probolinggo).",
        "foto": "media/image5.jpeg"
    },
    "BAKUNG": {
        "nama_latin": "Crinum asiaticium L.",
        "fungsi": "Mengurangi bengkak, obat keseleo dan pegal linu, mengatasi nyeri sendi dan rematik, obat bisul dan luka bernana, obat sakit kepala, mengatasi iritasi kulit ringan.",
        "syarat_hidup": "Iklim dan Suhu: Cocok di daerah tropis dan subtropis, toleran terhadap panas. Optimal di dataran rendah hingga ketinggian 700 mdpl. Optimal tumbuh di curah hujan tinggi 2.000-3.000 mm/th. Tumbuh optimal pada kisaran pH tanah 6,5-7,5",
        "cara_memanfaatkan": "Daun bakung ditumbuk halus dikompreskan pada bagian tubuh yang bengkak, memar atau terkilir. Ujung daun bakung dipotong untuk diambil getahnya, dioleskan pada luka atau yang terdapat bisul.",
        "yang_dimanfaatkan": "Daun dan getah",
        "potensi_sebaran": "RPTN Patok Picis (Bidang 1 SPTN Wilayah 2)",
        "foto": "media/image6.jpeg"
    },
    "KLANDINGAN": {
        "nama_latin": "Lucas lavandulifolia",
        "fungsi": "Mengatasi insomnia, meredakan sakit kepala, kejang pada anak, epilepsi, anti inflamasi (bengkak, meredakan nyeri, dan mengobati penyakit kulit (kudis), menurunkan gula dan kolesterol, serta antimikroba.",
        "syarat_hidup": "Hidup di wilayah tropis dan subtropis dengan rentang suhu udara rata-rata 20°C-35°C. Tumbuh liar di tanah kering dan terlantar, pada dataran rendah hingga ketinggian 1.500 mdpl. Optimal tumbuh di curah hujan tinggi 1.000mm/th -- 2000mm/th. Tumbuh optimal pada kisaran pH tanah antara 6,0 hingga 7,0 membutuhkan sinar matahari penuh",
        "cara_memanfaatkan": "Daun klandingan ditumbuk halus, pasta dioleskan pada area kulit yang gatal, radang/panas, bisul, dan kulit yang luka luar ringan. Biji klandingan direbus, air rebusan diminum rutin untuk menurunkan gula darah dan kolesterol. Daun direbus, air rebusan membantu tidur lebih nyenyak atau menurunkan panas dalam.",
        "yang_dimanfaatkan": "Daun dan Biji",
        "potensi_sebaran": "Desa Ngadas (Kecamatan Poncokusumo, Kab. Malang), Desa Ranupani (Kecamatan Senduro, Kab. Lumajang). Desa Tosari (Kecamatan Tosari Pasuruan)",
        "foto": "media/image7.jpeg"
    },
    "JARAK HITAM": {
        "nama_latin": "familia euphorbiaceous",
        "fungsi": "Radang telinga anak, demam, sembelit, memar akibat pukulan, penyakit kulit, kembung, masuk angin, panas, lepra dan kanker",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 20°C hingga 30°C. Ketinggian: dataran rendah hingga ketinggian 1700 mdpl. Tumbuh pada wilayah dengan curah hujan 300mm - 1200 mm/th, sangat tahan kekeringan. Tumbuh ideal pada tanah dengan pH 5,0 - 6,5",
        "cara_memanfaatkan": "Biji tanaman yang sudah dibuang kulitnya dihaluskan hingga menjadi serbuk dan dapat ditempelkan ke bagian yang terkena sakit lepra. Daun segar di tumbuk dicampur garam dan ditempelkan pada bagian yang luka atau pegal-pegal. Daun jarak direbus, air digunakan untuk mandi untuk mengurangi demam dan penderita penyakit kulit.",
        "yang_dimanfaatkan": "Biji dan daun",
        "potensi_sebaran": "",
        "foto": "media/image8.jpeg"
    },
    "JARAK": {
        "nama_latin": "Jatropha curcas L.",
        "fungsi": "Sakit gigi, sariawan, gatal-gatal, Mengatasi sembelit, perut kembung, penyembuhan luka (tanin dan flavonoid), nyeri sendi dan reumatik, obat batuk (pengencer dahak)",
        "syarat_hidup": "Iklim dan suhu: wilayah tropis dengan suhu optimal antara 20°C hingga 30°C. Ketinggian: dataran rendah hingga ketinggian 300-800 mdpl. Tumbuh pada wilayah dengan curah hujan 300-1500mm/tahun, sangat tahan terhadap kekeringan. Tumbuh ideal pada pH tanah di angka 5 - 6,5",
        "cara_memanfaatkan": "Daun muda dikukus, air rebusan diminum untuk mengatasi sembelit. Daun ditumbuk hingga halus campur air hangat sedikit, oleskan pada lokasi rematik atau masalah kulit seperti exim. Daun jarak tua bersihkan dan layukan di atas api. Setelah layu oleskan minyak kelapa, minyak telon atau minyak kayu putih dan tempelkan di bagian perut dan pinggang. Getah untuk sakit gigi (antiseptik) dan sariawan, perlu berhati-hati karena sering merusak gusi sehat.",
        "yang_dimanfaatkan": "Biji, getah, batang, dan daun",
        "potensi_sebaran": "",
        "foto": "media/image9.jpeg"
    },
    "BUAH DELIMA": {
        "nama_latin": "Punica granatum L",
        "fungsi": "Menjaga kesehatan jantung, menurunkan tekanan darah, menghambat kanker (kulit, payudara dan prostat), melawan peradangan, dan melancarkan pencernaan",
        "syarat_hidup": "Iklim dan suhu: wilayah tropis dengan suhu optimal antara 25°C hingga 30°C. Ketinggian: dataran rendah hingga ketinggian 1000 mdpl. Tumbuh baik pada curah hujan 800mm - 1200 mm/th, sangat tahan terhadap kekeringan. Tumbuh ideal pada pH tanah di angka 6,5 - 7,5",
        "cara_memanfaatkan": "Biji buah delima dihaluskan, saring airnya untuk mendapatkan jus murni yang kaya polifenol dan baik untuk menurunkan kolesterol jahat. Kulit buah delima dikeringkan dan diseduh untuk teh. Buah dapat dikonsumsi langsung kaya Vitamin C untuk kekebalan tubuh, produksi kolagen untuk mencegah penuaan dini, kandungan serat alaminya melancarkan pencernaan dan mencegah sembelit",
        "yang_dimanfaatkan": "Buah, kulit buah (teh) dan biji",
        "potensi_sebaran": "",
        "foto": "media/image10.jpeg"
    },
    "LABU SIAM HITAM": {
        "nama_latin": "Sicyos edulis",
        "fungsi": "Menurunkan tekanan darah, mengontrol gula darah, mencegah sembelit, mencegah cacat tabung saraf pada janin, melancarkan ASI, mengobati kanker kulit melanoma maligna",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 25°C - 30°C. Ketinggian: dataran rendah hingga ketinggian 1000 mdpl. Tumbuh pada wilayah dengan curah hujan 800mm - 1200 mm/th, sangat tahan terhadap kekeringan. Tumbuh ideal pada pH tanah di angka 6,5 - 7,5",
        "cara_memanfaatkan": "Air rebusan labu siam mengandung kalium efektif membantu kestabilan tekanan darah. Buah labu siam memiliki indeks glikemik rendah, sangat baik mencegah lonjakan gula darah pada penderita diabetes. Kandungan asam folat tinggi mencegah cacat tabung saraf pada janin dan membantu melancarkan produksi ASI. Daun Muda dikonsumsi atau diseduh sebagai teh herbal untuk peluruh urine (diuretik).",
        "yang_dimanfaatkan": "Buah dan daun",
        "potensi_sebaran": "",
        "foto": "media/image11.jpeg"
    },
    "PEPAYA GUNUNG": {
        "nama_latin": "Vasconcellea pubescens",
        "fungsi": "Mengatasi cacingan, melancarkan pencernaan dan mencegah konstipasi, anti oksidan untuk mencegah penyakit kanker, jantung, mencegah osteoporosis",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 10°C - 20°C. Ketinggian: hidup di dataran tinggi di ketinggian 1.500-3.000 mdpl. Penyiraman: curah hujan 800mm - 1200 mm/th, sangat tahan terhadap kekeringan. Tumbuh ideal pada pH tanah di 5,5 - 6,5",
        "cara_memanfaatkan": "Daun carica mengandung alkaloid karpain, efektif meredakan demam dan meningkatkan sistem kekebalan tubuh. Daun carica berkhasiat meredakan demam, nyeri sendi, dan meningkatkan imunitas. Rebusan akar sering diandalkan untuk membantu meluruhkan batu ginjal dan mengatasi cacingan. Tumbukan akar atau kulit batang mengandung antiseptik untuk meredakan bengkak akibat gigitan serangga atau radang kulit ringan.",
        "yang_dimanfaatkan": "Buah, daun, batang dan akar",
        "potensi_sebaran": "",
        "foto": "media/image12.jpeg"
    },
    "BIT MERAH": {
        "nama_latin": "Beta vulgaris L",
        "fungsi": "Menurunkan tekanan darah, mencegah pikun, diabetes, mencegah kanker terutama payudara dan kandung kemih, mencegah kelainan janin, vitalitas, anemia, mengatasi peradangan tubuh, dan meningkatkan kerja saraf dan otot",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 15°C - 25°C. Ketinggian: hidup di dataran tinggi di ketinggian 1.000-1.200 mdpl. Tumbuh pada wilayah dengan curah hujan 500-550 mm per tahun, sangat tahan terhadap kekeringan. Tumbuh ideal pada pH tanah di 6-7",
        "cara_memanfaatkan": "Umbi dimakan langsung (salad). Dibuat juice.",
        "yang_dimanfaatkan": "Umbi",
        "potensi_sebaran": "",
        "foto": "media/image13.jpeg"
    },
    "DAUN OTOT": {
        "nama_latin": "Stellaria saxatilis",
        "fungsi": "Meredakan pegal linu, nyeri otot, dan peradangan",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 20°C hingga 30°C. Ketinggian: dataran tinggi hingga ketinggian 2200 mdpl. Tumbuh baik pada wilayah dengan curah hujan 300mm /th-1200 mm/th, tahan terhadap kekeringan. Tumbuh ideal pada tanah dengan pH 5,0 - 6,5",
        "cara_memanfaatkan": "Daun dan batang ditumbuk dan ditambah minyak gandapura, dioleskan langsung pada area tubuh yang terasa nyeri atau pegal linu.",
        "yang_dimanfaatkan": "Daun dan batang",
        "potensi_sebaran": "",
        "foto": "media/image14.jpeg"
    },
    "CIPLUKAN": {
        "nama_latin": "Physalis minima",
        "fungsi": "Mengatasi demam dan masuk angin, obat batuk dan pilek, mengobati radang dan anti inflamasi, diuretik ringan, penyakit kulit ringan.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu 18°C-35°C dan penyinaran matahari penuh. Tumbuh di dataran rendah hingga ketinggian 700-2.300 mdpl, paling baik 1.500 mdpl. Penyiraman: menyukai curah hujan tahunan rata-rata 1.500-2.300 mm. Tumbuh ideal pada tanah dengan pH 4,5-8,2",
        "cara_memanfaatkan": "Akar dan batang direbus. Air rebusan dapat menurunkan gula, dan tekanan darah tinggi. Daun ciplukan ditumbuk dengan sedikit kapur sirih untuk dioleskan pada sendi yang mengalami peradangan. Daun ciplukan, daun sirih dan sedikit adas pulosari ditumbuk dan ditempelkan pada kulit yang bermasalah (bisul dan borok)",
        "yang_dimanfaatkan": "Daun, buah dan akar",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Gubuklakah dan Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadas dan Desa Ngadisari (Kec. Sukapura, Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari Kab Pasuruan).",
        "foto": "media/image15.jpeg"
    },
    "CALINGAN": {
        "nama_latin": "Centella asiatica L.",
        "fungsi": "Mempercepat penyembuhan luka, kesehatan kulit, sirkulasi darah, menenangkan saraf, anti inflamasi dan antioksidan, mengatasi gangguan pencernaan.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 20°C-30°C dengan kelembaban tinggi. Ketinggian: dataran rendah - 2500 mdpl. Tumbuh baik pada wilayah dengan curah hujan 1500mm - 2500 mm/th, sangat tahan kekeringan. Tumbuh ideal pada tanah dengan pH 5,5-6,5",
        "cara_memanfaatkan": "Dimakan mentah sebagai lalapan. Diseduh menjadi teh herbal. Dibuat jus segar. Daun pegagan dihaluskan, pasta untuk masker untuk menghilangkan kulit berjerawat dan merangsang produksi kolagen",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Gubuklakah dan Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadas dan Ngadisari (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari Kab Pasuruan).",
        "foto": "media/image16.jpeg"
    },
    "DAUN KANCING": {
        "nama_latin": "Desmodium sp.",
        "fungsi": "Anti radang, mengatasi batuk dan gangguan pernapasan, melancarkan buang air kecil, obat sakit perut dan diare, mengatasi luka dan infeksi kulit, menambah daya tahan tubuh, detoksifikasi hati.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun semanggi direbus. Air rebusan diminum untuk mengatasi infeksi saluran kencing, batuk sesak napas, amandel, menurunkan kolesterol, hingga mencegah pengeroposan tulang. Daun semanggi ditumbuk hingga halus. Pasta dioleskan kulit yang luka dan diam ±15-20 menit hingga mengering dan dibilas dengan air hangat. Daun dikeringkan untuk teh",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image17.jpeg"
    },
    "GANJAN": {
        "nama_latin": "Artemisia vulgaris",
        "fungsi": "Obat luka dan bisul, mengurangi bengkak-peradangan, mengatasi demam-masuk angin, mengatasi gangguan pencernaan ringan, antiseptik alami.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun segar atau kering direbus. Air rebusan untuk melancarkan haid, meredakan nyeri kram menstruasi, dan mengatasi gangguan pencernaan ringan. Daun segar ditumbuk atau diblender hingga halus dan berbentuk pasta kental. Pasta dioleskan atau ditempelkan pada bagian tubuh yang bengkak atau nyeri (memar atau luka). Daun ganjan diambil ekstrak kemudian dicampur minyak zaitun. Ekstrak daun ganjan dapat dijadikan minyak oles atau salep untuk menenangkan kulit dan meredakan gatal.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image18.jpeg"
    },
    "GANYONG": {
        "nama_latin": "Canna indica L.",
        "fungsi": "Menjaga kesehatan pencernaan, meredakan panas dalam & diare ringan, sumber energi-pemulihan tubuh, anti inflamasi ringan (pemakaian luar), kesehatan kulit.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Umbi ganyong diparut diperas untuk diambil sarinya. Sari pati diendapkan hingga airnya terpisah dan dibuang. Endapan pati dijemur hingga kering menjadi tepung ganyong. Pati ganyong dapat mengobati sakit magh dan asam lambung, mengatasi diare. Umbi ganyong direbus digunakan untuk meredakan panas dalam dan demam (antipiretik), mengatasi radang saluran kencing dan peluruh urine",
        "yang_dimanfaatkan": "Rimpang (umbi)",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Gubuklakah dan Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari Kab. Pasuruan).",
        "foto": "media/image19.jpeg"
    },
    "JENGGOT WESI": {
        "nama_latin": "Usnea Berbata Fries",
        "fungsi": "Anti bakteri, anti jamur, obat luka, gangguan pernapasan, penurun panas -antiradang, potensi antikanker (masih tahap awal riset).",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Jenggot wesi direbus sampai sarinya keluar, lalu saring airnya. Air rebusan untuk mengompres area kulit yang bermasalah atau mencuci luka. Jenggot wesi dicuci bersih dikeringkan dan dipotong kecil-kecil untuk diseduh dengan air panas (layaknya membuat teh). Air seduhan disaring dan ditambahkan madu asli untuk mengurangi rasa pait. Air seduhan jenggot wesi untuk meredakan batuk dan masalah pernapasan.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Gubuklakah dan Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab Pasuruan).",
        "foto": "media/image20.jpeg"
    },
    "KAYU AMPET": {
        "nama_latin": "Alstonia macrophylla",
        "fungsi": "Obat sakit perut dan diare, mengatasi masuk angin, mengobati demam, antiradang, mengatasi rematik, meningkatkan stamina.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Kulit kayu ampet dikeringkan dan direbus. Air rebusan digunakan meredakan nyeri pasca-persalinan dan merawat area kewanitaan. Kayu ampet dihaluskan hingga menjadi bubuk kayu. Bubuk kayu ampet diseduh untuk meredakan peradangan, menurunkan kolesterol, sakit perut, diare, masuk angin dan demam.",
        "yang_dimanfaatkan": "Kayu atau batang",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image21.jpeg"
    },
    "KENCANA UNGU": {
        "nama_latin": "Ruellia",
        "fungsi": "Membantu menurunkan gula darah, penurun panas & antiinflamasi, antibakteri, melancarkan buang air kecil, membantu batuk dan radang tenggorokan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun kencana ungu direbus. Air rebusan dapat menurunkan kadar gula darah. Daun atau bunga kencana ungu ditumbuk hingga halus. Ampas tumbukan dioleskan pada kulit yang gatal atau terkena iritasi. Akar kencana ungu direbus. Air rebusan digunakan untuk memperlancar buang air kecil.",
        "yang_dimanfaatkan": "Daun, bunga, dan akar",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image22.jpeg"
    },
    "LILI-LILIAN LIAR": {
        "nama_latin": "Molineria sp.",
        "fungsi": "Obat masuk angin & perut kembung, obat batuk & sakit tenggorokan, mengatasi mual, anti radang, anti bakteri dan anti jamur, mengatasi pegal linu atau rematik, meningkatkan nafsu makan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Akar (rimpang) direbus hingga mendidih dengan 2 gelas air. Air rebusan rimpang dapat mengatasi masalah pencernaan, menurunkan demam. Daun atau akar ditumbuk hingga halus membentuk pasta untuk ditempelkan pada area kulit yang bermasalah (gatal-gatal dan luka).",
        "yang_dimanfaatkan": "Daun dan akar",
        "potensi_sebaran": "RPTN Ranu Darungan (Bidang ll, SPTN Wilayah lV), RPTN Ranu Pani, RPTN Senduro.",
        "foto": "media/image23.jpeg"
    },
    "LOMBOK TERONG": {
        "nama_latin": "Solanum torvum Sw",
        "fungsi": "Mengatasi tekanan darah tinggi, pereda nyeri & antiinflamasi, antibakteri & antiseptik, mengatasi anemia, mengatasi batuk & radang tenggorokan, melancarkan pencernaan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "1 buah cabai dihaluskan dan dicampur dengan sedikit minyak kelapa atau minyak zaitun untuk dioleskan secara tipis pada area pegal, nyeri otot, atau rematik sebagai kompres hangat. Buah cabai terong diolah secara sehat untuk dikonsumsi dalam porsi yang sedikit untuk meningkatkan sistem imun tubuh (kaya vitamin C), menurunkan berat badan dan metabolisme, dan menurunkan stres dan sakit kepala.",
        "yang_dimanfaatkan": "Buah",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang).",
        "foto": "media/image24.png"
    },
    "PAITAN": {
        "nama_latin": "Tithonia diversifolia",
        "fungsi": "Menurunkan demam, mengatasi sakit perut, antiradang, mengatasi luka & infeksi kulit, menurunkan gula darah (tradisional), menurunkan tekanan darah, mengatasi malaria, antioksidan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun paitan muda dicuci bersih dan direbus dengan 2-3 gelas air bersih hingga menyusut. Air rebusan kemudian disaring untuk memisahkan ampas dan daunnya. Air rebusan daun paitan digunakan untuk membantu meredakan peradangan, menurunkan gula darah, mengatasi masalah pencernaan (diare dan kembung), demam, dan keluhan kulit (gatal, luka dan infeksi kulit).",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Ngadas RPTN Jemplang (Bidang l, SPTN Wilayah ll)",
        "foto": "media/image25.jpeg"
    },
    "PAKIS": {
        "nama_latin": "Davallia",
        "fungsi": "Mengobati gangguan pencernaan, anti inflamasi, mengatasi masalah kulit, meningkatkan kekebalan tubuh.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Akar pakis ditumbuk hingga halus kemudian ditempelkan pada area tubuh yang bengkak, memar, atau nyeri sendi. Akar pakis dicuci bersih kemudian diiris tipis-tipis. Diminum secara rutin untuk mengobati gangguan pencernaan, anti inflamasi, dan meningkatkan kekebalan tubuh.",
        "yang_dimanfaatkan": "Akar",
        "potensi_sebaran": "Blok Ireng-ireng, RPTN Senduro (Bidang II, SPTN Wilayah III)",
        "foto": "media/image26.jpeg"
    },
    "PAKU RANE": {
        "nama_latin": "Selaginella sp",
        "fungsi": "Mengobati penyakit jantung, stroke, obat luka, malaria, pembersih darah, mengatasi masalah kewanitaan, sakit perut, tonik pasca-persalinan, menurunkan demam, anti kanker, anti mikroba, dan antibiofilm.",
        "syarat_hidup": "Iklim dan Suhu: wilayah tropis dengan suhu optimal antara 15°C-28°C dengan kelembaban tinggi. Ketinggian: ditemukan di pegunungan 1.500 -- 2.356 mdpl. Memerlukan lingkungan sangat lembap dan teduh dengan curah hujan 1.500mm/th - 3.000 mm/th. Tumbuh ideal pada tanah dengan pH yang cenderung asam hingga netral (pH 3,9 - 7,0)",
        "cara_memanfaatkan": "Batang dan daun ditumbuk hingga halus, pasta dibalurkan atau ditempelkan sebagai kompres pada bagian tubuh yang bengkak, memar, atau luka. Batang dan daun direbus untuk meredakan batuk, asma, masalah pencernaan, hipertensi, dan demam",
        "yang_dimanfaatkan": "Daun dan Batang",
        "potensi_sebaran": "RPTN Ranu Darungan (Bidang ll, SPTN Wilayah lV), Blok Ireng-ireng RPTN Senduro.",
        "foto": "media/image27.jpeg"
    },
    "PARIJOTO": {
        "nama_latin": "Medinilla speciosa",
        "fungsi": "Meningkatkan kesuburan, menjaga kesehatan ibu hamil, mengatasi sariawan, daya tahan tubuh, menurunkan kolesterol dan trigliserida, serta digunakan dalam ritual adat Jawa simbol kesuburan dan bayi tampan/-cantik",
        "syarat_hidup": "Iklim dan suhu: tumbuh optimal di pegunungan dengan suhu 18°C-25°C dan kelembaban tinggi. Paling produktif dan tumbuh alami di area pegunungan dengan ketinggian 500--2.300 mdpl. Penyiraman: menyukai curah hujan tahunan rata-rata 1.500-2.300 mm. Tumbuh ideal pada tanah dengan pH 5.5-6.5",
        "cara_memanfaatkan": "Buah parijoto dapat dimakan langsung. Buah parijoto cocok untuk program hamil. Daun parijoto direbus, air rebusan untuk penambah imunitas tubuh, meredakan diare dan melancarkan pencernaan, menurunkan kolesterol dan trigliserida. Tumbuk daun parijoto, diperas airnya digunakan sebagai obat kumur untuk meredakan sariawan dan gusi bengkak.",
        "yang_dimanfaatkan": "Buah dan daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image28.jpeg"
    },
    "PECUT KUDA": {
        "nama_latin": "Stachytarpheta sp",
        "fungsi": "Menurunkan demam, obat batuk-flu, melancarkan buang air kecil gangguan pencernaan, anti radang, menurunkan tekanan darah, menurunkan gula darah, obat luka & penyakit kulit, mengatasi rematik dan pegal-pegal.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun pecut kuda direbus dengan 2-3 gelas air bersih hingga mendidih dan menyusut menjadi 1 gelas. Air rebusan disaring dan diminum 1-2 kali sehari saat hangat untuk mengatasi demam, radang tenggorokan, amandel, batuk, flu, dan infeksi saluran pernapasan. Daun segar ditumbuk hingga halus sampai bertekstur bubur. Tumbukan ditempelkan langsung pada area kulit yang bermasalah atau luka. Daun pecut kuda direbus dengan air hingga berubah menjadi asam-asam kuku, kemudian air rebusan digunakan untuk membasuh area kewanitaan untuk mengatasi keputihan dan rasa gatal.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image29.jpeg"
    },
    "RANTI": {
        "nama_latin": "Tinospora crispa L. Miers",
        "fungsi": "Antimalaria, mengatasi demam, menjaga kesehatan jantung dan tekanan darah, melancarkan pencernaan, antibakteri dan antiinflamasi, meningkatkan daya tahan tubuh.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun ranti ditumbuk hingga halus kemudian diseduh dan disaring untuk diminum airnya. Air daun ranti dapat menurunkan tekanan darah tinggi. Daun ranti direbus hingga mendidih dan airnya tersisa setengahnya. Air rebusan disaring dan diminum untuk mengobati sakit perut dan diare. Seluruh bagian tanaman ranti dicuci bersih lalu ditumbuk hingga halus dan ditambahkan madu atau minyak kelapa dan dibalurkan pada area kulit yang bermasalah atau bengkak. Buah ranti dikonsumsi sebagai lalapan atau dimasak tumis (kaya akan vitamin dan nutrisi) untuk mencegah sariawan dan menjaga imunitas",
        "yang_dimanfaatkan": "Daun, Batang, dan Buah",
        "potensi_sebaran": "Desa Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ranupani (Kec. Senduro, Kab, Lumajang).",
        "foto": "media/image30.jpeg"
    },
    "SAWI IRENG": {
        "nama_latin": "Brassica juncea",
        "fungsi": "Melancarkan pencernaan, menurunkan kolesterol, kesehatan jantung, anti bakteri dan anti inflamasi, penambah imunitas, mengatasi masuk angin ringan.",
        "syarat_hidup": "Iklim dan Suhu: membutuhkan sinar matahari penuh, dan suhu ideal 10°C-25°C. Tumbuh optimal di dataran rendah hingga tinggi 5-1.200 m dpl. Membutuhkan curah hujan ideal antara 1.000-1.500 mm/tahun. Tumbuh baik pada pH 6.0-6.8",
        "cara_memanfaatkan": "Daun atau biji sawi ireng ditumbuk, pasta kental ditempelkan bagian tubuh yang nyeri atau bengkak. Daun direbus air rebusan diminum 1 kali sehari untuk membantu detoksifikasi dan pencernaan.",
        "yang_dimanfaatkan": "Daun dan Biji",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab. Pasuruan).",
        "foto": "media/image31.jpeg"
    },
    "SEMANGGI": {
        "nama_latin": "Marsilea crenata",
        "fungsi": "Melancarkan peredaran darah, menurunkan kadar gula darah, mengatasi demam, melancarkan pencernaan, antibakteri dan antiinflamasi.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun dan tangkai semanggi direbus, air rebusan untuk menurunkan demam, mengobati flu, dan meredakan radang. Kepala bunga dan daun dikeringkan untuk teh herbal meredakan gejala menopause dan mencegah osteoporosis. Daun diolah menjadi lalapan, pecel atau urap untuk mendapatkan vitamin dan antioksidan untuk menjaga kesehatan pembuluh darah serta menurunkan kolesterol jahat.",
        "yang_dimanfaatkan": "Daun dan bunga",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec Tosari, Kab Pasuruan).",
        "foto": "media/image32.jpeg"
    },
    "SENGGANEN": {
        "nama_latin": "Melastoma malabathricum L",
        "fungsi": "Mengobati diare, menghentikan pendarahan, mempercepat penyembuhan luka, mengatasi sariawan dan radang mulut, mengobati keputihan, anti-inflamasi, mengatasi bisul atau infeksi kulit.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun segar direbus, air rebusan untuk mengobati diare dan disentri, meredakan asam lambung dan nyeri sendi (terdapat senyawa anti-inflamasi). Akar senggani direbus dengan sedikit garam, air rebusan untuk berkumur (meredakan sakit gigi). Daun atau buah senggani ditumbuk halus, pasta ditempelkan pada area kulit yang terkena luka bakar dan bisul sebagai obat luar. Akar senggani dengan sambitolo dan kunyit, air rebusan untuk mengatasi keputihan dan nyeri haid",
        "yang_dimanfaatkan": "Daun, buah dan akar",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Ngadas dan Desa Gubuklakah Ngadas (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari Kab Pasuruan).",
        "foto": "media/image33.jpeg"
    },
    "SIRIH": {
        "nama_latin": "Piper betle Linn",
        "fungsi": "Antiseptik, obat keputihan, mengatasi bau mulut, obat sariawan dan radang gusi, menghentikan mimisan, mengobati luka, infeksi kulit, mengurangi keringat berlebih dan bau badan, obat batuk.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun sirih direbus dengan 500 ml air selama 10-15 menit hingga mendidih, tunggu sampai hangat lalu digunakan untuk berkumur selama beberapa detik sebelum dibuang, obat kumur daun sirih bermanfaat untuk meredakan sakit gigi, sariawan, dan bau mulut. Daun sirih direbus dengan 3 gelas air bersih hingga tersisa 1,5 gelas, kemudian disaring dan didinginkan untuk diminum 2-3 kali sehari sebelum makan. Air rebusan daun sirih dapat mengatasi batuk dan diabetes. Daun sirih yang sudah dicuci bersih ditumbuk hingga halus, lalu ditempelkan pada luka untuk mempercepat penutupan jaringan (obat luka) dan gatal.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image34.jpeg"
    },
    "STROBERI TENGGER": {
        "nama_latin": "Rubus Idaeus L.",
        "fungsi": "Menjaga kesehatan darah dan menstruasi, antibakteri dan antiinflamasi, mengontrol gula darah, menjaga kesehatan jantung, melancarkan pencernaan, mengatasi pilek dan flu ringan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun dikeringkan (dijadikan teh herbal) kemudian seduh dengan secangkir air panas dan disaring untuk diminum (dapat ditambahkan dengan madu murni). Seduhan ini dapat membantu mengencangkan otot panggul, meredakan nyeri haid, dan mengatasi diare. Buah stroberi diblender dengan sedikit air atau yogurt untuk dikonsumsi dan membantu menangkal radikal bebas karena tinggi antioksidan (antosianin dan flavonoid), menurunkan peradangan, menjaga kesehatan sel, meningkatkan sistem kekebalan tubuh. Seduhan teh daun Rubus idaeus pekat dibiarkan hingga dingin kemudian kain bersih dicelupkan ke dalam air seduhan untuk ditempelkan pada area kulit yang meradang.",
        "yang_dimanfaatkan": "Daun dan buah",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab Pasuruan).",
        "foto": "media/image35.jpeg"
    },
    "SURI PANDAK": {
        "nama_latin": "Plantago mayor Linn.",
        "fungsi": "Menyembuhkan luka & memar, meredakan batuk & gangguan pernapasan, melancarkan pencernaan, antibakteri & antiinflamasi, pereda nyeri ringan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun segar direbus, air rebusan diminum untuk mengencerkan dahak dan melegakan pernapasan, meredakan nyeri, asam urat, meredakan diare ringan serta melancarkan saluran kemih. Daun segar ditumbuk hingga halus kemudian dikompreskan pada bagian yang sakit (mengatasi bengkak)",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab, Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab. Pasuruan).",
        "foto": "media/image36.jpeg"
    },
    "TEKLAN": {
        "nama_latin": "Eupatorium riparium",
        "fungsi": "Obat demam, melancarkan buang air kecil, mengatasi gangguan pencernaan, anti radang luka ringan, mengatasi batuk.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun segar direbus dengan 2 gelas air bersih selama 15 menit hingga tersisa 1 gelas, kemudian air rebusan disaring dan dibagi menjadi dua bagian untuk diminum 2 kali sehari (pagi dan sore). Air rebusan ini membantu melancarkan urine, menurunkan tekanan darah. Antioksidan (mengandung senyawa flavonoid, tanin, dan fenol yang membantu menangkal radikal bebas).",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image37.jpeg"
    },
    "TEPUNG OTOT": {
        "nama_latin": "Borreria laevis",
        "fungsi": "Mengendalikan gula darah, meredakan nyeri otot & pegal linu, mengurangi peradangan, obat memar & luka ringan, melancarkan peredaran darah.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun segar yang sudah dicuci bersih direbus dengan 3 gelas hingga tersisa 1,5 gelas, kemudian air disaring dan diminum 1-2 kali sehari untuk mengobati batuk, radang, infeksi saluran kemih, diare atau sembelit. Akar dan daun direbus kemudian saring dan diminum selagi hangat untuk meredakan pegal atau nyeri otot. Daun segar ditumbuk hingga halus dan dioleskan atau ditempelkan tumbukan daun pada bagian kulit yang luka, memar, atau bekas gigitan serangga.",
        "yang_dimanfaatkan": "Akar dan Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image38.jpeg"
    },
    "TIREM": {
        "nama_latin": "Chromolaena odoratum",
        "fungsi": "Mengatasi sakit perut & gangguan pencernaan, menurunkan demam, obat luka & bisul, antiradang, mengatasi rematik.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun tirem ditumbuk hingga halus untuk ditempelkan pada area kulit yang luka atau ruam sebagai obat luar. Daun direbus dengan 3 gelas air hingga tersisa setengahnya, kemudian air disaring dan gunakan untuk mengompres pada area yang memar atau meradang.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image39.jpeg"
    },
    "SIMBARAN": {
        "nama_latin": "Peperomia sp",
        "fungsi": "Menyembuhkan luka ringan, meredakan batuk & radang tenggorokan, mengatasi demam ringan, pereda nyeri ringan, antibakteri ringan.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun bersih direbus. Air rebusan untuk mengatasi asam urat, rematik, sakit pinggang, kolesterol tinggi, dan menurunkan tekanan darah. Daun ditumbuk hingga halus. Pasta ditempelkan pada kulit yang terluka atau mengalami memar. Memiliki sifat antiseptik dan antiradang bagus untuk mempercepat penyembuhan luka bakar ringan, bisul, jerawat, serta mencerahkan wajah.",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab. Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab. Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab Pasuruan).",
        "foto": "media/image40.jpeg"
    },
    "TERONG BELANDA": {
        "nama_latin": "Solanum betaceum",
        "fungsi": "Mencegah obesitas, daya tahan tubuh, menurunkan tekanan darah, mengurangi resiko serangan jantung dan kanker, menjaga pencernaan, mencegah anemia, menjaga kesehatan mata, menangkal radikal bebas.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daging buah dijus, dapat membantu menurunkan kolesterol, mengontrol darah tinggi, mengatasi sariawan, hingga melancarkan pencernaan.",
        "yang_dimanfaatkan": "Daging buah",
        "potensi_sebaran": "Desa Argosari (Kec. Senduro, Kab Lumajang), Desa Ngadas dan Desa Gubuklakah (Kec. Poncokusumo, Kab. Malang), Desa Ngadisari dan Desa Ngadas (Kec. Sukapura, Kab Probolinggo), Desa Wonokitri dan Desa Mororejo (Kec. Tosari, Kab. Pasuruan).",
        "foto": "media/image41.jpeg"
    },
    "SELEDRI": {
        "nama_latin": "Apium graveolens",
        "fungsi": "Menurunkan hipertensi dan kolesterol, mengontrol gula darah, mengurangi peradangan, asam urat dan nyeri sendi, menjaga kesehatan jantung, membantu menenangkan saraf dan mengurangi stres.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun seledri direbus, air rebusan diminum untuk mengontrol tekanan darah dan membantu membuang kelebihan asam urine melalui urine. Daun seledri diblender hingga halus dan diminum secara teratur untuk menurunkan kolesterol dan detoksifikasi",
        "yang_dimanfaatkan": "Daun dan batang",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image42.jpeg"
    },
    "JAMUR LINGZHI": {
        "nama_latin": "Ganoderma lucidum",
        "fungsi": "Mengatasi insomnia, hipertensi, gastritis, menambah nafsu makan, menurunkan kolesterol dan lemak dalam darah, batuk, asma, bronkitis, rheumatic arthritis, mencegah tumor, meningkatkan daya tahan tubuh.",
        "syarat_hidup": "Optimal di hidup di suhu 25°C-30°C. Hidup pada ketinggian optimum 400-600 m dpl. Menyukai kondisi lingkungan dengan curah hujan rata-rata 2.000-2.500 mm/th. Jamur lingzhi umumnya hidup di batang pohon. Media tanam jamur ini berada pada kisaran pH 5,5 hingga 6,5",
        "cara_memanfaatkan": "Jamur dikeringkan atau direbus langsung. Air rebusan jamur lingzhi dapat meningkatkan kekebalan tubuh, menurunkan kolesterol, hingga mencegah kanker.",
        "yang_dimanfaatkan": "Jamur",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image43.jpeg"
    },
    "TEBU IRENG": {
        "nama_latin": "Saccharum officinarum",
        "fungsi": "Mengontrol gula darah, melancarkan sistem pencernaan, mencegah infeksi bakteri, mengurangi risiko terkena kanker",
        "syarat_hidup": "Iklim dan Suhu: iklim tropis dengan suhu optimal 24°C-30°C. Ketinggian: Ideal hidup di dataran rendah hingga 1.000 mdpl. Penyiraman: curah hujan 200mm/th, sangat tahan terhadap kekeringan. Tumbuh: subur di tanah gembur, kaya bahan organik, pH tanah antara 6,0-6,5",
        "cara_memanfaatkan": "Air rebusan akar, daun, dan sari batang tebu ireng, digunakan meredakan demam, melancarkan buang air kecil, dan meningkatkan kekebalan tubuh",
        "yang_dimanfaatkan": "Daun, batang, dan akar",
        "potensi_sebaran": "",
        "foto": "media/image44.jpeg"
    },
    "KETIUW": {
        "nama_latin": "Sonchus arvensis",
        "fungsi": "Meluruhkan batu ginjal atau batu kandung kemih (efek diuretik), menurunkan kadar asam urat, tekanan darah dan gula darah, meredakan radang dan pembengkakan.",
        "syarat_hidup": "Iklim dan Suhu: tumbuh baik pada suhu 25°C -32°C. Tumbuh subur dan optimal di ketinggian pada kisaran 50-1.600 mdpl. Tumbuh: subur di tanah gembur, kaya bahan organik, pH tanah antara 5.5-7.0",
        "cara_memanfaatkan": "Daun direbus dan diminum airnya. Daun dimakan langsung sebagai sayur. Daun ditumbuk, pasta digunakan sebagai kompres pada kulit yang bengkak",
        "yang_dimanfaatkan": "Daun",
        "potensi_sebaran": "Seluruh Kawasan TNBTS",
        "foto": "media/image45.jpeg"
    },
    "PUTIHAN": {
        "nama_latin": "Buddleja asiatica",
        "fungsi": "Upacara adat Suku Tengger, meredakan demam, penyakit kulit, ramuan pencuci luka karena mengandung antiseptik alami.",
        "syarat_hidup": "",
        "cara_memanfaatkan": "Daun direbus, uap air digunakan meredakan sakit kepala dan mengatasi masalah pernapasan. Tumbukan daun digunakan sebagai antiseptik topikal untuk membantu meredakan penyakit kulit. Akar dan daun digunakan sebagai obat nyeri, diare, dan demam. Selain digunakan untuk herbal, pada beberapa daerah tertentu juga dimanfaatkan sebagai penolak serangga (insektisida alami). Bunga putihan juga digunakan untuk upacara adat Suku Tengger.",
        "yang_dimanfaatkan": "Daun, bunga, dan akar",
        "potensi_sebaran": "",
        "foto": "media/image46.png"
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
    (6, 'ANDONG', 113.051111, -8.067778),
    (7, 'ANDONG', 113.051111, -8.067778),
    (8, 'AWAR-AWAR', 112.940877, -7.995191),
    (9, 'AWAR-AWAR', 112.978188, -7.974912),
    (10, 'AWAR-AWAR', 112.979085, -8.037856),
    (11, 'AWAR-AWAR', 113.026885, -7.995636),
    (12, 'BAKUNG', 112.948793, -8.011198),
    (13, 'BAKUNG', 112.950278, -8.013333),
    (14, 'BIT MERAH', 112.906453, -7.985204),
    (15, 'BIT MERAH', 112.906453, -7.985204),
    (16, 'BUAH DELIMA', 112.801975, -8.046787),
    (17, 'BUAH DELIMA', 112.801975, -8.046787),
    (18, 'CALINGAN', 112.922384, -7.971914),
    (19, 'CALINGAN', 112.924369, -7.996918),
    (20, 'CALINGAN', 112.946141, -8.002254),
    (21, 'CALINGAN', 113.005141, -8.030703),
    (22, 'CIPLUKAN', 112.933274, -8.030870),
    (23, 'CIPLUKAN', 112.964490, -7.922893),
    (24, 'CIPLUKAN', 112.964490, -7.922893),
    (25, 'CIPLUKAN', 112.999910, -7.967044),
    (26, 'DAUN KANCING', 112.941457, -8.015665),
    (27, 'DAUN KANCING', 113.018173, -7.971436),
    (28, 'DAUN OTOT', 112.912578, -8.045221),
    (29, 'GANJAN', 112.846877, -8.015389),
    (30, 'GANJAN', 112.896997, -7.901751),
    (31, 'GANJAN', 112.905667, -7.952630),
    (32, 'GANJAN', 112.911370, -7.896581),
    (33, 'GANJAN', 113.016111, -7.986944),
    (34, 'GANYONG', 112.941746, -8.000256),
    (35, 'JAMUR LINGZHI', 112.974959, -8.032646),
    (36, 'JAMUR LINGZHI', 113.009718, -8.037503),
    (37, 'JAMUR LINGZHI', 113.027076, -8.048771),
    (38, 'JARAK', 112.915327, -7.979138),
    (39, 'JARAK HITAM', 112.906554, -7.985286),
    (40, 'JENGGOT WESI', 112.916632, -8.040489),
    (41, 'JENGGOT WESI', 112.928867, -8.037286),
    (42, 'JENGGOT WESI', 113.007500, -8.038333),
    (43, 'KAYU AMPET', 112.929233, -8.035871),
    (44, 'KAYU AMPET', 112.996800, -7.968200),
    (45, 'KAYU AMPET', 112.996800, -7.968200),
    (46, 'KENCANA UNGU', 113.028632, -8.021287),
    (47, 'KETIUW', 112.959908, -7.930724),
    (48, 'KLANDINGAN', 112.951197, -7.930200),
    (49, 'KLANDINGAN', 112.951206, -7.930210),
    (50, 'LABU SIAM HITAM', 112.850204, -8.015127),
    (51, 'LILI-LILIAN LIAR', 112.944995, -8.000340),
    (52, 'LOMBOK TERONG', 112.880632, -7.919999),
    (53, 'LOMBOK TERONG', 112.896981, -7.901768),
    (54, 'PAITAN', 112.848401, -8.015110),
    (55, 'PAITAN', 112.901323, -7.895460),
    (56, 'PAITAN', 112.901323, -7.895460),
    (57, 'PAITAN', 113.025278, -8.013611),
    (58, 'PAITAN', 113.025278, -8.013611),
    (59, 'PAKIS', 112.980267, -8.032115),
    (60, 'PAKU RANE', 112.992477, -8.021199),
    (61, 'PARIJOTO', 113.026874, -8.024953),
    (62, 'PECUT KUDA', 113.017233, -7.960574),
    (63, 'PEPAYA GUNUNG', 112.880852, -7.919954),
    (64, 'PEPAYA GUNUNG', 112.880857, -7.919554),
    (65, 'PEPAYA GUNUNG', 112.898502, -7.988507),
    (66, 'PEPAYA GUNUNG', 112.898502, -7.988507),
    (67, 'PEPAYA GUNUNG', 112.898502, -7.988507),
    (68, 'PEPAYA GUNUNG', 112.898802, -7.988507),
    (69, 'PEPAYA GUNUNG', 112.984027, -7.915494),
    (70, 'PEPAYA GUNUNG', 112.984027, -7.915494),
    (71, 'PUTIHAN', 112.950980, -7.930804),
    (72, 'PUTIHAN', 113.000200, -7.967600),
    (73, 'PUTIHAN', 113.000200, -7.967600),
    (74, 'RANTI', 113.028845, -8.049922),
    (75, 'SAWI IRENG', 113.015757, -7.986393),
    (76, 'SAWI IRENG', 113.015757, -7.986393),
    (77, 'SELEDRI', 112.983340, -7.914567),
    (78, 'SELEDRI', 113.015742, -7.986405),
    (79, 'SELEDRI', 113.015742, -7.986405),
    (80, 'SEMANGGI', 113.052808, -7.991959),
    (81, 'SENGGANEN', 113.000200, -7.967600),
    (82, 'SENGGANEN', 113.000200, -7.967600),
    (83, 'SIMBARAN', 112.990639, -8.018076),
    (84, 'SIRIH', 113.004444, -8.029722),
    (85, 'STROBERI TENGGER', 112.943040, -8.022686),
    (86, 'SURI PANDAK', 112.912578, -8.045221),
    (87, 'TEBU IRENG', 113.025370, -7.973474),
    (88, 'TEKLAN', 112.989008, -8.094180),
    (89, 'TEPUNG OTOT', 112.846877, -8.015389),
    (90, 'TEPUNG OTOT', 112.935605, -8.023313),
    (91, 'TEPUNG OTOT', 112.950908, -7.930724),
    (92, 'TERONG BELANDA', 112.880537, -7.919971),
    (93, 'TERONG BELANDA', 112.880590, -7.920100),
    (94, 'TERONG BELANDA', 112.906433, -7.984717),
    (95, 'TERONG BELANDA', 112.983948, -7.914695),
    (96, 'TIREM', 112.939092, -8.002598),
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
def load_herbal_geojson():
    """
    Membaca data sebaran tanaman herbal (titik + atribut lengkap) dari
    sebaran_tanaman_herbal_TNBTS.geojson (246 titik / 133 spesies).

    File ini merupakan hasil merge seluruh koordinat & data botani tanaman
    herbal TNBTS, dan menjadi sumber data utama peta. Mengembalikan
    DataFrame dengan skema yang sama seperti load_herbal_data() lama
    (No, Nama, X, Y) ditambah kolom detail (NamaLatin, Fungsi,
    PotensiSebaran, SyaratHidup, CaraMemanfaatkan, BagianDimanfaatkan)
    yang diambil langsung dari properti GeoJSON, sehingga tidak lagi
    bergantung sepenuhnya pada dictionary HERBAL_DETAIL_DATA.
    """
    gdf = _load_geojson('sebaran_tanaman_herbal_TNBTS.geojson')
    if gdf.empty:
        return pd.DataFrame()

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        try:
            gdf = gdf.to_crs("EPSG:4326")
        except Exception as e:
            st.sidebar.error(f"❌ Gagal memproyeksikan GeoJSON tanaman herbal: {e}")
            return pd.DataFrame()

    records = []
    for i, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        lon, lat = geom.x, geom.y
        nama = str(row.get('nama_tanaman', '')).strip().upper()
        if not nama or nama == 'NONE':
            continue
        records.append({
            'No': i + 1,
            'Nama': nama,
            'X': lon,
            'Y': lat,
            'NamaLatin': row.get('nama_ilmiah', '') or '',
            'Fungsi': row.get('fungsi_manfaat', '') or '',
            'PotensiSebaran': row.get('potensi_sebaran', '') or '',
            'SyaratHidup': row.get('syarat_hidup', '') or '',
            'CaraMemanfaatkan': row.get('cara_memanfaatkan', '') or '',
            'BagianDimanfaatkan': row.get('bagian_dimanfaatkan', '') or '',
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
    """
    Membaca data sebaran tanaman herbal.

    Urutan prioritas sumber data:
      1. sebaran_tanaman_herbal_TNBTS.geojson — 246 titik / 133 spesies,
         atribut botani lengkap (sumber utama & paling mutakhir).
      2. Titik Rapihin.xlsx / .xls / .csv — berkas Excel/CSV lama.
      3. Data embedded HERBAL_DATA_EMBEDDED — fallback terakhir.
    """
    df_geojson = load_herbal_geojson()
    if not df_geojson.empty:
        return df_geojson

    # Coba baca dari file Excel
    filenames = ['Titik Rapihin.xlsx', 'Titik Rapihin.xls', 'Titik Rapihin.csv']
    
    for filename in filenames:
        filepath = _find_file(filename)
        if filepath:
            try:
                # Coba import openpyxl jika file .xlsx
                if filename.endswith('.xlsx'):
                    try:
                        import openpyxl
                    except ImportError:
                        # Jika openpyxl tidak terinstall, lanjut ke file berikutnya
                        continue
                
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
                    
                    # Tampilkan pesan sukses di sidebar
                    st.sidebar.success(f"✅ Memuat {len(result_df)} data dari {filename}")
                    return result_df
            except Exception as e:
                # Lewati error dan coba file berikutnya
                continue
    
    # Jika file tidak ditemukan, gunakan data embedded
    # Tampilkan pesan informatif di sidebar
    st.sidebar.info(f"📊 Menggunakan data tanaman herbal embedded ({len(HERBAL_DATA_EMBEDDED)} titik)")
    df = pd.DataFrame(HERBAL_DATA_EMBEDDED, columns=['No', 'Nama', 'X', 'Y'])
    return df


def get_plant_detail(plant_name, row=None):
    """
    Mendapatkan detail tanaman berdasarkan nama.

    Jika `row` (baris df_herbal hasil sebaran_tanaman_herbal_TNBTS.geojson)
    disediakan dan berisi kolom detail, atribut tersebut diprioritaskan
    karena bersumber langsung dari data botani terbaru. Jika `row` tidak
    diberikan, fungsi ini otomatis mencari baris pertama yang cocok di
    df_herbal (global) sehingga semua pemanggil tetap mendapat data
    terlengkap tanpa perlu diubah satu per satu. Dictionary
    HERBAL_DETAIL_DATA (embedded) dipakai sebagai pelengkap/fallback,
    misalnya untuk field 'foto' yang tidak ada di GeoJSON.
    """
    plant_name_clean = plant_name.upper().strip()

    if row is None and 'df_herbal' in globals() and not df_herbal.empty and 'NamaLatin' in df_herbal.columns:
        match = df_herbal[df_herbal['Nama'] == plant_name_clean]
        if not match.empty:
            row = match.iloc[0]

    # Detail dari baris GeoJSON (df_herbal)
    detail_from_row = None
    if row is not None and 'NamaLatin' in getattr(row, 'index', []):
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

    # Detail dari dictionary embedded (fallback / pelengkap foto)
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
    
    # Warna border berdasarkan highlight
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
        
        # Tambahkan foto jika ada
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


def create_plant_detail_card(plant_name):
    """Membuat kartu detail tanaman untuk ditampilkan di Data Tanaman."""
    detail = get_plant_detail(plant_name)
    
    if not detail:
        return """
        <div style="background: #fff3e0; border-radius: 8px; padding: 12px; 
                    border-left: 4px solid #FF9800; margin: 8px 0;">
            <span style="color: #E65100;">⚠️ Data detail tidak tersedia</span>
        </div>
        """
    
    html = f"""
    <div style="background: #f8f9fa; border-radius: 10px; padding: 16px; 
                margin: 8px 0; border: 1px solid #e0e0e0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    border-bottom: 2px solid #2E7D32; padding-bottom: 8px; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #1B5E20;">🌿 {plant_name}</h4>
            <span style="font-style: italic; color: #666; font-size: 14px;">{detail.get('nama_latin', '')}</span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
    """
    
    # Fungsi
    if detail.get('fungsi'):
        html += f"""
            <div style="grid-column: 1 / -1; background: #E8F5E9; border-radius: 6px; padding: 8px 12px;">
                <span style="font-weight: bold; color: #2E7D32;">💊 Fungsi:</span><br>
                <span style="font-size: 13px; color: #333;">{detail['fungsi']}</span>
            </div>
        """
    
    # Syarat Hidup
    if detail.get('syarat_hidup'):
        html += f"""
            <div style="background: #FFF8E1; border-radius: 6px; padding: 8px 12px; grid-column: 1 / 2;">
                <span style="font-weight: bold; color: #F57F17;">🌱 Syarat Hidup:</span><br>
                <span style="font-size: 12px; color: #555;">{detail['syarat_hidup'][:200]}{'...' if len(detail['syarat_hidup']) > 200 else ''}</span>
            </div>
        """
    
    # Cara Memanfaatkan
    if detail.get('cara_memanfaatkan'):
        html += f"""
            <div style="background: #E3F2FD; border-radius: 6px; padding: 8px 12px; grid-column: 2 / 3;">
                <span style="font-weight: bold; color: #0D47A1;">🔬 Cara Memanfaatkan:</span><br>
                <span style="font-size: 12px; color: #555;">{detail['cara_memanfaatkan'][:200]}{'...' if len(detail['cara_memanfaatkan']) > 200 else ''}</span>
            </div>
        """
    
    # Yang Dimanfaatkan
    if detail.get('yang_dimanfaatkan'):
        html += f"""
            <div style="background: #F3E5F5; border-radius: 6px; padding: 8px 12px; grid-column: 1 / 2;">
                <span style="font-weight: bold; color: #6A1B9A;">✂️ Yang Dimanfaatkan:</span><br>
                <span style="font-size: 13px; color: #555;">{detail['yang_dimanfaatkan']}</span>
            </div>
        """
    
    # Potensi Sebaran
    if detail.get('potensi_sebaran'):
        html += f"""
            <div style="background: #E0F7FA; border-radius: 6px; padding: 8px 12px; grid-column: 2 / 3;">
                <span style="font-weight: bold; color: #00695C;">📍 Potensi Sebaran:</span><br>
                <span style="font-size: 12px; color: #555;">{detail['potensi_sebaran']}</span>
            </div>
        """
    
    # Foto
    if detail.get('foto'):
        html += f"""
            <div style="grid-column: 1 / -1; background: #ECEFF1; border-radius: 6px; padding: 8px 12px; text-align: center;">
                <span style="font-weight: bold; color: #455A64;">📷 Foto:</span>
                <span style="font-size: 12px; color: #666; display: block;">{detail['foto']}</span>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html


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
    
    /* Sembunyikan pesan error/gagal di sidebar */
    [data-testid="stSidebar"] .stAlert {
        background: rgba(0,0,0,0.5) !important;
        color: white !important;
        border-color: rgba(255,255,255,0.2) !important;
    }
    [data-testid="stSidebar"] .stAlert svg {
        fill: #4CAF50 !important;
    }
    
    /* Sembunyikan pesan error spesifik */
    .stAlert .stMarkdown:contains("Gagal membaca") {
        display: none !important;
    }

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
    
    /* Status badge di sidebar */
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
    
    /* Highlight untuk tanaman rekomendasi */
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
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MUSIK (Floating Player) - LINK YOUTUBE BARU
# ─────────────────────────────────────────────────────────────────────────────
# Link YouTube: https://www.youtube.com/watch?v=NVY60XJuGKs&list=RDNVY60XJuGKs&start_radio=1&rv=Ep1C30KRYu8
# Video ID: NVY60XJuGKs
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
    # Mapping gejala ke tanaman
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
    
    # Simpan daftar tanaman yang direkomendasikan untuk highlight
    recommended_plants = []
    
    response += "**Rekomendasi Tanaman:**\n"
    for i, (_, row) in enumerate(results.head(5).iterrows()):
        plant_name = row['Nama']
        recommended_plants.append(plant_name)
        
        response += f"\n{i+1}. **{plant_name}**\n"
        response += f"   - Koordinat: {row['Y']:.6f}, {row['X']:.6f}\n"
        
        # Tambahkan detail jika tersedia
        detail = get_plant_detail(plant_name)
        if detail:
            if detail.get('fungsi'):
                response += f"   - Fungsi: {detail['fungsi'][:100]}...\n"
            if detail.get('cara_memanfaatkan'):
                response += f"   - Cara: {detail['cara_memanfaatkan'][:100]}...\n"
    
    if len(results) > 5:
        response += f"\n📋 **{len(results)-5} tanaman lainnya** dapat dilihat di Data Tanaman."
    
    response += "\n\n💡 **Catatan:** Selalu konsultasikan dengan ahli kesehatan sebelum mengonsumsi tanaman herbal."
    
    # Simpan daftar tanaman yang direkomendasikan di session state
    st.session_state.recommended_plants = recommended_plants
    
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
    gdf_desa, gdf_kabupaten, gdf_batas, df_tanaman_filtered, 
    highlight_points=None, show_only_highlighted=False
):
    """
    Membuat peta interaktif TNBTS.
    
    Parameters:
    - show_only_highlighted: Jika True, hanya menampilkan tanaman yang ada di highlight_points
    - highlight_points: List nama tanaman yang akan di-highlight (warna merah bintang)
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
        # Jika show_only_highlighted True, filter hanya tanaman yang di-highlight
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
                
                # Gunakan popup dengan detail lengkap (row = data dari GeoJSON)
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

# ═════════════════════════════════════════════════════════════════════════════
# MENU: WEBGIS SDM POTENSI HERBAL (LINK EKSTERNAL)
# ═════════════════════════════════════════════════════════════════════════════
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
        use_container_width=True,
        type="primary",
    )

# ═════════════════════════════════════════════════════════════════════════════
# MENU: CHATBOT HERBAL
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Tanya Mbah Dukun Herbal Digital":
    st.markdown("## 🤖 Mbah Dukun Herbal Digital TNBTS")
    
    # Inisialisasi recommended_plants jika belum ada
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
        send_button = st.button("📤 Kirim", use_container_width=True)
    
    if send_button and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        response = generate_chatbot_response_herbal(user_input, df_herbal)
        
        # Tanaman yang direkomendasikan sudah disimpan di generate_chatbot_response_herbal
        st.session_state.chat_history.append({'role': 'bot', 'content': response})
        st.rerun()
    
    if st.button("🗑️ Hapus Riwayat Chat"):
        st.session_state.chat_history = []
        st.session_state.recommended_plants = []
        st.rerun()
    
    # ─── PETA SEBARAN TANAMAN YANG DIREKOMENDASIKAN ────────────────────────
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
        
        # Filter data hanya untuk tanaman yang direkomendasikan
        df_recommended = df_herbal[df_herbal['Nama'].isin(st.session_state.recommended_plants)]
        
        if not df_recommended.empty:
            try:
                # Tampilkan hanya tanaman yang direkomendasikan dengan highlight
                m = create_tnbts_map(
                    show_desa_geojson=show_desa_geojson,
                    show_kabupaten=show_kabupaten,
                    show_batas_tnbts=show_batas_tnbts,
                    show_tanaman=show_tanaman,
                    gdf_desa=gdf_desa,
                    gdf_kabupaten=gdf_kabupaten,
                    gdf_batas=gdf_batas,
                    df_tanaman_filtered=df_recommended,  # Hanya data yang direkomendasikan
                    highlight_points=st.session_state.recommended_plants,
                    show_only_highlighted=True  # Hanya tampilkan yang direkomendasikan
                )
                folium_static(m, width=1200, height=500)
                
                # Tampilkan daftar tanaman yang direkomendasikan
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
        
        # Tampilkan data dengan detail
        st.markdown("### 📋 Data Tanaman dengan Detail Lengkap")
        st.markdown("Klik nama tanaman untuk melihat detail fungsi, syarat hidup, dan cara memanfaatkan.")
        
        # Buat expander untuk setiap tanaman unik
        unique_plants = sorted(df_show['Nama'].unique())
        
        if len(unique_plants) > 0:
            # Tampilkan dalam grid 2 kolom
            cols_per_row = 2
            for i in range(0, len(unique_plants), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(unique_plants):
                        plant_name = unique_plants[idx]
                        with col:
                            with st.expander(f"🌿 {plant_name}", expanded=False):
                                # Dapatkan detail tanaman
                                detail = get_plant_detail(plant_name)
                                
                                if detail:
                                    # Tampilkan detail dalam format yang rapi
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
                                    
                                    # Fungsi
                                    if detail.get('fungsi'):
                                        st.markdown(f"""
                                        <div style="background: #E8F5E9; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #2E7D32;">
                                            <span style="font-weight: bold; color: #1B5E20; font-size: 14px;">💊 Fungsi:</span><br>
                                            <span style="font-size: 13px; color: #333; line-height: 1.6;">{detail['fungsi']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Syarat Hidup
                                    if detail.get('syarat_hidup'):
                                        st.markdown(f"""
                                        <div style="background: #FFF8E1; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #F57F17;">
                                            <span style="font-weight: bold; color: #E65100; font-size: 14px;">🌱 Syarat Hidup:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.6;">{detail['syarat_hidup']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Cara Memanfaatkan
                                    if detail.get('cara_memanfaatkan'):
                                        st.markdown(f"""
                                        <div style="background: #E3F2FD; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #0D47A1;">
                                            <span style="font-weight: bold; color: #0D47A1; font-size: 14px;">🔬 Cara Memanfaatkan:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.6;">{detail['cara_memanfaatkan']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Grid untuk informasi tambahan
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
                                    
                                    # Potensi Sebaran
                                    if detail.get('potensi_sebaran'):
                                        st.markdown(f"""
                                        <div style="background: #E0F7FA; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border-left: 4px solid #00695C;">
                                            <span style="font-weight: bold; color: #00695C; font-size: 13px;">📍 Potensi Sebaran:</span><br>
                                            <span style="font-size: 12px; color: #555; line-height: 1.5;">{detail['potensi_sebaran']}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    # Tampilkan titik sebaran
                                    plant_points = df_show[df_show['Nama'] == plant_name]
                                    if len(plant_points) > 0:
                                        st.markdown(f"""
                                        <div style="background: #F5F5F5; border-radius: 8px; padding: 10px 14px; 
                                                    margin: 6px 0; border: 1px solid #ddd;">
                                            <span style="font-weight: bold; color: #555; font-size: 13px;">📍 Jumlah titik sebaran: {len(plant_points)}</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        # Tampilkan data dalam tabel kecil
                                        st.dataframe(
                                            plant_points[['No', 'X', 'Y']],
                                            use_container_width=True,
                                            hide_index=True,
                                            height=150
                                        )
                                else:
                                    st.warning(f"⚠️ Data detail untuk '{plant_name}' tidak tersedia")
                                    
                                    # Tetap tampilkan titik sebaran
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
        
        # Tombol download
        col_download1, col_download2, col_download3 = st.columns([1, 2, 1])
        with col_download2:
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
            detailed_count = len([n for n in df_herbal['Nama'].unique() if get_plant_detail(n) is not None])
            st.metric("Tanaman dengan Data Detail", detailed_count)

# ═════════════════════════════════════════════════════════════════════════════
# MENU: STATISTIK
# ═════════════════════════════════════════════════════════════════════════════
elif selected == "Statistik":
    st.markdown("## 📊 Statistik Tanaman Herbal TNBTS")
    
    st.markdown("### 🌿 Sebaran Spesies Tanaman")
    
    # Top tanaman
    top_counts = df_herbal['Nama'].value_counts().head(15)
    st.bar_chart(top_counts, use_container_width=True)
    
    # Tampilkan detail untuk top tanaman
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

# ═════════════════════════════════════════════════════════════════════════════
# HALAMAN: INFORMASI
# ═════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("## ℹ️ Informasi TNBTS")

    total_penduduk  = gdf_desa['jumlah_pen'].sum()    if not gdf_desa.empty and 'jumlah_pen'  in gdf_desa.columns else 0
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

    # ── Fungsi utama tanaman ──────────────────────────────────────────────────
    st.markdown("### 💊 Kelompok Fungsi Tanaman")
    
    # Tampilkan beberapa contoh tanaman dengan fungsinya
    st.markdown("""
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; margin: 12px 0;">
    """, unsafe_allow_html=True)
    
    shown = 0
    for name, detail in HERBAL_DETAIL_DATA.items():
        if shown >= 16:
            break
        if detail.get('fungsi'):
            fungsi_short = detail['fungsi'][:80] + ('...' if len(detail['fungsi']) > 80 else '')
            st.markdown(f"""
            <div style="background: #f8f9fa; border-radius: 8px; padding: 12px 16px; 
                        border-left: 4px solid #2E7D32; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-weight: bold; color: #2E7D32; font-size: 14px;">🌿 {name}</div>
                <div style="font-size: 12px; color: #555; margin-top: 4px;">{fungsi_short}</div>
                <div style="font-size: 11px; color: #888; margin-top: 2px; font-style: italic;">{detail.get('yang_dimanfaatkan', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            shown += 1
    
    st.markdown("</div>", unsafe_allow_html=True)

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
    - **Data Tanaman:** Hasil survei lapangan Tim Peneliti UB (2026) — 86 spesies, 8 kawasan ekologi
    - **Data Detail Tanaman:** Dokumentasi lengkap fungsi, syarat hidup, dan cara pemanfaatan
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
