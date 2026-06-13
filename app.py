import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata
import io

# ============================================================
# KONFIGURASI HALAMAN
# ============================================================
st.set_page_config(
    page_title="🌍 Model 3D Geolistrik Resistivitas",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# TABEL TELFORD – REFERENSI RESISTIVITAS BATUAN
# (Telford et al., 1990 – Applied Geophysics)
# ============================================================
TELFORD_TABLE = {
    # nama_litologi : (resistivitas_min, resistivitas_maks, deskripsi)
    "Air (fresh water)":          (10,     100,    "Air tanah tawar"),
    "Air (salt water)":           (0.01,   1.0,    "Air asin / air laut"),
    "Gambut / Peat":              (1,      100,    "Material organik terdekomposisi"),
    "Lempung / Clay":             (1,      100,    "Mineral lempung, permeabilitas rendah"),
    "Lumpur / Mud":               (1,      20,     "Sedimen halus jenuh air"),
    "Alluvium (jenuh)":           (10,     200,    "Endapan aluvial jenuh air"),
    "Lanau / Silt":               (10,     200,    "Sedimen halus berukuran lanau"),
    "Pasir / Sand (jenuh)":       (1,      100,    "Pasir jenuh air"),
    "Pasir / Sand (kering)":      (100,    10000,  "Pasir kering atau tidak jenuh"),
    "Kerikil / Gravel":           (100,    600,    "Material kasar alluvial"),
    "Batupasir / Sandstone":      (1,      6400,   "Batuan sedimen klastik kasar"),
    "Batulempung / Claystone":    (1,      100,    "Batuan sedimen klastik halus"),
    "Batusabak / Shale":          (20,     2000,   "Batuan metamorf daun/foliasi"),
    "Batugamping / Limestone":    (50,     107,    "Batuan karbonat"),
    "Dolomit / Dolomite":         (100,    10000,  "Batuan karbonat magnesium"),
    "Batubara / Coal":            (10,     500,    "Batuan organik terpadatkan"),
    "Granit / Granite":           (100,    106,    "Batuan beku asam"),
    "Basalt / Basalt":            (10,     107,    "Batuan beku basa"),
    "Andesit / Andesite":         (100,    105,    "Batuan beku menengah"),
    "Riolit / Rhyolite":          (200,    106,    "Batuan beku vulkanik asam"),
    "Tuf / Tuff":                 (10,     5000,   "Material piroklastik terpadatkan"),
    "Breksi Vulkanik":            (100,    104,    "Material piroklastik kasar"),
    "Marmer / Marble":            (100,    108,    "Batuan metamorf karbonat"),
    "Kuarsit / Quartzite":        (10,     108,    "Batuan metamorf silika"),
    "Serpentin / Serpentinite":   (1000,   105,    "Batuan ultrabasa termeta"),
    "Laterit / Laterite":         (10,     2000,   "Tanah residual tropika"),
    "Tanah Lempungan / Clay Soil":(10,     200,    "Tanah bertekstur lempung"),
    "Batuan Pelapukan / Saprolite":(100,   1000,   "Batuan lapuk in-situ"),
}

# ============================================================
# KONTEKS GEOLOGI REGIONAL → LITOLOGI YANG MUNGKIN ADA
# ============================================================
REGIONAL_GEOLOGY_CONTEXT = {
    "Aluvium / Alluvium": {
        "deskripsi": "Endapan sungai dan dataran banjir: lempung, lanau, pasir, kerikil, gambut.",
        "litologi_umum": [
            "Gambut / Peat",
            "Lempung / Clay",
            "Lanau / Silt",
            "Lumpur / Mud",
            "Pasir / Sand (jenuh)",
            "Kerikil / Gravel",
            "Alluvium (jenuh)",
            "Air (fresh water)",
        ]
    },
    "Delta / Deltaic": {
        "deskripsi": "Endapan delta sungai: lempung lunak, lanau, pasir halus, gambut pesisir.",
        "litologi_umum": [
            "Gambut / Peat",
            "Lempung / Clay",
            "Lumpur / Mud",
            "Lanau / Silt",
            "Pasir / Sand (jenuh)",
            "Air (fresh water)",
            "Air (salt water)",
        ]
    },
    "Pantai / Coastal": {
        "deskripsi": "Endapan pantai: pasir pantai, kerikil, lempung marin, air asin.",
        "litologi_umum": [
            "Pasir / Sand (jenuh)",
            "Pasir / Sand (kering)",
            "Kerikil / Gravel",
            "Lempung / Clay",
            "Lumpur / Mud",
            "Air (salt water)",
            "Air (fresh water)",
        ]
    },
    "Karst / Limestone": {
        "deskripsi": "Formasi karbonat: batugamping, dolomit, lempung residual, rongga karst terisi air.",
        "litologi_umum": [
            "Batugamping / Limestone",
            "Dolomit / Dolomite",
            "Lempung / Clay",
            "Air (fresh water)",
            "Tanah Lempungan / Clay Soil",
        ]
    },
    "Vulkanik / Volcanic": {
        "deskripsi": "Kompleks vulkanik: basalt, andesit, tuf, breksi vulkanik, riolit.",
        "litologi_umum": [
            "Basalt / Basalt",
            "Andesit / Andesite",
            "Riolit / Rhyolite",
            "Tuf / Tuff",
            "Breksi Vulkanik",
            "Lempung / Clay",
            "Batuan Pelapukan / Saprolite",
            "Laterit / Laterite",
        ]
    },
    "Sedimen Tersier / Tertiary Sediment": {
        "deskripsi": "Batuan sedimen Tersier: batupasir, batulempung, serpih, batubara, batugamping.",
        "litologi_umum": [
            "Batupasir / Sandstone",
            "Batulempung / Claystone",
            "Batusabak / Shale",
            "Batubara / Coal",
            "Batugamping / Limestone",
            "Lempung / Clay",
            "Pasir / Sand (jenuh)",
        ]
    },
    "Metamorf / Metamorphic": {
        "deskripsi": "Batuan metamorf: marmer, kuarsit, sekis, batusabak, granit.",
        "litologi_umum": [
            "Marmer / Marble",
            "Kuarsit / Quartzite",
            "Batusabak / Shale",
            "Granit / Granite",
            "Batuan Pelapukan / Saprolite",
            "Laterit / Laterite",
        ]
    },
    "Batuan Beku Intrusi / Intrusive Igneous": {
        "deskripsi": "Batuan beku dalam: granit, diorit, gabro beserta zona lapukannya.",
        "litologi_umum": [
            "Granit / Granite",
            "Batuan Pelapukan / Saprolite",
            "Laterit / Laterite",
            "Lempung / Clay",
            "Tanah Lempungan / Clay Soil",
        ]
    },
    "Rawa / Swamp": {
        "deskripsi": "Lingkungan rawa: gambut, lempung organik, lumpur, air tanah dangkal.",
        "litologi_umum": [
            "Gambut / Peat",
            "Lempung / Clay",
            "Lumpur / Mud",
            "Lanau / Silt",
            "Air (fresh water)",
            "Alluvium (jenuh)",
        ]
    },
    "Universal (Tanpa Filter)": {
        "deskripsi": "Gunakan seluruh database Telford tanpa filter geologi regional.",
        "litologi_umum": list(TELFORD_TABLE.keys())
    },
}

# ============================================================
# FUNGSI: KLASIFIKASI LITOLOGI BERDASARKAN RESISTIVITAS
# ============================================================
def classify_lithology(resistivity_value, candidate_lithologies):
    """
    Mengklasifikasikan jenis litologi berdasarkan nilai resistivitas
    dan daftar litologi kandidat dari konteks geologi regional.

    Mengembalikan nama litologi terbaik.
    """
    best_match = None
    best_score = np.inf

    for lith_name in candidate_lithologies:
        if lith_name not in TELFORD_TABLE:
            continue
        rmin, rmax, _ = TELFORD_TABLE[lith_name]
        if rmin <= resistivity_value <= rmax:
            # Seberapa "tengah" nilai ini dalam rentang?
            mid = (rmin + rmax) / 2.0
            score = abs(np.log10(resistivity_value + 1e-9) - np.log10(mid + 1e-9))
            if score < best_score:
                best_score = score
                best_match = lith_name
        else:
            # Hitung jarak logaritmik ke rentang terdekat
            dist = min(
                abs(np.log10(resistivity_value + 1e-9) - np.log10(rmin + 1e-9)),
                abs(np.log10(resistivity_value + 1e-9) - np.log10(rmax + 1e-9))
            ) + 999  # penalti jika di luar rentang
            if dist < best_score:
                best_score = dist
                best_match = lith_name

    return best_match if best_match else "Tidak Teridentifikasi"


def build_color_scale_and_legend(candidate_lithologies, resistivity_min, resistivity_max):
    """
    Membangun palet warna berdasarkan urutan resistivitas
    dari litologi kandidat pada geologi regional terpilih.
    """
    # Warna default per kelompok litologi
    COLOR_MAP = {
        "Air":         "#1e90ff",
        "Gambut":      "#8B4513",
        "Lempung":     "#DAA520",
        "Lumpur":      "#6B8E23",
        "Alluvium":    "#D2B48C",
        "Lanau":       "#BDB76B",
        "Pasir":       "#F5DEB3",
        "Kerikil":     "#A9A9A9",
        "Batupasir":   "#CD853F",
        "Batulempung": "#BC8F8F",
        "Batusabak":   "#708090",
        "Batugamping": "#F0E68C",
        "Dolomit":     "#EEE8AA",
        "Batubara":    "#2F2F2F",
        "Granit":      "#C0C0C0",
        "Basalt":      "#404040",
        "Andesit":     "#808080",
        "Riolit":      "#D3D3D3",
        "Tuf":         "#B8860B",
        "Breksi":      "#8B7355",
        "Marmer":      "#FFFAFA",
        "Kuarsit":     "#F8F8FF",
        "Serpentin":   "#2E8B57",
        "Laterit":     "#B22222",
        "Tanah":       "#A0522D",
        "Batuan Pelapukan": "#C4A882",
        "Tidak Teridentifikasi": "#E0E0E0",
    }

    def get_color(name):
        for key, color in COLOR_MAP.items():
            if key.lower() in name.lower():
                return color
        return "#999999"

    legend = []
    for lith in candidate_lithologies:
        if lith in TELFORD_TABLE:
            rmin, rmax, desc = TELFORD_TABLE[lith]
            legend.append({
                "litologi": lith,
                "rmin": rmin,
                "rmax": rmax,
                "deskripsi": desc,
                "warna": get_color(lith)
            })

    legend.sort(key=lambda x: x["rmin"])
    return legend


def get_lithology_color(resistivity_value, candidate_lithologies, legend):
    """Ambil warna untuk nilai resistivitas tertentu."""
    lith_name = classify_lithology(resistivity_value, candidate_lithologies)
    for item in legend:
        if item["litologi"] == lith_name:
            return item["warna"], lith_name
    return "#999999", lith_name


# ============================================================
# FUNGSI: MEMBACA DATA EXCEL
# ============================================================
def load_excel_data(uploaded_file):
    try:
        xl = pd.ExcelFile(uploaded_file)
        df_geo = pd.read_excel(xl, sheet_name="GEOMETRY")
        df_data = pd.read_excel(xl, sheet_name="DATA")
        df_geo.columns = [c.strip().upper() for c in df_geo.columns]
        df_data.columns = [c.strip().upper() for c in df_data.columns]
        return df_geo, df_data, None
    except Exception as e:
        return None, None, str(e)


# ============================================================
# FUNGSI: INTERPOLASI 3D
# ============================================================
def interpolate_3d(df_data, df_geo, nx=60, ny=60, nz=30):
    geo_map = dict(zip(df_geo["LINE"], df_geo["Y_POSITION"]))
    df_data = df_data.copy()
    df_data["Y"] = df_data["LINE"].map(geo_map)
    df_data = df_data.dropna(subset=["Y"])

    x = df_data["POSITION"].values.astype(float)
    y = df_data["Y"].values.astype(float)
    z = df_data["DEPTH"].values.astype(float)
    r = df_data["RESISTIVITY"].values.astype(float)

    # ── Jika hanya 1 lintasan (y unik = 1), duplikasi dengan offset kecil
    # ── agar Delaunay 3D tidak gagal karena titik coplanar
    n_lines = len(np.unique(y))
    if n_lines < 2:
        y_offset = max(np.ptp(x) * 0.01, 0.1)
        x = np.concatenate([x, x])
        y = np.concatenate([y, y + y_offset])
        z = np.concatenate([z, z])
        r = np.concatenate([r, r])

    # ── Tambahkan jitter sangat kecil untuk mencegah degenerasi Qhull
    rng = np.random.default_rng(42)
    eps_x = np.ptp(x) * 1e-6 if np.ptp(x) > 0 else 1e-6
    eps_y = np.ptp(y) * 1e-6 if np.ptp(y) > 0 else 1e-6
    eps_z = np.ptp(z) * 1e-6 if np.ptp(z) > 0 else 1e-6
    x = x + rng.uniform(-eps_x, eps_x, size=x.shape)
    y = y + rng.uniform(-eps_y, eps_y, size=y.shape)
    z = z + rng.uniform(-eps_z, eps_z, size=z.shape)

    xi = np.linspace(x.min(), x.max(), nx)
    yi = np.linspace(y.min(), y.max(), ny)
    zi = np.linspace(z.min(), z.max(), nz)

    XX, YY, ZZ = np.meshgrid(xi, yi, zi, indexing="ij")
    points = np.column_stack([x, y, z])

    # ── Coba linear, fallback ke nearest jika Qhull / triangulasi gagal
    try:
        RR = griddata(points, r, (XX, YY, ZZ), method="linear")
        mask = np.isnan(RR)
        if mask.any():
            RR_nn = griddata(points, r, (XX, YY, ZZ), method="nearest")
            RR[mask] = RR_nn[mask]
    except Exception:
        # Fallback total ke nearest – selalu berhasil
        RR = griddata(points, r, (XX, YY, ZZ), method="nearest")

    # Pastikan tidak ada NaN tersisa
    if np.isnan(RR).any():
        RR = np.where(np.isnan(RR), np.nanmedian(r), RR)

    return XX, YY, ZZ, RR, xi, yi, zi


# ============================================================
# FUNGSI: BUAT COLORSCALE PLOTLY DARI LEGEND
# ============================================================
def build_plotly_colorscale(legend, r_min, r_max):
    """Membuat colorscale Plotly berbasis log dari legend litologi."""
    if r_min <= 0:
        r_min = 0.1
    log_min = np.log10(r_min)
    log_max = np.log10(r_max)
    log_range = log_max - log_min
    if log_range == 0:
        log_range = 1

    colorscale = []
    for item in legend:
        rmin_l = max(item["rmin"], r_min)
        rmax_l = min(item["rmax"], r_max)
        pos_start = max(0.0, (np.log10(max(rmin_l, 1e-9)) - log_min) / log_range)
        pos_end   = min(1.0, (np.log10(max(rmax_l, 1e-9)) - log_min) / log_range)
        colorscale.append([pos_start, item["warna"]])
        colorscale.append([pos_end,   item["warna"]])

    colorscale.sort(key=lambda x: x[0])

    # Pastikan 0.0 dan 1.0 selalu ada
    if not colorscale or colorscale[0][0] > 0:
        colorscale.insert(0, [0.0, legend[0]["warna"] if legend else "#1e90ff"])
    if colorscale[-1][0] < 1:
        colorscale.append([1.0, legend[-1]["warna"] if legend else "#C0C0C0"])

    return colorscale


# ============================================================
# MAIN APP
# ============================================================
def main():
    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Earthlayers.png/240px-Earthlayers.png",
                 use_column_width=True)
        st.title("⚙️ Pengaturan")

        st.markdown("---")
        st.subheader("📁 Upload Data")
        uploaded_file = st.file_uploader(
            "File Excel (.xlsx)",
            type=["xlsx"],
            help="Sheet: GEOMETRY dan DATA"
        )

        st.markdown("---")
        st.subheader("🗺️ Geologi Regional")

        regional_choice = st.selectbox(
            "Pilih Konteks Geologi Regional",
            list(REGIONAL_GEOLOGY_CONTEXT.keys()),
            help="Pilih geologi regional lokasi survei agar interpretasi litologi sesuai kondisi lapangan."
        )

        geo_info = REGIONAL_GEOLOGY_CONTEXT[regional_choice]
        st.info(f"ℹ️ {geo_info['deskripsi']}")

        # Tampilkan litologi kandidat, user bisa centang/hapus
        st.markdown("**Litologi kandidat (edit sesuai kebutuhan):**")
        candidate_defaults = geo_info["litologi_umum"]
        selected_candidates = st.multiselect(
            "Litologi yang mungkin hadir",
            options=list(TELFORD_TABLE.keys()),
            default=candidate_defaults,
            help="Anda bisa menambah atau menghapus litologi dari daftar Telford sesuai kondisi lokal."
        )

        if not selected_candidates:
            st.warning("⚠️ Pilih minimal 1 litologi!")
            selected_candidates = candidate_defaults

        st.markdown("---")
        st.subheader("🎨 Visualisasi")
        opacity_vol = st.slider("Opasitas Volume 3D", 0.1, 1.0, 0.6, 0.05)
        show_surface = st.checkbox("Tampilkan Permukaan Batas Lapisan", value=True)
        interp_method = st.selectbox("Metode Interpolasi", ["linear", "nearest", "cubic"], index=0)

        st.markdown("---")
        st.subheader("📐 Irisan Horizontal")
        depth_slice = st.slider(
            "Kedalaman Irisan (m, negatif = ke bawah)",
            -20.0, 0.0, -1.0, 0.5
        )

        st.markdown("---")
        st.subheader("📚 Referensi")
        st.caption("Tabel resistivitas: Telford et al. (1990), *Applied Geophysics*, 2nd ed., Cambridge University Press.")

    # ---------- HEADER UTAMA ----------
    st.title("🌍 Model 3D Resistivitas Geolistrik")
    st.markdown(
        "Aplikasi universal untuk visualisasi dan interpretasi litologi bawah permukaan "
        "berdasarkan data geolistrik resistivitas 2D multi-lintasan."
    )

    # ---------- PANEL INFO GEOLOGI ----------
    with st.expander("🗺️ Informasi Geologi Regional & Tabel Telford", expanded=False):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader(f"Konteks: {regional_choice}")
            st.write(geo_info["deskripsi"])
            st.markdown("**Litologi kandidat terpilih:**")
            for lith in selected_candidates:
                rmin, rmax, desc = TELFORD_TABLE.get(lith, (0, 0, "-"))
                st.markdown(f"- **{lith}**: {rmin}–{rmax} Ω·m")

        with col2:
            st.subheader("📖 Tabel Resistivitas Telford (Lengkap)")
            telford_df = pd.DataFrame([
                {"Litologi": k, "ρ min (Ω·m)": v[0], "ρ maks (Ω·m)": v[1], "Deskripsi": v[2]}
                for k, v in TELFORD_TABLE.items()
            ])
            st.dataframe(telford_df, use_container_width=True, height=300)

    # ---------- CEK FILE ----------
    if uploaded_file is None:
        st.info("⬆️ Upload file Excel di sidebar untuk memulai. Format: sheet **GEOMETRY** dan **DATA**.")

        st.subheader("📋 Format Data yang Diperlukan")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Sheet: GEOMETRY**")
            sample_geo = pd.DataFrame({"LINE": ["L1","L2","L3"], "Y_Position": [0, 10, 20]})
            st.dataframe(sample_geo)
        with c2:
            st.markdown("**Sheet: DATA**")
            sample_data = pd.DataFrame({
                "Line": ["L1","L1","L2"],
                "Distance": [1.5, 2.5, 1.5],
                "Position": [0, 0, 0],
                "Depth": [-0.25, -0.75, -0.25],
                "Resistivity": [1.29, 4.5, 25.3]
            })
            st.dataframe(sample_data)
        return

    # ---------- BACA DATA ----------
    df_geo, df_data, error = load_excel_data(uploaded_file)
    if error:
        st.error(f"❌ Gagal membaca file: {error}")
        return

    st.success(f"✅ Data dimuat: **{len(df_data)}** titik dari **{df_data['LINE'].nunique()}** lintasan.")

    # ---------- STATISTIK ----------
    r_values = df_data["RESISTIVITY"].values
    r_min, r_max, r_mean, r_median = r_values.min(), r_values.max(), r_values.mean(), np.median(r_values)

    col_s = st.columns(4)
    col_s[0].metric("ρ Min", f"{r_min:.2f} Ω·m")
    col_s[1].metric("ρ Maks", f"{r_max:.2f} Ω·m")
    col_s[2].metric("ρ Rata-rata", f"{r_mean:.2f} Ω·m")
    col_s[3].metric("ρ Median", f"{r_median:.2f} Ω·m")

    # ---------- BANGUN LEGEND ----------
    legend = build_color_scale_and_legend(selected_candidates, r_min, r_max)
    plotly_cs = build_plotly_colorscale(legend, r_min, r_max)

    # ---------- INTERPOLASI ----------
    with st.spinner("🔄 Menginterpolasi data 3D..."):
        XX, YY, ZZ, RR, xi, yi, zi = interpolate_3d(df_data, df_geo)

    # ===========================
    # TAB VISUALISASI
    # ===========================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧊 Volume 3D",
        "🏗️ Fence Diagram",
        "📐 Irisan Horizontal",
        "📏 Irisan Vertikal",
        "📊 Interpretasi Litologi"
    ])

    # -------- TAB 1: VOLUME 3D --------
    with tab1:
        st.subheader("Model Volume Resistivitas 3D")

        log_RR = np.log10(np.maximum(RR, 0.01))

        fig_vol = go.Figure(data=go.Volume(
            x=XX.flatten(), y=YY.flatten(), z=ZZ.flatten(),
            value=log_RR.flatten(),
            isomin=np.log10(max(r_min, 0.01)),
            isomax=np.log10(r_max),
            opacity=opacity_vol,
            surface_count=15,
            colorscale=plotly_cs,
            colorbar=dict(
                title="log₁₀(ρ) Ω·m",
                thickness=15,
                tickvals=[np.log10(max(r_min,0.01)),
                          np.log10(max(r_min,0.01)) + (np.log10(r_max)-np.log10(max(r_min,0.01)))/2,
                          np.log10(r_max)],
                ticktext=[f"{r_min:.1f}", f"{np.sqrt(r_min*r_max):.1f}", f"{r_max:.1f}"]
            ),
        ))

        fig_vol.update_layout(
            scene=dict(
                xaxis_title="Posisi (m)",
                yaxis_title="Lintasan (m)",
                zaxis_title="Kedalaman (m)",
                bgcolor="rgba(0,0,0,0)"
            ),
            title=f"Model 3D – {regional_choice}",
            height=600,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # -------- TAB 2: FENCE DIAGRAM --------
    with tab2:
        st.subheader("Fence Diagram (Penampang Antar-Lintasan)")

        fig_fence = go.Figure()
        colors_fence = ["#e6194b","#3cb44b","#4363d8","#f58231","#911eb4","#42d4f4"]

        lines = df_data["LINE"].unique()
        geo_map = dict(zip(df_geo["LINE"], df_geo["Y_POSITION"]))

        for i, line in enumerate(lines):
            df_line = df_data[df_data["LINE"] == line]
            y_pos = geo_map.get(line, i * 10)

            x_l = df_line["POSITION"].values
            z_l = df_line["DEPTH"].values
            r_l = df_line["RESISTIVITY"].values

            fig_fence.add_trace(go.Scatter3d(
                x=x_l, y=[y_pos]*len(x_l), z=z_l,
                mode="markers",
                marker=dict(
                    size=4,
                    color=np.log10(np.maximum(r_l, 0.01)),
                    colorscale=plotly_cs,
                    cmin=np.log10(max(r_min, 0.01)),
                    cmax=np.log10(r_max),
                    showscale=(i == 0)
                ),
                name=str(line),
                hovertemplate=(
                    f"Lintasan: {line}<br>"
                    "Posisi: %{x:.1f} m<br>"
                    "Kedalaman: %{z:.2f} m<br>"
                    "Resistivitas: %{marker.color:.2f} log Ω·m<extra></extra>"
                )
            ))

        fig_fence.update_layout(
            scene=dict(
                xaxis_title="Posisi (m)",
                yaxis_title="Y (m)",
                zaxis_title="Kedalaman (m)"
            ),
            title="Fence Diagram Multi-Lintasan",
            height=600
        )
        st.plotly_chart(fig_fence, use_container_width=True)

    # -------- TAB 3: IRISAN HORIZONTAL --------
    with tab3:
        st.subheader(f"Irisan Horizontal pada Kedalaman {depth_slice:.1f} m")

        iz = np.argmin(np.abs(zi - depth_slice))
        slice_h = RR[:, :, iz]

        # Klasifikasi litologi per sel
        lith_grid = np.empty(slice_h.shape, dtype=object)
        for ii in range(slice_h.shape[0]):
            for jj in range(slice_h.shape[1]):
                lith_grid[ii, jj] = classify_lithology(slice_h[ii, jj], selected_candidates)

        fig_h = go.Figure(data=go.Heatmap(
            x=xi, y=yi,
            z=np.log10(np.maximum(slice_h, 0.01)).T,
            colorscale=plotly_cs,
            colorbar=dict(title="log₁₀(ρ) Ω·m"),
            hovertemplate="X: %{x:.1f} m<br>Y: %{y:.1f} m<br>log(ρ): %{z:.2f}<extra></extra>"
        ))

        fig_h.update_layout(
            title=f"Peta Resistivitas – Kedalaman {depth_slice:.1f} m",
            xaxis_title="Posisi (m)",
            yaxis_title="Y (m)",
            height=450
        )
        st.plotly_chart(fig_h, use_container_width=True)

        # Tabel distribusi litologi pada kedalaman ini
        lith_flat = lith_grid.flatten()
        unique, counts = np.unique(lith_flat, return_counts=True)
        df_lith_dist = pd.DataFrame({
            "Litologi": unique,
            "Jumlah Sel": counts,
            "Persentase (%)": (counts / counts.sum() * 100).round(1)
        }).sort_values("Jumlah Sel", ascending=False)

        st.markdown(f"**Distribusi Litologi pada Kedalaman {depth_slice:.1f} m:**")
        st.dataframe(df_lith_dist, use_container_width=True)

    # -------- TAB 4: IRISAN VERTIKAL --------
    with tab4:
        st.subheader("Irisan Vertikal per Lintasan")

        lines = df_data["LINE"].unique()
        geo_map = dict(zip(df_geo["LINE"], df_geo["Y_POSITION"]))
        line_choice = st.selectbox("Pilih Lintasan", lines)
        df_line = df_data[df_data["LINE"] == line_choice]

        x_l = df_line["POSITION"].values
        z_l = df_line["DEPTH"].values
        r_l = df_line["RESISTIVITY"].values

        fig_v = go.Figure(data=go.Scatter(
            x=x_l, y=z_l,
            mode="markers",
            marker=dict(
                size=8,
                color=np.log10(np.maximum(r_l, 0.01)),
                colorscale=plotly_cs,
                cmin=np.log10(max(r_min, 0.01)),
                cmax=np.log10(r_max),
                colorbar=dict(title="log₁₀(ρ) Ω·m"),
                showscale=True
            ),
            hovertemplate=(
                "Posisi: %{x:.2f} m<br>"
                "Kedalaman: %{y:.2f} m<br>"
                "<extra></extra>"
            )
        ))

        fig_v.update_layout(
            title=f"Penampang Vertikal – Lintasan {line_choice}",
            xaxis_title="Posisi (m)",
            yaxis_title="Kedalaman (m)",
            height=400
        )
        st.plotly_chart(fig_v, use_container_width=True)

        # Tabel interpretasi per titik ukur
        lithologies = [classify_lithology(r, selected_candidates) for r in r_l]
        df_interp = pd.DataFrame({
            "Posisi (m)": x_l.round(2),
            "Kedalaman (m)": z_l.round(3),
            "Resistivitas (Ω·m)": r_l.round(3),
            "Interpretasi Litologi": lithologies
        })
        st.markdown("**Tabel Interpretasi Titik Ukur:**")
        st.dataframe(df_interp, use_container_width=True)

    # -------- TAB 5: INTERPRETASI LITOLOGI --------
    with tab5:
        st.subheader("📊 Interpretasi Litologi Keseluruhan")
        st.markdown(
            f"Interpretasi menggunakan **tabel Telford et al. (1990)** "
            f"dengan konteks geologi regional **{regional_choice}**."
        )

        # Klasifikasi seluruh titik data
        all_liths = [classify_lithology(r, selected_candidates) for r in r_values]
        df_data_copy = df_data.copy()
        df_data_copy["Interpretasi"] = all_liths

        # Statistik per litologi
        lith_stats = df_data_copy.groupby("Interpretasi")["RESISTIVITY"].agg(
            Jumlah="count",
            Resistivitas_Min="min",
            Resistivitas_Maks="max",
            Resistivitas_Rerata="mean"
        ).reset_index()
        lith_stats["Persentase (%)"] = (lith_stats["Jumlah"] / len(df_data_copy) * 100).round(1)
        lith_stats = lith_stats.sort_values("Jumlah", ascending=False)

        # Tambahkan warna
        warna_map = {item["litologi"]: item["warna"] for item in legend}

        col_leg, col_chart = st.columns([1, 2])

        with col_leg:
            st.markdown("**Legenda Litologi (Telford):**")
            for item in legend:
                if any(l == item["litologi"] for l in all_liths):
                    color_box = f"<span style='background:{item['warna']};padding:2px 10px;border-radius:3px;'>&nbsp;</span>"
                    st.markdown(
                        f"{color_box} **{item['litologi']}**  \n"
                        f"&nbsp;&nbsp;&nbsp;ρ: {item['rmin']}–{item['rmax']} Ω·m  \n"
                        f"&nbsp;&nbsp;&nbsp;{item['deskripsi']}",
                        unsafe_allow_html=True
                    )
                    st.markdown("")

        with col_chart:
            fig_pie = go.Figure(data=go.Pie(
                labels=lith_stats["Interpretasi"],
                values=lith_stats["Jumlah"],
                hole=0.35,
                marker=dict(colors=[warna_map.get(l, "#999999") for l in lith_stats["Interpretasi"]])
            ))
            fig_pie.update_layout(
                title="Distribusi Litologi (% titik ukur)",
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("**Tabel Statistik per Litologi:**")
        st.dataframe(
            lith_stats.rename(columns={
                "Interpretasi": "Litologi",
                "Resistivitas_Min": "ρ Min (Ω·m)",
                "Resistivitas_Maks": "ρ Maks (Ω·m)",
                "Resistivitas_Rerata": "ρ Rerata (Ω·m)"
            }).round(2),
            use_container_width=True
        )

        # Download tabel interpretasi lengkap
        st.markdown("**Unduh Hasil Interpretasi Lengkap:**")
        csv_out = df_data_copy.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download CSV Interpretasi",
            data=csv_out,
            file_name="interpretasi_litologi.csv",
            mime="text/csv"
        )

    # ---------- FOOTER ----------
    st.markdown("---")
    st.caption(
        "📚 Referensi resistivitas: **Telford, W.M., Geldart, L.P. & Sheriff, R.E. (1990)**. "
        "*Applied Geophysics*, 2nd ed., Cambridge University Press.  \n"
        "Dikembangkan untuk interpretasi geolistrik resistivitas 2D/3D – universal untuk semua lingkungan geologi."
    )


if __name__ == "__main__":
    main()
