import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy.interpolate import griddata
import io

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="Model Geolistrik 3D Universal",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# DATABASE RESISTIVITAS TELFORD et al. (1990)
# Applied Geophysics, 2nd Edition - Cambridge University Press
# ============================================================
TELFORD_RESISTIVITY = {
    # ---------- SEDIMEN LUNAK / UNCONSOLIDATED ----------
    "Gambut (Peat)": {
        "min": 10, "max": 500,
        "color": "#8B4513", "group": "Sedimen Organik",
        "desc": "Material organik terdekomposisi, kadar air tinggi"
    },
    "Lempung (Clay)": {
        "min": 1, "max": 100,
        "color": "#708090", "group": "Sedimen Klastik Halus",
        "desc": "Sedimen berbutir sangat halus, plastisitas tinggi"
    },
    "Lempung Jenuh Air (Saturated Clay)": {
        "min": 1, "max": 20,
        "color": "#4682B4", "group": "Sedimen Klastik Halus",
        "desc": "Lempung yang tersaturasi oleh air tanah"
    },
    "Lanau (Silt)": {
        "min": 10, "max": 200,
        "color": "#D2B48C", "group": "Sedimen Klastik Halus",
        "desc": "Sedimen berbutir halus antara lempung dan pasir"
    },
    "Pasir Kering (Dry Sand)": {
        "min": 500, "max": 1500,
        "color": "#F4A460", "group": "Sedimen Klastik Kasar",
        "desc": "Pasir tidak jenuh, resistivitas tinggi"
    },
    "Pasir Jenuh Air (Wet Sand)": {
        "min": 10, "max": 100,
        "color": "#87CEEB", "group": "Sedimen Klastik Kasar",
        "desc": "Pasir tersaturasi air tanah tawar"
    },
    "Kerikil Kering (Dry Gravel)": {
        "min": 100, "max": 600,
        "color": "#A0A0A0", "group": "Sedimen Klastik Kasar",
        "desc": "Kerikil tidak jenuh air"
    },
    "Kerikil Jenuh Air (Wet Gravel)": {
        "min": 30, "max": 100,
        "color": "#7B9DB5", "group": "Sedimen Klastik Kasar",
        "desc": "Kerikil tersaturasi air tanah"
    },
    "Aluvium (Alluvium)": {
        "min": 10, "max": 800,
        "color": "#C8A882", "group": "Sedimen Klastik Kasar",
        "desc": "Endapan campuran pasir-kerikil-lempung dari sungai"
    },

    # ---------- BATUAN SEDIMEN KONSOLIDASI ----------
    "Batu Pasir (Sandstone)": {
        "min": 1, "max": 100000,
        "color": "#DEB887", "group": "Sedimen Konsolidasi",
        "desc": "Batuan sedimen klastik terkompaksi"
    },
    "Batu Lempung (Mudstone/Claystone)": {
        "min": 5, "max": 100,
        "color": "#808080", "group": "Sedimen Konsolidasi",
        "desc": "Batuan sedimen lempung terkompaksi"
    },
    "Serpih (Shale)": {
        "min": 20, "max": 2000,
        "color": "#696969", "group": "Sedimen Konsolidasi",
        "desc": "Batuan sedimen berbutir halus berlapis"
    },
    "Konglomerat (Conglomerate)": {
        "min": 200, "max": 10000,
        "color": "#BC8A5F", "group": "Sedimen Konsolidasi",
        "desc": "Batuan klastik kasar terkementasi"
    },
    "Batu Bara (Coal)": {
        "min": 1000, "max": 100000000,
        "color": "#1C1C1C", "group": "Sedimen Organik",
        "desc": "Batuan organik terkarbonisasi"
    },

    # ---------- BATUAN KARBONAT ----------
    "Batu Gamping (Limestone)": {
        "min": 50, "max": 10000000,
        "color": "#F5F5DC", "group": "Karbonat",
        "desc": "Batuan karbonat CaCO₃, variasi lebar tergantung rekahan"
    },
    "Dolomit (Dolomite)": {
        "min": 100, "max": 10000000,
        "color": "#E8E8E8", "group": "Karbonat",
        "desc": "Batuan karbonat CaMg(CO₃)₂"
    },

    # ---------- BATUAN VULKANIK ----------
    "Basalt (Basalt)": {
        "min": 10, "max": 10000000,
        "color": "#2F4F4F", "group": "Batuan Vulkanik",
        "desc": "Batuan beku ekstrusif mafik"
    },
    "Andesit (Andesite)": {
        "min": 100, "max": 100000,
        "color": "#708090", "group": "Batuan Vulkanik",
        "desc": "Batuan beku ekstrusif intermediet"
    },
    "Riolit (Rhyolite)": {
        "min": 1000, "max": 10000000,
        "color": "#FF6B6B", "group": "Batuan Vulkanik",
        "desc": "Batuan beku ekstrusif felsik"
    },
    "Tufa Vulkanik (Volcanic Tuff)": {
        "min": 20, "max": 2000,
        "color": "#BDB76B", "group": "Batuan Vulkanik",
        "desc": "Material piroklastik halus terkompaksi"
    },
    "Breksi Vulkanik (Volcanic Breccia)": {
        "min": 100, "max": 10000,
        "color": "#8B7355", "group": "Batuan Vulkanik",
        "desc": "Material piroklastik kasar terkementasi"
    },

    # ---------- BATUAN BEKU INTRUSI ----------
    "Granit (Granite)": {
        "min": 100, "max": 1000000,
        "color": "#FF69B4", "group": "Batuan Beku Intrusi",
        "desc": "Batuan beku intrusif felsik kasar"
    },
    "Diorit (Diorite)": {
        "min": 100, "max": 100000,
        "color": "#C0C0C0", "group": "Batuan Beku Intrusi",
        "desc": "Batuan beku intrusif intermediet"
    },
    "Gabro (Gabbro)": {
        "min": 1000, "max": 10000000,
        "color": "#2D3436", "group": "Batuan Beku Intrusi",
        "desc": "Batuan beku intrusif mafik"
    },

    # ---------- BATUAN METAMORF ----------
    "Kuarsit (Quartzite)": {
        "min": 100, "max": 200000000,
        "color": "#F5DEB3", "group": "Metamorf",
        "desc": "Metamorf dari batu pasir kuarsa"
    },
    "Marmer (Marble)": {
        "min": 100, "max": 250000000,
        "color": "#FFFACD", "group": "Metamorf",
        "desc": "Metamorf dari batu gamping"
    },
    "Sekis (Schist)": {
        "min": 20, "max": 10000,
        "color": "#556B2F", "group": "Metamorf",
        "desc": "Metamorf berderajat menengah, foliasi kuat"
    },
    "Gneis (Gneiss)": {
        "min": 100, "max": 10000000,
        "color": "#8FBC8F", "group": "Metamorf",
        "desc": "Metamorf berderajat tinggi"
    },
    "Filit (Phyllite)": {
        "min": 10, "max": 1000,
        "color": "#6B8E23", "group": "Metamorf",
        "desc": "Metamorf berderajat rendah-menengah"
    },

    # ---------- TANAH & REGOLITH ----------
    "Laterit (Laterite)": {
        "min": 100, "max": 10000,
        "color": "#CD5C5C", "group": "Tanah & Regolith",
        "desc": "Tanah pelapukan tropis kaya Fe-Al oksida"
    },
    "Tanah Pelapukan (Residual Soil)": {
        "min": 10, "max": 500,
        "color": "#A0522D", "group": "Tanah & Regolith",
        "desc": "Hasil pelapukan in-situ batuan dasar"
    },

    # ---------- FLUIDA ----------
    "Air Tanah Tawar (Fresh Groundwater)": {
        "min": 10, "max": 100,
        "color": "#0000CD", "group": "Fluida",
        "desc": "Akuifer air tanah tawar"
    },
    "Air Tanah Payau (Brackish Water)": {
        "min": 1, "max": 10,
        "color": "#00BFFF", "group": "Fluida",
        "desc": "Air tanah dengan salinitas menengah"
    },
    "Air Tanah Asin (Saline/Sea Water)": {
        "min": 0.05, "max": 3,
        "color": "#00CED1", "group": "Fluida",
        "desc": "Air laut atau air tanah salinitas tinggi"
    },
}

