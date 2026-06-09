# 🌍 Model 3D Resistivitas Geolistrik

Aplikasi web interaktif untuk memvisualisasikan data geolistrik 2D menjadi model 3D resistivitas, khusus untuk pemetaan sebaran gambut.

## ✨ Fitur

| Fitur | Keterangan |
|-------|-----------|
| 🧊 **Model 3D Volume** | Visualisasi volume resistivitas 3D interaktif |
| 🏗️ **Fence Diagram** | Penampang vertikal 3 lintasan dalam ruang 3D |
| 📐 **Irisan Horizontal** | Peta resistivitas pada kedalaman tertentu |
| 📏 **Irisan Vertikal** | Penampang memanjang per lintasan |
| 📊 **Data & Interpretasi** | Statistik dan legenda litologi |

## 🚀 Cara Menjalankan

### Online (Streamlit Cloud)
Kunjungi: **[link-streamlit-anda]** *(setelah deploy)*

### Lokal
```bash
# 1. Clone repository
git clone https://github.com/username/geolistrik-3d.git
cd geolistrik-3d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan aplikasi
streamlit run app.py
```

## 📂 Format Data Excel

File Excel harus memiliki **2 sheet**:

### Sheet: `GEOMETRY`
| Line | Y_Position |
|------|-----------|
| L1   | 0         |
| L2   | 10        |
| L3   | 20        |

### Sheet: `DATA`
| Line | Distance | Position | Depth  | Resistivity |
|------|----------|----------|--------|-------------|
| L1   | 1.5      | 0        | -0.25  | 1.29        |
| L1   | 2.5      | 0        | -0.25  | 1.44        |
| ...  | ...      | ...      | ...    | ...         |

## 🗺️ Interpretasi Litologi

| Rentang Resistivitas | Interpretasi |
|---------------------|--------------|
| < 1 Ω·m | Lempung sangat jenuh/air |
| 1 – 5 Ω·m | Gambut jenuh |
| 5 – 20 Ω·m | Gambut kurang jenuh |
| 20 – 100 Ω·m | Lempung |
| > 100 Ω·m | Pasir/kerikil |

## 🛠️ Deploy ke Streamlit Cloud (Gratis)

1. **Fork** atau **push** repository ini ke GitHub Anda
2. Buka [share.streamlit.io](https://share.streamlit.io)
3. Klik **"New app"** → pilih repository ini
4. Set **Main file path**: `app.py`
5. Klik **Deploy** → aplikasi online dalam ~2 menit!

## 📦 Dependencies

- `streamlit` — framework web app
- `plotly` — visualisasi 3D interaktif
- `scipy` — interpolasi 3D (griddata)
- `pandas` — manajemen data
- `numpy` — komputasi numerik
- `openpyxl` — baca file Excel

## 👤 Tentang

Dibuat untuk penelitian sebaran gambut menggunakan metode geolistrik resistivitas 2D yang dikonversi menjadi model 3D melalui interpolasi spasial.

---
*Aplikasi ini menggunakan interpolasi `griddata` dari SciPy untuk membangun model 3D dari data 2D multi-lintasan.*
