import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

# 1. TASARIM VE SAYFA AYARLARI
st.set_page_config(page_title="StuMech Pro v2.0", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0a192f;
        background-image: linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    .stMetric, .stSelectbox, .stSlider, .stNumberInput, [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border-radius: 12px; padding: 15px; border: 1px solid #1e293b;
    }
    h1, h2, h3, p, span, label { color: #e2e8f0 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white; border-radius: 6px; font-weight: bold; width: 100%; border: 1px solid #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚙️ StuMech Pro v2.0: Çoklu Kesit Analizörü")

# 2. GİRİŞ PARAMETRELERİ
st.sidebar.header("🏢 Sistem Geometrisi")
sistem_tipi = st.sidebar.selectbox("Kiris Tipi", ["Basit Mesnet (Kopru)", "Ankastre (Balkon)"])
L = st.sidebar.slider("Kiris Boyu (m)", 1.0, 15.0, 5.0)

st.sidebar.header("📐 Kesit Tasarımı")
kesit_tipi = st.sidebar.selectbox("Kesit Geometrisi", ["Dikdortgen", "Daire", "I-Profil (NPI)"])

if kesit_tipi == "Dikdortgen":
    b = st.sidebar.slider("Genislik b (mm)", 10, 300, 50) / 1000
    h = st.sidebar.slider("Yukseklik h (mm)", 10, 300, 100) / 1000
    I = (b * h**3) / 12
    W = (b * h**2) / 6
    alan_cizim = {"x": [-b/2, b/2, b/2, -b/2, -b/2], "y": [h/2, h/2, -h/2, -h/2, h/2]}
elif kesit_tipi == "Daire":
    d = st.sidebar.slider("Cap d (mm)", 10, 300, 100) / 1000
    h = d # Çizim ölçeği için
    I = (np.pi * d**4) / 64
    W = (np.pi * d**3) / 32
    theta = np.linspace(0, 2*np.pi, 100)
    alan_cizim = {"x": (d/2)*np.cos(theta), "y": (d/2)*np.sin(theta)}
else: # I-Profil basitleştirilmiş model
    B = st.sidebar.slider("Baslik Genisligi B (mm)", 50, 300, 100) / 1000
    H = st.sidebar.slider("Toplam Yukseklik H (mm)", 50, 500, 200) / 1000
    tw = 10 / 1000 # Gövde et kalınlığı (sabit varsayıldı)
    tf = 15 / 1000 # Başlık et kalınlığı (sabit varsayıldı)
    h = H
    # I-Profil Atalet Hesabı: (B*H^3/12) - (B-tw)*(H-2*tf)^3/12
    I = (B * H**3 / 12) - ((B - tw) * (H - 2 * tf)**3 / 12)
    W = I / (H / 2)
    alan_cizim = {"x": [-B/2, B/2, B/2, tw/2, tw/2, B/2, B/2, -B/2, -B/2, -tw/2, -tw/2, -B/2, -B/2],
                  "y": [H/2, H/2, H/2-tf, H/2-tf, -H/2+tf, -H/2+tf, -H/2, -H/2, -H/2+tf, -H/2+tf, H/2-tf, H/2-tf, H/2]}

st.sidebar.header("⚖️ Yukleme ve Malzeme")
P = st.sidebar.number_input("Tekil Yuk (P) [N]", value=2000.0)
a = st.sidebar.slider("Yuk Konumu (m)", 0.0, L, L/2)
q = st.sidebar.number_input("Yayili Yuk (q) [N/m]", value=0.0)

malzemeler = {"Celik (S235)": [235, 210000], "Aluminyum (6061)": [110, 70000]}
secilen = st.sidebar.selectbox("Malzeme", list(malzemeler.keys()))
akma, E_mpa = malzemeler[secilen]
EI = (E_mpa * 1e6) * I

# 3. HESAPLAMA MOTORU (Aynı mantık, yeni I ve W ile)
x = np.linspace(0, L, 500)
if "Kopru" in sistem_tipi:
    R1 = (P * (L - a) / L) + (q * L / 2)
    V = R1 - (q * x) - np.where(x > a, P, 0)
    M = (R1 * x) - (q * x**2 / 2) - np.where(x > a, P * (x - a), 0)
    # Sehim
    y_p = (P * (L-a) * x / (6 * L * EI)) * (L**2 - (L-a)**2 - x**2)
    y_p = np.where(x > a, y_p + (P * (x - a)**3 / (6 * EI)), y_p)
    y_q = (q * x / (24 * EI)) * (L**3 - 2 * L * x**2 + x**3)
    y_son = y_p + y_q
else:
    R_duvar = P + (q * L)
    M_duvar = (P * a) + (q * L**2 / 2)
    V = R_duvar - (q * x) - np.where(x > a, P, 0)
    M = -M_duvar + (R_duvar * x) - (q * x**2 / 2) - np.where(x > a, P * (x - a), 0)
    y_p = np.where(x <= a, (P * x**2 / (6 * EI)) * (3 * a - x), (P * a**2 / (6 * EI)) * (3 * x - a))
    y_q = (q * x**2 / (24 * EI)) * (6 * L**2 - 4 * L * x + x**2)
    y_son = y_p + y_q

M_max = np.max(np.abs(M))
gerilme_max = (M_max / W) / 1e6
emniyet = akma / gerilme_max
sehim_max_mm = np.max(np.abs(y_son)) * 1000

# 4. GÖRSELLEŞTİRME
fig = make_subplots(rows=4, cols=1, subplot_titles=("📐 KESIT VE SISTEM SEMASI", "KESME (V)", "MOMENT (M)", "SEHIM (mm)"), vertical_spacing=0.07)

# Kesit ve Kiriş Çizimi (Yandaki küçük kesit görüntüsü)
fig.add_trace(go.Scatter(x=alan_cizim["x"], y=alan_cizim["y"], fill="toself", fillcolor='rgba(56, 189, 248, 0.3)', line=dict(color='#38bdf8'), name='Kesit'), row=1, col=1)
fig.add_trace(go.Scatter(x=[0, L], y=[0, 0], mode='lines', line=dict(color='white', width=5)), row=1, col=1)

# Diyagramlar
fig.add_trace(go.Scatter(x=x, y=V, fill='tozeroy', line_color='#0ea5e9'), row=2, col=1)
fig.add_trace(go.Scatter(x=x, y=M, fill='tozeroy', line_color='#22c55e'), row=3, col=1)
fig.add_trace(go.Scatter(x=x, y=-y_son*1000, fill='tozeroy', line_color='#fbbf24'), row=4, col=1)

fig.update_layout(height=1100, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 5. SONUÇLAR
c1, c2, c3 = st.columns(3)
c1.metric("Max Gerilme", f"{gerilme_max:.2f} MPa")
c2.metric("Maks. Sehim", f"{sehim_max_mm:.2f} mm")
c3.metric("Emniyet", f"{emniyet:.2f}")

if emniyet < 1.5: st.error("⚠️ DIKKAT: Kesit yetersiz veya emniyet katsayisi dusuk!")
else: st.success("✅ Sistem guvenli limitler dahilinde.")