# ============================================================
# KONFIGURASI GEOLOGI REGIONAL
# Setiap setting geologi memiliki daftar litologi yang relevan
# ============================================================
REGIONAL_GEOLOGY = {
    "── Semua Litologi (Tanpa Filter) ──": {
        "desc": "Gunakan seluruh tabel Telford tanpa filter regional",
        "icon": "🌐",
        "lithologies": list(TELFORD_RESISTIVITY.keys())
    },
    "Aluvium / Dataran Banjir (Alluvial Plain)": {
        "desc": "Endapan sungai dan dataran banjir: lempung, lanau, pasir, kerikil, gambut",
        "icon": "🏞️",
        "lithologies": [
            "Gambut (Peat)", "Lempung (Clay)", "Lempung Jenuh Air (Saturated Clay)",
            "Lanau (Silt)", "Pasir Kering (Dry Sand)", "Pasir Jenuh Air (Wet Sand)",
            "Kerikil Kering (Dry Gravel)", "Kerikil Jenuh Air (Wet Gravel)",
            "Aluvium (Alluvium)", "Air Tanah Tawar (Fresh Groundwater)",
            "Tanah Pelapukan (Residual Soil)"
        ]
    },
    "Rawa / Lahan Gambut (Peatland/Swamp)": {
        "desc": "Lahan basah dengan dominasi material organik dan sedimen jenuh air",
        "icon": "🌿",
        "lithologies": [
            "Gambut (Peat)", "Lempung (Clay)", "Lempung Jenuh Air (Saturated Clay)",
            "Lanau (Silt)", "Pasir Jenuh Air (Wet Sand)", "Aluvium (Alluvium)",
            "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Delta / Pesisir (Deltaic/Coastal)": {
        "desc": "Endapan delta dan pesisir: pasir, lempung, kemungkinan intrusi air asin",
        "icon": "🏖️",
        "lithologies": [
            "Pasir Kering (Dry Sand)", "Pasir Jenuh Air (Wet Sand)",
            "Lempung (Clay)", "Lempung Jenuh Air (Saturated Clay)",
            "Lanau (Silt)", "Kerikil Jenuh Air (Wet Gravel)", "Gambut (Peat)",
            "Aluvium (Alluvium)", "Air Tanah Tawar (Fresh Groundwater)",
            "Air Tanah Payau (Brackish Water)", "Air Tanah Asin (Saline/Sea Water)"
        ]
    },
    "Sedimen Tersier (Tertiary Sedimentary Basin)": {
        "desc": "Cekungan sedimen Tersier: batu pasir, serpih, batu gamping, batu bara",
        "icon": "🪨",
        "lithologies": [
            "Batu Pasir (Sandstone)", "Serpih (Shale)", "Batu Lempung (Mudstone/Claystone)",
            "Batu Gamping (Limestone)", "Konglomerat (Conglomerate)", "Batu Bara (Coal)",
            "Lempung (Clay)", "Pasir Jenuh Air (Wet Sand)", "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Formasi Karbonat (Carbonate Formation)": {
        "desc": "Batu gamping dan dolomit, sering berasosiasi dengan akifer karst",
        "icon": "🏔️",
        "lithologies": [
            "Batu Gamping (Limestone)", "Dolomit (Dolomite)", "Lempung (Clay)",
            "Pasir Jenuh Air (Wet Sand)", "Batu Pasir (Sandstone)",
            "Air Tanah Tawar (Fresh Groundwater)", "Serpih (Shale)"
        ]
    },
    "Vulkanik (Volcanic Terrain)": {
        "desc": "Daerah vulkanik aktif/tidak aktif: andesit, basalt, tuf, breksi",
        "icon": "🌋",
        "lithologies": [
            "Basalt (Basalt)", "Andesit (Andesite)", "Riolit (Rhyolite)",
            "Tufa Vulkanik (Volcanic Tuff)", "Breksi Vulkanik (Volcanic Breccia)",
            "Laterit (Laterite)", "Tanah Pelapukan (Residual Soil)",
            "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Batuan Beku Intrusi (Intrusive Igneous)": {
        "desc": "Pluton granit, diorit, gabro dengan zona pelapukan di atasnya",
        "icon": "💎",
        "lithologies": [
            "Granit (Granite)", "Diorit (Diorite)", "Gabro (Gabbro)",
            "Andesit (Andesite)", "Laterit (Laterite)",
            "Tanah Pelapukan (Residual Soil)", "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Kompleks Metamorf (Metamorphic Complex)": {
        "desc": "Batuan metamorf: kuarsit, marmer, sekis, gneis, filit",
        "icon": "🔮",
        "lithologies": [
            "Kuarsit (Quartzite)", "Marmer (Marble)", "Sekis (Schist)",
            "Gneis (Gneiss)", "Filit (Phyllite)",
            "Tanah Pelapukan (Residual Soil)", "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Batuan Pra-Tersier (Pre-Tertiary Basement)": {
        "desc": "Batuan dasar berumur Mesozoik-Paleozoik: gamping, kuarsit, granit",
        "icon": "🏛️",
        "lithologies": [
            "Batu Gamping (Limestone)", "Batu Pasir (Sandstone)", "Serpih (Shale)",
            "Kuarsit (Quartzite)", "Granit (Granite)", "Diorit (Diorite)",
            "Breksi Vulkanik (Volcanic Breccia)", "Dolomit (Dolomite)",
            "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
    "Profil Pelapukan / Laterit (Weathering Profile)": {
        "desc": "Zona pelapukan intensif tropis: laterit di atas batuan dasar",
        "icon": "🌱",
        "lithologies": [
            "Laterit (Laterite)", "Tanah Pelapukan (Residual Soil)",
            "Lempung (Clay)", "Serpih (Shale)", "Granit (Granite)",
            "Basalt (Basalt)", "Air Tanah Tawar (Fresh Groundwater)"
        ]
    },
}

# ============================================================
# FUNGSI KLASIFIKASI LITOLOGI
# ============================================================
def hitung_skor_kesesuaian(resistivity, rho_min, rho_max):
    """
    Hitung skor kesesuaian nilai resistivitas terhadap rentang litologi
    menggunakan skala logaritmik (0-100%)
    """
    if resistivity <= 0:
        return 0.0
    
    log_r   = np.log10(resistivity)
    log_min = np.log10(max(rho_min, 1e-10))
    log_max = np.log10(rho_max)
    
    if log_min <= log_r <= log_max:
        log_center   = (log_min + log_max) / 2.0
        half_range   = (log_max - log_min) / 2.0
        dist_center  = abs(log_r - log_center)
        score = (1.0 - dist_center / max(half_range, 1e-10)) * 100.0
        return round(max(score, 0.0), 1)
    return 0.0


def klasifikasi_litologi(resistivity_value, active_lithologies):
    """
    Klasifikasikan nilai resistivitas berdasarkan tabel Telford,
    difilter oleh daftar litologi aktif (dari geologi regional).
    Mengembalikan list litologi yang cocok, diurutkan dari skor tertinggi.
    """
    hasil = []
    
    for nama in active_lithologies:
        if nama not in TELFORD_RESISTIVITY:
            continue
        data  = TELFORD_RESISTIVITY[nama]
        skor  = hitung_skor_kesesuaian(resistivity_value, data["min"], data["max"])
        if skor > 0:
            hasil.append({
                "lithology": nama,
                "score":     skor,
                "min":       data["min"],
                "max":       data["max"],
                "color":     data["color"],
                "group":     data["group"],
                "desc":      data["desc"]
            })
    
    hasil.sort(key=lambda x: x["score"], reverse=True)
    
    # Jika tidak ada yang cocok, cari yang paling dekat
    if not hasil:
        terdekat = None
        jarak_min = float('inf')
        
        for nama in active_lithologies:
            if nama not in TELFORD_RESISTIVITY:
                continue
            data  = TELFORD_RESISTIVITY[nama]
            log_r = np.log10(max(resistivity_value, 1e-10))
            log_a = np.log10(max(data["min"], 1e-10))
            log_b = np.log10(data["max"])
            
            if log_r < log_a:
                jarak = log_a - log_r
            elif log_r > log_b:
                jarak = log_r - log_b
            else:
                jarak = 0
            
            if jarak < jarak_min:
                jarak_min = jarak
                terdekat = {
                    "lithology": nama,
                    "score":     max(0.0, round((1 - jarak_min) * 50, 1)),
                    "min":       data["min"],
                    "max":       data["max"],
                    "color":     data["color"],
                    "group":     data["group"],
                    "desc":      data["desc"],
                    "note":      "⚠️ Di luar rentang – estimasi terdekat"
                }
        
        if terdekat:
            hasil = [terdekat]
    
    return hasil


def get_primary_lithology(rho, active_lithologies):
    hasil = klasifikasi_litologi(rho, active_lithologies)
    return hasil[0]["lithology"] if hasil else "Tidak Teridentifikasi"


def get_primary_color(rho, active_lithologies):
    hasil = klasifikasi_litologi(rho, active_lithologies)
    return hasil[0]["color"] if hasil else "#888888"


def get_primary_score(rho, active_lithologies):
    hasil = klasifikasi_litologi(rho, active_lithologies)
    return hasil[0]["score"] if hasil else 0.0


# ============================================================
# FUNGSI GENERATE DATA SAMPEL
# ============================================================
def buat_data_sampel(geologi_regional):
    """Buat data sampel sintetis sesuai geologi regional"""
    np.random.seed(42)
    
    # Tentukan distribusi resistivitas berdasarkan geologi regional
    template = {
        "Aluvium / Dataran Banjir (Alluvial Plain)": [
            (12, 50, 60),   # Lempung/gambut
            (50, 200, 80),  # Lanau/pasir jenuh
            (200, 700, 60), # Kerikil/pasir
        ],
        "Rawa / Lahan Gambut (Peatland/Swamp)": [
            (10, 80, 100),  # Gambut
            (1, 20, 80),    # Lempung jenuh
            (20, 100, 20),  # Pasir jenuh
        ],
        "Vulkanik (Volcanic Terrain)": [
            (20, 200, 50),    # Tuf / tanah pelapukan
            (200, 5000, 80),  # Andesit / breksi
            (5000, 50000, 70),# Andesit segar
        ],
        "Sedimen Tersier (Tertiary Sedimentary Basin)": [
            (5, 50, 60),     # Serpih / batu lempung
            (50, 500, 80),   # Batu pasir
            (500, 5000, 60), # Batu pasir kompak
        ],
    }
    
    if geologi_regional in template:
        ranges = template[geologi_regional]
    else:
        ranges = [(10, 100, 70), (100, 1000, 80), (1000, 10000, 50)]
    
    data_list = []
    for (rmin, rmax, n) in ranges:
        r_vals = np.random.uniform(rmin, rmax, n)
        x_vals = np.random.uniform(0, 100, n)
        y_vals = np.random.uniform(0, 100, n)
        z_vals = np.random.choice([-2, -4, -6, -8, -10, -12, -15], n)
        for x, y, z, r in zip(x_vals, y_vals, z_vals, r_vals):
            data_list.append({"X": x, "Y": y, "Z": z, "Resistivity": r})
    
    return pd.DataFrame(data_list)


# ============================================================
# APLIKASI UTAMA
# ============================================================
def main():
    # ---------- HEADER ----------
    st.title("🌍 Model Geolistrik 3D — Identifikasi Litologi Universal")
    st.markdown(
        "**Interpretasi resistivitas geolistrik berbasis Tabel Telford et al. (1990), "
        "disesuaikan dengan kondisi geologi regional.**"
    )
    st.divider()

    # ============================================================
    # SIDEBAR — Pengaturan Geologi Regional
    # ============================================================
    with st.sidebar:
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/"
            "Earth_layers_diagram.svg/300px-Earth_layers_diagram.svg.png",
            use_column_width=True
        )
        st.header("⚙️ Pengaturan")

        # ── Geologi Regional ──
        st.subheader("🗺️ Kondisi Geologi Regional")
        geo_names = list(REGIONAL_GEOLOGY.keys())
        selected_geo = st.selectbox(
            "Pilih geologi regional lokasi survei:",
            options=geo_names,
            index=0,
            help="Menentukan jenis litologi yang relevan untuk dipertimbangkan dalam klasifikasi"
        )

        geo_cfg = REGIONAL_GEOLOGY[selected_geo]
        active_lithologies = geo_cfg["lithologies"]

        if selected_geo != geo_names[0]:
            st.info(f"📋 {geo_cfg['desc']}")
            with st.expander(f"✅ {len(active_lithologies)} litologi aktif"):
                for lit in active_lithologies:
                    if lit in TELFORD_RESISTIVITY:
                        d = TELFORD_RESISTIVITY[lit]
                        st.markdown(
                            f"<span style='color:{d['color']}'>■</span> "
                            f"**{lit}**  \n`{d['min']} – {d['max']} Ω·m`",
                            unsafe_allow_html=True
                        )

        st.divider()

        # ── Info Survei ──
        st.subheader("📝 Info Survei")
        loc_name    = st.text_input("Nama Lokasi:", placeholder="e.g., Desa Sungai Besar")
        formation   = st.text_input("Nama Formasi:", placeholder="e.g., Formasi Muara Enim")
        operator    = st.text_input("Operator:", placeholder="e.g., Kementerian ESDM")

        st.divider()

        # ── Opsi Visualisasi ──
        st.subheader("🎨 Opsi Visualisasi")
        colorscale  = st.selectbox("Colorscale (resistivitas):", ["Jet", "Viridis", "Plasma", "Rainbow", "RdBu_r"])
        opacity_3d  = st.slider("Opacity Model 3D:", 0.1, 1.0, 0.75, 0.05)
        marker_size = st.slider("Ukuran Marker:", 2, 12, 5)
        color_by    = st.radio("Warnai berdasarkan:", ["Litologi", "Nilai Resistivitas"])

    # ============================================================
    # TABS UTAMA
    # ============================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Input Data",
        "🔬 Klasifikasi Litologi",
        "🌐 Model 3D",
        "📊 Analisis Statistik",
        "📖 Referensi Telford"
    ])

    # ======================================================
    # TAB 1 — INPUT DATA
    # ======================================================
    with tab1:
        st.header("📂 Input Data Geolistrik")

        col_up, col_fmt = st.columns([1, 1])

        with col_up:
            st.subheader("Upload Data")
            uploaded = st.file_uploader(
                "Upload CSV atau Excel:",
                type=["csv", "xlsx", "xls"],
                help="Kolom wajib: X, Y, Z, Resistivity (Ω·m)"
            )

        with col_fmt:
            st.subheader("Format yang Diperlukan")
            st.markdown("""
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| **X** | Float | Koordinat Easting (m) |
| **Y** | Float | Koordinat Northing (m) |
| **Z** | Float | Kedalaman negatif (m), misal: -5.0 |
| **Resistivity** | Float | Nilai resistivitas (Ω·m) |
            """)

            use_sample = st.button("🔄 Gunakan Data Sampel", type="primary")

        # -- Load Data --
        df = None

        if uploaded is not None:
            try:
                if uploaded.name.endswith(".csv"):
                    df = pd.read_csv(uploaded)
                else:
                    df = pd.read_excel(uploaded)

                # Normalisasi nama kolom
                df.columns = [c.strip() for c in df.columns]

                # Cari kolom resistivitas secara fleksibel
                resist_col = None
                for c in df.columns:
                    if any(kw in c.lower() for kw in ["resist", "rho", "ohm", "tahanan", "ρ"]):
                        resist_col = c
                        break

                if resist_col is None:
                    st.error("❌ Kolom resistivitas tidak ditemukan. Pastikan ada kolom bernama 'Resistivity' atau 'Rho'.")
                else:
                    st.success(f"✅ Data dimuat: **{len(df)} titik** | Kolom resistivitas: `{resist_col}`")
                    st.session_state["df"] = df
                    st.session_state["resist_col"] = resist_col
                    st.dataframe(df.head(15), use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error: {e}")

        if use_sample or st.session_state.get("use_sample_flag", False):
            st.session_state["use_sample_flag"] = True
            df = buat_data_sampel(selected_geo)
            st.session_state["df"] = df
            st.session_state["resist_col"] = "Resistivity"
            st.success(f"✅ Data sampel untuk **{selected_geo}** dimuat: {len(df)} titik")
            st.dataframe(df.head(10), use_container_width=True)

    # ======================================================
    # TAB 2 — KLASIFIKASI LITOLOGI
    # ======================================================
    with tab2:
        st.header("🔬 Klasifikasi Litologi Berdasarkan Tabel Telford")

        # ── Panel Cek Manual ──
        st.subheader("🔍 Cek Nilai Resistivitas Secara Manual")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            test_rho = st.number_input(
                "Masukkan nilai resistivitas (Ω·m):",
                min_value=0.001, max_value=1e9,
                value=50.0, format="%.3f"
            )
            run_check = st.button("🔎 Identifikasi Sekarang", type="primary")

        with col_b:
            if selected_geo != geo_names[0]:
                st.success(
                    f"🗺️ **Geologi Regional:** {selected_geo}\n\n"
                    f"Hasil difilter untuk **{len(active_lithologies)} litologi** yang relevan."
                )
            else:
                st.warning("⚠️ Belum memilih geologi regional — semua litologi dipertimbangkan.")

        if run_check:
            results = klasifikasi_litologi(test_rho, active_lithologies)
            st.subheader(f"📋 Hasil Identifikasi: ρ = {test_rho:.2f} Ω·m")

            if results:
                for i, res in enumerate(results[:6]):
                    with st.container():
                        cols = st.columns([0.05, 3, 2, 1])
                        badge = "🥇" if i == 0 else ("🥈" if i == 1 else f"{i+1}.")
                        cols[0].markdown(badge)
                        cols[1].markdown(
                            f"**{res['lithology']}**  \n"
                            f"<small style='color:gray'>{res['group']} — {res['desc']}</small>",
                            unsafe_allow_html=True
                        )
                        cols[2].metric(
                            "Rentang (Ω·m)",
                            f"{res['min']:,} – {res['max']:,}"
                        )
                        cols[3].metric("Kesesuaian", f"{res['score']}%")
                        st.progress(res["score"] / 100)
                        if "note" in res:
                            st.caption(res["note"])
                        if i < len(results) - 1:
                            st.divider()

                # Interpretasi akhir
                st.success(
                    f"✅ **Interpretasi Utama:** {results[0]['lithology']} "
                    f"({results[0]['score']}% kesesuaian)\n\n"
                    f"*Berdasarkan geologi regional: {selected_geo}*"
                )
            else:
                st.error("Tidak ada litologi yang cocok.")

        st.divider()

        # ── Klasifikasi Batch ──
        st.subheader("🚀 Klasifikasi Otomatis Seluruh Data")

        if "df" not in st.session_state:
            st.info("📌 Upload data atau gunakan data sampel di tab **Input Data** terlebih dahulu.")
        else:
            df_raw       = st.session_state["df"].copy()
            resist_col   = st.session_state["resist_col"]

            if st.button("▶️ Jalankan Klasifikasi Batch", type="primary"):
                with st.spinner("Mengklasifikasikan data..."):
                    df_raw["Litologi_Primer"]   = df_raw[resist_col].apply(
                        lambda r: get_primary_lithology(r, active_lithologies)
                    )
                    df_raw["Skor_Kesesuaian_%"] = df_raw[resist_col].apply(
                        lambda r: get_primary_score(r, active_lithologies)
                    )
                    df_raw["Geologi_Regional"]  = selected_geo
                    df_raw["Warna_Litologi"]     = df_raw[resist_col].apply(
                        lambda r: get_primary_color(r, active_lithologies)
                    )
                    st.session_state["df_classified"] = df_raw
                    st.session_state["resist_col"]    = resist_col

                st.success(f"✅ Selesai! {len(df_raw)} titik diklasifikasikan.")
                st.dataframe(
                    df_raw[["X", "Y", "Z", resist_col, "Litologi_Primer", "Skor_Kesesuaian_%", "Geologi_Regional"]],
                    use_container_width=True
                )

                # Pie chart ringkasan
                litho_count = df_raw["Litologi_Primer"].value_counts().reset_index()
                litho_count.columns = ["Litologi", "Jumlah"]
                color_map = {
                    row["Litologi"]: TELFORD_RESISTIVITY.get(row["Litologi"], {}).get("color", "#999")
                    for _, row in litho_count.iterrows()
                }

                col_pie, col_bar = st.columns([1, 1])
                with col_pie:
                    fig_pie = go.Figure(go.Pie(
                        labels=litho_count["Litologi"],
                        values=litho_count["Jumlah"],
                        marker_colors=[color_map[l] for l in litho_count["Litologi"]],
                        hole=0.35
                    ))
                    fig_pie.update_layout(title="Distribusi Litologi", height=400)
                    st.plotly_chart(fig_pie, use_container_width=True)

                with col_bar:
                    fig_bar = px.bar(
                        litho_count, x="Jumlah", y="Litologi",
                        orientation="h",
                        color="Litologi",
                        color_discrete_map=color_map,
                        title="Jumlah Titik per Litologi"
                    )
                    fig_bar.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_bar, use_container_width=True)

                # Download
                csv_out = df_raw.drop(columns=["Warna_Litologi"], errors="ignore").to_csv(index=False)
                st.download_button(
                    "⬇️ Download Hasil (CSV)",
                    data=csv_out,
                    file_name="klasifikasi_geolistrik.csv",
                    mime="text/csv"
                )

    # ======================================================
    # TAB 3 — MODEL 3D
    # ======================================================
    with tab3:
        st.header("🌐 Visualisasi Model 3D Geolistrik")

        df_vis = st.session_state.get("df_classified", st.session_state.get("df", None))

        if df_vis is None:
            st.warning("⚠️ Silakan upload data di tab **Input Data** terlebih dahulu.")
        else:
            resist_col = st.session_state.get("resist_col", "Resistivity")

            try:
                x_arr = df_vis["X"].values
                y_arr = df_vis["Y"].values
                z_arr = df_vis["Z"].values
                r_arr = df_vis[resist_col].values

                fig3d = go.Figure()

                if color_by == "Litologi" and "Litologi_Primer" in df_vis.columns:
                    for litho_name in df_vis["Litologi_Primer"].unique():
                        mask  = df_vis["Litologi_Primer"] == litho_name
                        clr   = TELFORD_RESISTIVITY.get(litho_name, {}).get("color", "#888888")
                        subset = df_vis[mask]

                        fig3d.add_trace(go.Scatter3d(
                            x=subset["X"], y=subset["Y"], z=subset["Z"],
                            mode="markers",
                            marker=dict(size=marker_size, color=clr, opacity=opacity_3d),
                            name=litho_name,
                            customdata=np.stack([subset[resist_col].values,
                                                 subset.get("Skor_Kesesuaian_%", pd.Series(np.zeros(len(subset)))).values], axis=-1),
                            hovertemplate=(
                                "<b>%{fullData.name}</b><br>"
                                "X: %{x:.1f} m<br>Y: %{y:.1f} m<br>Z: %{z:.1f} m<br>"
                                "ρ = %{customdata[0]:.2f} Ω·m<br>"
                                "Kesesuaian: %{customdata[1]:.1f}%<extra></extra>"
                            )
                        ))
                else:
                    fig3d.add_trace(go.Scatter3d(
                        x=x_arr, y=y_arr, z=z_arr,
                        mode="markers",
                        marker=dict(
                            size=marker_size,
                            color=np.log10(np.maximum(r_arr, 0.01)),
                            colorscale=colorscale,
                            opacity=opacity_3d,
                            colorbar=dict(title="log₁₀(ρ) [Ω·m]", thickness=15),
                            showscale=True
                        ),
                        text=[f"ρ = {v:.1f} Ω·m" for v in r_arr],
                        hovertemplate="<b>%{text}</b><br>X:%{x:.1f} Y:%{y:.1f} Z:%{z:.1f}<extra></extra>"
                    ))

                title_txt = f"Model 3D Geolistrik"
                if loc_name:
                    title_txt += f" — {loc_name}"
                subtitle = f"Geologi Regional: {selected_geo}"
                if formation:
                    subtitle += f" | Formasi: {formation}"

                fig3d.update_layout(
                    title=dict(text=f"{title_txt}<br><sup>{subtitle}</sup>", x=0.5),
                    scene=dict(
                        xaxis_title="X / Easting (m)",
                        yaxis_title="Y / Northing (m)",
                        zaxis_title="Kedalaman (m)",
                        bgcolor="rgba(245,245,250,1)"
                    ),
                    legend=dict(
                        x=0, y=1,
                        bgcolor="rgba(255,255,255,0.85)",
                        bordercolor="#ccc", borderwidth=1
                    ),
                    height=700,
                )

                st.plotly_chart(fig3d, use_container_width=True)

                # Statistik cepat
                with st.expander("📊 Statistik Resistivitas"):
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Min ρ",    f"{r_arr.min():.2f} Ω·m")
                    c2.metric("Max ρ",    f"{r_arr.max():.2f} Ω·m")
                    c3.metric("Rata-rata",f"{r_arr.mean():.2f} Ω·m")
                    c4.metric("Median",   f"{np.median(r_arr):.2f} Ω·m")
                    c5.metric("Std Dev",  f"{r_arr.std():.2f} Ω·m")

            except Exception as e:
                st.error(f"❌ Error model 3D: {e}")

    # ======================================================
    # TAB 4 — ANALISIS STATISTIK
    # ======================================================
    with tab4:
        st.header("📊 Analisis Statistik")

        df_stat = st.session_state.get("df_classified", st.session_state.get("df", None))

        if df_stat is None:
            st.info("📌 Data belum tersedia.")
        else:
            resist_col = st.session_state.get("resist_col", "Resistivity")
            r_arr = df_stat[resist_col].values

            # Histogram
            fig_hist = px.histogram(
                df_stat, x=resist_col, nbins=50,
                title="Distribusi Nilai Resistivitas",
                labels={resist_col: "Resistivitas (Ω·m)"},
                log_x=True
            )
            fig_hist.update_layout(bargap=0.05)
            st.plotly_chart(fig_hist, use_container_width=True)

            # Cross-section by depth
            if "Z" in df_stat.columns:
                depths = sorted(df_stat["Z"].unique())
                selected_depth = st.select_slider(
                    "Pilih Slice Kedalaman (m):", options=depths
                )
                slice_df = df_stat[df_stat["Z"] == selected_depth]

                if not slice_df.empty and "X" in slice_df.columns and "Y" in slice_df.columns:
                    fig_slice = px.scatter(
                        slice_df, x="X", y="Y",
                        color=resist_col if color_by == "Nilai Resistivitas" else "Litologi_Primer",
                        color_continuous_scale=colorscale if color_by == "Nilai Resistivitas" else None,
                        title=f"Peta Resistivitas pada Kedalaman Z = {selected_depth} m",
                        labels={resist_col: "ρ (Ω·m)"},
                        size_max=15,
                        hover_data=["Litologi_Primer"] if "Litologi_Primer" in slice_df.columns else None
                    )
                    fig_slice.update_traces(marker=dict(size=12))
                    fig_slice.update_layout(height=500)
                    st.plotly_chart(fig_slice, use_container_width=True)

    # ======================================================
    # TAB 5 — REFERENSI TELFORD
    # ======================================================
    with tab5:
        st.header("📖 Tabel Referensi Resistivitas Telford et al. (1990)")

        st.markdown("""
> **Sumber Utama:**  
> Telford, W.M., Geldart, L.P., & Sheriff, R.E. (1990). *Applied Geophysics* (2nd ed.).  
> Cambridge University Press. ISBN: 978-0521339113

Tabel ini menjadi **standar internasional** dalam interpretasi data geolistrik,  
digunakan secara luas oleh peneliti dan praktisi geofisika di seluruh dunia.
        """)

        # Filter per kelompok
        all_groups = sorted(set(v["group"] for v in TELFORD_RESISTIVITY.values()))
        sel_groups = st.multiselect(
            "Filter kelompok batuan:",
            options=all_groups, default=all_groups
        )

        rows = []
        for nama, data in TELFORD_RESISTIVITY.items():
            if data["group"] in sel_groups:
                rows.append({
                    "Jenis Batuan / Material": nama,
                    "Kelompok": data["group"],
                    "ρ Min (Ω·m)": data["min"],
                    "ρ Max (Ω·m)": data["max"],
                    "Deskripsi": data["desc"]
                })

        tbl_df = pd.DataFrame(rows)
        st.dataframe(tbl_df, use_container_width=True, hide_index=True)

        st.subheader("📈 Grafik Rentang Resistivitas")

        filtered_dict = {k: v for k, v in TELFORD_RESISTIVITY.items() if v["group"] in sel_groups}
        fig_range = go.Figure()

        for nama, data in filtered_dict.items():
            fig_range.add_trace(go.Scatter(
                x=[data["min"], data["max"]],
                y=[nama, nama],
                mode="lines+markers",
                line=dict(color=data["color"], width=10),
                marker=dict(size=8, color=data["color"]),
                showlegend=False,
                hovertemplate=(
                    f"<b>{nama}</b><br>"
                    f"Min: {data['min']:,} Ω·m<br>"
                    f"Max: {data['max']:,} Ω·m<extra></extra>"
                )
            ))

        fig_range.update_layout(
            xaxis=dict(type="log", title="Resistivitas (Ω·m)", gridcolor="lightgray"),
            yaxis=dict(title="", autorange="reversed"),
            height=max(500, len(filtered_dict) * 28),
            title="Rentang Resistivitas Batuan & Material (Skala Log)",
            margin=dict(l=300),
            plot_bgcolor="rgba(250,250,250,1)"
        )

        st.plotly_chart(fig_range, use_container_width=True)


# ============================================================
if __name__ == "__main__":
    # Inisialisasi session state
    if "use_sample_flag" not in st.session_state:
        st.session_state["use_sample_flag"] = False

    main()
