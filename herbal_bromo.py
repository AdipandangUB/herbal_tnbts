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
