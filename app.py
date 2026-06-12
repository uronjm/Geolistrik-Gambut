
"""
app_v3.py
Geological Interpretation System berbasis Geolistrik 3D
Versi kerangka terintegrasi dari app.py + konsep Geological AI Interpretation

CATATAN:
- Mempertahankan struktur data DATA dan GEOMETRY seperti aplikasi lama.
- Menambahkan Geological Knowledge Base.
- Menambahkan Geological Constraint Engine.
- Menambahkan Probabilistic Lithology Classification.
- Menambahkan Confidence Index.
- Menambahkan Geological Report.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata
import io

st.set_page_config(page_title="Geological Interpretation System 3D", layout="wide")

# =====================================================================
# GEOLOGY DATABASE
# =====================================================================

LITHOLOGY_DB = {
    "Clay": (1,100),
    "Silt": (10,200),
    "Sand": (60,1000),
    "Gravel": (100,5000),
    "Peat": (20,300),
    "Sandstone": (8,4000),
    "Shale": (1,500),
    "Coal": (100,10000),
    "Limestone": (50,100000),
    "Andesite": (170,45000),
    "Basalt": (100,10000),
    "Granite": (1000,1000000),
    "Quartzite": (500,800000)
}

GEOLOGY_RULES = {
    "Alluvium":["Clay","Silt","Sand","Gravel","Peat","Sandstone"],
    "Peat Swamp":["Peat","Clay","Silt","Sand"],
    "Sedimentary Basin":["Clay","Sandstone","Shale","Coal","Limestone"],
    "Coal Formation":["Coal","Clay","Sandstone","Shale"],
    "Karst Limestone":["Limestone","Clay"],
    "Volcanic Deposit":["Andesite","Basalt"],
    "Metamorphic Terrain":["Quartzite"],
    "Granitic Intrusion":["Granite"]
}

def classify_lithology(value, geology):
    candidates = GEOLOGY_RULES.get(geology, list(LITHOLOGY_DB.keys()))
    scores = []

    for lith in candidates:
        rmin, rmax = LITHOLOGY_DB[lith]

        if rmin <= value <= rmax:
            mid = (rmin+rmax)/2
            score = 1/(abs(value-mid)+1)
            scores.append((lith, score))

    if len(scores) == 0:
        return "Unknown", 0

    total = sum(s for _, s in scores)
    scores = [(l, round(s/total*100,1)) for l,s in scores]
    scores.sort(key=lambda x:x[1], reverse=True)

    return scores[0]

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name="DATA")
    geom = pd.read_excel(file, sheet_name="GEOMETRY")
    return df, geom

st.title("🌍 Geological Interpretation System 3D")

# SIDEBAR
uploaded = st.sidebar.file_uploader("Upload Excel", type=["xlsx"])

regional_geology = st.sidebar.selectbox(
    "Regional Geology",
    list(GEOLOGY_RULES.keys())
)

study_mode = st.sidebar.selectbox(
    "Study Mode",
    [
        "Universal Geological",
        "Peatland Investigation",
        "Hydrogeology",
        "Coal Exploration",
        "Engineering Geology"
    ]
)

if uploaded:

    df, geom = load_data(uploaded)

    lithologies = []
    confidences = []

    for r in df["Resistivity"]:
        lith, conf = classify_lithology(r, regional_geology)
        lithologies.append(lith)
        confidences.append(conf)

    df["Lithology"] = lithologies
    df["Confidence"] = confidences

    tabs = st.tabs([
        "Model Data",
        "Lithology",
        "Confidence",
        "Geological Report"
    ])

    with tabs[0]:
        st.subheader("Input Data")
        st.dataframe(df.head())

        st.metric("Total Data", len(df))
        st.metric("Min Resistivity", round(df["Resistivity"].min(),2))
        st.metric("Max Resistivity", round(df["Resistivity"].max(),2))

    with tabs[1]:
        st.subheader("Lithology Interpretation")

        lith_count = df["Lithology"].value_counts()
        st.bar_chart(lith_count)

        st.dataframe(
            df[["Resistivity","Lithology","Confidence"]]
        )

    with tabs[2]:
        st.subheader("Confidence Analysis")

        mean_conf = round(df["Confidence"].mean(),1)

        st.metric(
            "Average Confidence (%)",
            mean_conf
        )

        st.line_chart(df["Confidence"])

    with tabs[3]:
        st.subheader("Automatic Geological Report")

        dominant = df["Lithology"].value_counts().idxmax()
        conf = round(df["Confidence"].mean(),1)

        report = f"""
REGIONAL GEOLOGY:
{regional_geology}

STUDY MODE:
{study_mode}

DOMINANT LITHOLOGY:
{dominant}

AVERAGE CONFIDENCE:
{conf}%

INTERPRETATION:
Interpretasi dilakukan berdasarkan database resistivitas
dan geological constraint sesuai geologi regional.
"""

        st.text_area(
            "Generated Report",
            report,
            height=300
        )

else:
    st.info("Upload file Excel geolistrik untuk memulai.")
