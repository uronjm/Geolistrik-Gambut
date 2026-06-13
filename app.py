import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import griddata
import io

st.set_page_config(
    page_title="Model 3D Resistivitas Geolistrik",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Model 3D Resistivitas Geolistrik")
st.markdown("**Visualisasi 3D Sebaran Gambut — Skala Warna Identik dengan Res2DInv**")

# ─────────────────────────────────────────────────────────────────────────────
# COLORSCALE IDENTIK DENGAN RES2DINV
# Tick legend 2D: 1, 7, 13, 19, 25, 31, 37, 43 Ω·m
# Range data   : 0.49 – 60.94 Ω·m
# Warna urutan : biru tua → biru → biru muda → cyan → hijau tua → hijau muda
#                → kuning-hijau → kuning → oranye → merah → merah tua → ungu
# ─────────────────────────────────────────────────────────────────────────────
R_MIN_DATA = 0.49
R_MAX_DATA = 60.94

def norm(r):
    """Normalisasi nilai resistivitas ke 0-1 untuk colorscale."""
    return (r - R_MIN_DATA) / (R_MAX_DATA - R_MIN_DATA)

# Colorscale disesuaikan dengan posisi tick Res2DInv
COLORSCALE_RES2DINV = [
    [0.000,               '#00004B'],  # < 0.49 Ω·m — biru sangat tua
    [norm(1.0),           '#0000FF'],  # 1 Ω·m — biru
    [norm(7.0),           '#0080FF'],  # 7 Ω·m — biru muda
    [norm(13.0),          '#00FFFF'],  # 13 Ω·m — cyan
    [norm(19.0),          '#00C800'],  # 19 Ω·m — hijau tua
    [norm(25.0),          '#80FF00'],  # 25 Ω·m — hijau muda
    [norm(31.0),          '#FFFF00'],  # 31 Ω·m — kuning
    [norm(37.0),          '#FFA000'],  # 37 Ω·m — oranye
    [norm(43.0),          '#FF0000'],  # 43 Ω·m — merah
    [norm(52.0),          '#800000'],  # ~52 Ω·m — merah tua
    [1.000,               '#500050'],  # 60.94 Ω·m — ungu tua
]

# Tick untuk colorbar (nilai asli Ω·m)
CBAR_TICKVALS = [norm(v) for v in [1, 7, 13, 19, 25, 31, 37, 43]]
CBAR_TICKTEXT = ['1.0', '7.0', '13.0', '19.0', '25.0', '31.0', '37.0', '43.0']

CBAR_CFG = dict(
    title=dict(text="Resistivity (Ω·m)", side='right', font=dict(size=13)),
    thickness=20, len=0.75,
    tickvals=CBAR_TICKVALS,
    ticktext=CBAR_TICKTEXT,
    tickfont=dict(size=11),
    outlinewidth=1,
)

# ─── Load & Grid Builder ──────────────────────────────────────────────────────
@st.cache_data
def load_and_build(file_bytes, nx, ny, nz):
    df   = pd.read_excel(io.BytesIO(file_bytes), sheet_name='DATA')
    geom = pd.read_excel(io.BytesIO(file_bytes), sheet_name='GEOMETRY')
    line_y = dict(zip(geom['Line'], geom['Y_Position']))
    df['Y'] = df['Line'].map(line_y)

    xi = np.linspace(df['Distance'].min(), df['Distance'].max(), nx)
    yi = np.linspace(df['Y'].min(),        df['Y'].max(),        ny)
    zi = np.linspace(df['Depth'].min(),    df['Depth'].max(),    nz)

    pts  = df[['Distance','Y','Depth']].values
    vals = df['Resistivity'].values

    XX, YY, ZZ = np.meshgrid(xi, yi, zi, indexing='ij')
    flat = np.column_stack([XX.flatten(), YY.flatten(), ZZ.flatten()])

    r_lin  = griddata(pts, vals, flat, method='linear')
    r_near = griddata(pts, vals, flat, method='nearest')
    grid   = np.where(np.isnan(r_lin), r_near, r_lin).reshape(nx, ny, nz)

    # Normalisasi ke [0,1] sesuai colorscale
    grid_norm = np.clip((grid - R_MIN_DATA) / (R_MAX_DATA - R_MIN_DATA), 0, 1)

    return xi, yi, zi, grid, grid_norm, df, geom, line_y

# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.header("📂 Upload Data")
uploaded = st.sidebar.file_uploader("Upload file Excel (.xlsx)", type=['xlsx'])

if uploaded:
    file_bytes = uploaded.read()
else:
    try:
        with open('Geolistrik_3D.xlsx', 'rb') as f:
            file_bytes = f.read()
        st.sidebar.success("✅ Data bawaan: Geolistrik_3D.xlsx")
    except:
        st.warning("⚠️ Silakan upload file Excel data geolistrik Anda.")
        st.stop()

st.sidebar.header("⚙️ Resolusi Grid")
nx = st.sidebar.slider("Grid X", 30, 120, 60, 10)
ny = st.sidebar.slider("Grid Y", 10, 50,  30,  5)
nz = st.sidebar.slider("Grid Z", 10, 40,  20,  5)

xi, yi, zi, grid, grid_norm, df, geom, line_y = load_and_build(file_bytes, nx, ny, nz)

# Konversi zi ke kedalaman positif (untuk label)
zi_depth = np.abs(zi)  # misal: -0.25 → 0.25 m

# ─── Helper: buat surface ─────────────────────────────────────────────────────
def make_surf(x2d, y2d, z2d, color_norm, name, show_cb=False):
    return go.Surface(
        x=x2d, y=y2d, z=z2d,
        surfacecolor=color_norm,
        colorscale=COLORSCALE_RES2DINV,
        cmin=0, cmax=1,
        showscale=show_cb,
        colorbar=CBAR_CFG if show_cb else None,
        name=name,
        hovertemplate=(
            'X: %{x:.1f} m<br>'
            'Y: %{y:.1f} m<br>'
            'Z: %{z:.2f} m<extra>' + name + '</extra>'
        ),
    )

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧊 Model 3D Box",
    "🏗️ Fence Diagram",
    "📐 Irisan Horizontal",
    "📏 Irisan Vertikal",
    "📊 Data & Interpretasi",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — MODEL 3D BOX
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Model 3D Resistivitas — Box View (Surfer Style)")

    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        show_front = st.checkbox("✅ Sisi Depan (Y min)", value=True)
        show_top   = st.checkbox("✅ Sisi Atas (permukaan)", value=True)
    with col_opt2:
        show_left  = st.checkbox("✅ Sisi Kiri (X min)", value=True)
        show_back  = st.checkbox("Sisi Belakang (Y max)", value=False)
    with col_opt3:
        show_right = st.checkbox("Sisi Kanan (X max)", value=False)
        show_bot   = st.checkbox("Sisi Bawah (terdalam)", value=False)

    fig = go.Figure()
    cb_done = False

    # Sisi Depan — Y=min
    if show_front:
        XF, ZF = np.meshgrid(xi, zi, indexing='ij')
        YF = np.full_like(XF, yi[0])
        fig.add_trace(make_surf(XF, YF, ZF, grid_norm[:,0,:], 'Depan', not cb_done))
        cb_done = True

    # Sisi Belakang — Y=max
    if show_back:
        XB, ZB = np.meshgrid(xi, zi, indexing='ij')
        YB = np.full_like(XB, yi[-1])
        fig.add_trace(make_surf(XB, YB, ZB, grid_norm[:,-1,:], 'Belakang', not cb_done))
        cb_done = True

    # Sisi Atas — Z=max (permukaan tanah)
    if show_top:
        XT, YT = np.meshgrid(xi, yi, indexing='ij')
        ZT = np.full_like(XT, zi[-1])
        fig.add_trace(make_surf(XT, YT, ZT, grid_norm[:,:,-1], 'Atas', not cb_done))
        cb_done = True

    # Sisi Bawah — Z=min
    if show_bot:
        XBo, YBo = np.meshgrid(xi, yi, indexing='ij')
        ZBo = np.full_like(XBo, zi[0])
        fig.add_trace(make_surf(XBo, YBo, ZBo, grid_norm[:,:,0], 'Bawah', not cb_done))
        cb_done = True

    # Sisi Kiri — X=min
    if show_left:
        YL, ZL = np.meshgrid(yi, zi, indexing='ij')
        XL = np.full_like(YL, xi[0])
        fig.add_trace(make_surf(XL, YL, ZL, grid_norm[0,:,:], 'Kiri', not cb_done))
        cb_done = True

    # Sisi Kanan — X=max
    if show_right:
        YR, ZR = np.meshgrid(yi, zi, indexing='ij')
        XR = np.full_like(YR, xi[-1])
        fig.add_trace(make_surf(XR, YR, ZR, grid_norm[-1,:,:], 'Kanan', not cb_done))
        cb_done = True

    # Label & garis lintasan
    for _, row in geom.iterrows():
        y_pos = float(row['Y_Position'])
        fig.add_trace(go.Scatter3d(
            x=[(xi[0]+xi[-1])/2],
            y=[y_pos],
            z=[zi[-1] + abs(zi[-1]-zi[0])*0.18],
            mode='text+markers',
            text=[f"<b>{row['Line']}<br>Y={int(y_pos)} m</b>"],
            textfont=dict(size=11, color='black'),
            marker=dict(size=3, color='black'),
            showlegend=False,
        ))
        fig.add_trace(go.Scatter3d(
            x=[xi[0], xi[-1]], y=[y_pos, y_pos], z=[zi[-1], zi[-1]],
            mode='lines',
            line=dict(color='black', width=2, dash='dash'),
            showlegend=False,
        ))

    fig.update_layout(
        scene=dict(
            xaxis=dict(title='X (m)', backgroundcolor='rgb(245,245,245)', showbackground=True),
            yaxis=dict(title='Y (m)', backgroundcolor='rgb(235,235,245)', showbackground=True),
            zaxis=dict(title='Kedalaman (m)', backgroundcolor='rgb(235,245,245)', showbackground=True),
            camera=dict(eye=dict(x=1.6, y=-1.8, z=1.1)),
            aspectmode='manual',
            aspectratio=dict(x=2.2, y=0.6, z=0.5),
        ),
        height=640,
        title=dict(text="MODEL 3D RESISTIVITAS", x=0.5, font=dict(size=16, color='black')),
        margin=dict(l=0, r=20, t=50, b=0),
        paper_bgcolor='white',
    )
    st.plotly_chart(fig, use_container_width=True)

    # Informasi skala
    st.info(
        "📌 **Skala warna identik dengan Res2DInv:** "
        "🔵 Biru tua < 1 Ω·m → 🔵 Biru 7 → 🩵 Cyan 13 → 🟢 Hijau 19–25 → "
        "🟡 Kuning 31 → 🟠 Oranye 37 → 🔴 Merah 43+ Ω·m"
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FENCE DIAGRAM
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Fence Diagram — Penampang Vertikal 3 Lintasan")

    fig_f = go.Figure()
    cb_f  = False

    for _, row in geom.iterrows():
        y_pos = float(row['Y_Position'])
        iy    = np.argmin(np.abs(yi - y_pos))
        face  = grid_norm[:, iy, :]   # NX x NZ

        XF2, ZF2 = np.meshgrid(xi, zi, indexing='ij')
        YF2 = np.full_like(XF2, y_pos)

        fig_f.add_trace(make_surf(XF2, YF2, ZF2, face, f"{row['Line']} Y={int(y_pos)}m", not cb_f))
        cb_f = True

        fig_f.add_trace(go.Scatter3d(
            x=[(xi[0]+xi[-1])/2], y=[y_pos],
            z=[zi[-1] + abs(zi[-1]-zi[0])*0.2],
            mode='text',
            text=[f"<b>{row['Line']}<br>Y={int(y_pos)} m</b>"],
            textfont=dict(size=11, color='black'),
            showlegend=False,
        ))

    fig_f.update_layout(
        scene=dict(
            xaxis=dict(title='X (m)'),
            yaxis=dict(title='Y (m)'),
            zaxis=dict(title='Kedalaman (m)'),
            camera=dict(eye=dict(x=1.8, y=-1.6, z=1.0)),
            aspectmode='manual',
            aspectratio=dict(x=2.2, y=0.6, z=0.5),
        ),
        height=600,
        title=dict(text="FENCE DIAGRAM (PENAMPANG 3D)", x=0.5, font=dict(size=16)),
        margin=dict(l=0, r=20, t=50, b=0),
        paper_bgcolor='white',
    )
    st.plotly_chart(fig_f, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — IRISAN HORIZONTAL
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Irisan Horizontal (pada Kedalaman Tertentu)")

    depth_labels = [f"{abs(z):.2f} m" for z in zi]
    col1, col2, col3 = st.columns(3)
    with col1:
        d1 = st.selectbox("Kedalaman 1", range(len(zi)), format_func=lambda i: depth_labels[i], index=0)
    with col2:
        d2 = st.selectbox("Kedalaman 2", range(len(zi)), format_func=lambda i: depth_labels[i], index=len(zi)//2)
    with col3:
        d3 = st.selectbox("Kedalaman 3", range(len(zi)), format_func=lambda i: depth_labels[i], index=len(zi)-1)

    titles_h = [f"Kedalaman {depth_labels[i]}" for i in [d1,d2,d3]]
    fig_h = make_subplots(rows=1, cols=3, subplot_titles=titles_h, horizontal_spacing=0.08)

    # Buat colorscale untuk contour (pakai nilai asli Ω·m)
    for col_i, iz_idx in enumerate([d1, d2, d3], 1):
        slice_r = grid[:, :, iz_idx]   # NX x NY, nilai resistivitas asli

        fig_h.add_trace(go.Contour(
            x=xi, y=yi, z=slice_r.T,
            colorscale=[[norm(v), c] for v, c in [
                (0.49,'#00004B'),(1,'#0000FF'),(7,'#0080FF'),
                (13,'#00FFFF'),(19,'#00C800'),(25,'#80FF00'),
                (31,'#FFFF00'),(37,'#FFA000'),(43,'#FF0000'),
                (52,'#800000'),(60.94,'#500050')
            ]],
            zmin=R_MIN_DATA, zmax=R_MAX_DATA,
            showscale=(col_i == 3),
            colorbar=dict(
                title="Resistivity (Ω·m)",
                tickvals=[1,7,13,19,25,31,37,43],
                ticktext=['1','7','13','19','25','31','37','43'],
                thickness=15,
            ) if col_i == 3 else None,
            contours=dict(
                coloring='heatmap',
                showlabels=True,
                labelfont=dict(size=8, color='white'),
                start=1, end=43, size=6,
            ),
            hovertemplate='X:%{x:.1f} m<br>Y:%{y:.1f} m<br>R:%{z:.2f} Ω·m<extra></extra>',
        ), row=1, col=col_i)

        # Garis lintasan
        for _, grow in geom.iterrows():
            fig_h.add_trace(go.Scatter(
                x=[xi[0], xi[-1]],
                y=[grow['Y_Position'], grow['Y_Position']],
                mode='lines+text',
                line=dict(color='white', width=1.5, dash='dot'),
                text=[grow['Line'], ''],
                textposition='top left',
                textfont=dict(size=9, color='white'),
                showlegend=False,
            ), row=1, col=col_i)

    fig_h.update_xaxes(title_text="X (m)")
    fig_h.update_yaxes(title_text="Y (m)")
    fig_h.update_layout(
        height=400,
        title=dict(text="IRISAN HORIZONTAL (KEDALAMAN TERTENTU)", x=0.5, font=dict(size=15)),
        paper_bgcolor='white',
    )
    st.plotly_chart(fig_h, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — IRISAN VERTIKAL
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Irisan Vertikal — Penampang Memanjang per Lintasan")

    lines_all = geom['Line'].tolist()
    col_a, col_b = st.columns([1, 3])
    with col_a:
        mode_v = st.radio("Tampilkan", ["Semua Lintasan", "Pilih Lintasan"])
        sel_line = st.selectbox("Pilih", lines_all) if mode_v == "Pilih Lintasan" else None

    lines_show = lines_all if mode_v == "Semua Lintasan" else [sel_line]
    titles_v   = [f"{l} — Y={int(line_y[l])} m" for l in lines_show]

    fig_v = make_subplots(rows=1, cols=len(lines_show), subplot_titles=titles_v,
                          horizontal_spacing=0.06)

    contour_colorscale = [[norm(v), c] for v, c in [
        (0.49,'#00004B'),(1,'#0000FF'),(7,'#0080FF'),
        (13,'#00FFFF'),(19,'#00C800'),(25,'#80FF00'),
        (31,'#FFFF00'),(37,'#FFA000'),(43,'#FF0000'),
        (52,'#800000'),(60.94,'#500050')
    ]]

    for col_i, lname in enumerate(lines_show, 1):
        iy      = np.argmin(np.abs(yi - line_y[lname]))
        slice_v = grid[:, iy, :]   # NX x NZ, nilai asli

        fig_v.add_trace(go.Contour(
            x=xi, y=zi, z=slice_v.T,
            colorscale=contour_colorscale,
            zmin=R_MIN_DATA, zmax=R_MAX_DATA,
            showscale=(col_i == len(lines_show)),
            colorbar=dict(
                title="Resistivity (Ω·m)",
                tickvals=[1,7,13,19,25,31,37,43],
                ticktext=['1','7','13','19','25','31','37','43'],
                thickness=15,
            ) if col_i == len(lines_show) else None,
            contours=dict(
                coloring='heatmap',
                showlabels=True,
                labelfont=dict(size=9, color='white'),
                start=1, end=43, size=6,
            ),
            hovertemplate='X:%{x:.1f} m<br>Z:%{y:.2f} m<br>R:%{z:.2f} Ω·m<extra></extra>',
        ), row=1, col=col_i)

    fig_v.update_xaxes(title_text="X (m)")
    fig_v.update_yaxes(title_text="Kedalaman (m)")
    fig_v.update_layout(
        height=400,
        title=dict(text="IRISAN VERTIKAL (PENAMPANG MEMANJANG)", x=0.5, font=dict(size=15)),
        paper_bgcolor='white',
    )
    st.plotly_chart(fig_v, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DATA & INTERPRETASI
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Data & Interpretasi Litologi Gambut")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Data Poin", len(df))
    c2.metric("Rentang Resistivitas", f"{df['Resistivity'].min():.2f} – {df['Resistivity'].max():.2f} Ω·m")
    c3.metric("Rentang Kedalaman", f"{abs(df['Depth'].max()):.2f} – {abs(df['Depth'].min()):.2f} m")

    st.markdown("---")
    st.markdown("### 🗺️ Legenda Interpretasi Litologi (Sesuai Skala Res2DInv)")

    interp = [
        ('#00004B', '< 1 Ω·m',     'Lempung sangat jenuh / air'),
        ('#0000FF', '1 – 7 Ω·m',   'Gambut jenuh (zona utama)'),
        ('#00FFFF', '7 – 13 Ω·m',  'Gambut agak jenuh'),
        ('#00C800', '13 – 19 Ω·m', 'Gambut kurang jenuh'),
        ('#FFFF00', '25 – 31 Ω·m', 'Batas gambut/mineral'),
        ('#FF0000', '> 43 Ω·m',    'Lapisan mineral / lempung padat'),
    ]
    cols_leg = st.columns(len(interp))
    for ci, (color, rng, desc) in zip(cols_leg, interp):
        text_color = 'black' if color in ['#FFFF00', '#80FF00'] else 'white'
        ci.markdown(
            f'<div style="background:{color};padding:10px 6px;border-radius:8px;'
            f'text-align:center;margin-bottom:4px;">'
            f'<span style="color:{text_color};font-weight:bold;font-size:11px;">'
            f'{rng}<br><small>{desc}</small></span></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("### 📋 Statistik Per Lintasan")
    stats = df.groupby('Line')['Resistivity'].agg(['min','max','mean','median']).round(3)
    stats.columns = ['Min (Ω·m)', 'Max (Ω·m)', 'Mean (Ω·m)', 'Median (Ω·m)']
    st.dataframe(stats, use_container_width=True)

    st.markdown("### 📋 Statistik Per Kedalaman")
    stats_z = df.groupby('Depth')['Resistivity'].agg(['min','max','mean']).round(3)
    stats_z.index = [f"{abs(z):.2f} m" for z in stats_z.index]
    stats_z.columns = ['Min (Ω·m)', 'Max (Ω·m)', 'Mean (Ω·m)']
    st.dataframe(stats_z, use_container_width=True)

    st.markdown("---")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='DATA', index=False)
        geom.to_excel(writer, sheet_name='GEOMETRY', index=False)
        stats.to_excel(writer, sheet_name='STATISTIK_LINTASAN')
        stats_z.to_excel(writer, sheet_name='STATISTIK_KEDALAMAN')
    st.download_button(
        "⬇️ Download Data Lengkap (.xlsx)",
        data=buf.getvalue(),
        file_name="Geolistrik_3D_Hasil.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.markdown("---")
st.caption(
    "📌 Skala warna & tick identik dengan Res2DInv | "
    "Interpolasi: Scipy griddata (linear + nearest fill) | "
    "Nilai legend: Apparent Resistivity (Ω·m) asli"
)
