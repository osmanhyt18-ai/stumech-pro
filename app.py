import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fpdf import FPDF

# 1. SAYFA AYARLARI VE MEKANİK TASARIM
st.set_page_config(page_title="StuMech Pro", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #0a192f;
        background-image: linear-gradient(rgba(56, 189, 248, 0.05) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(56, 189, 248, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
    }
    .stMetric, .stSelectbox, .stSlider, .stNumberInput, [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border-radius: 10px; padding: 15px; border: 1px solid #1e293b;
    }
    h1, h2, h3, p, span, label { color: #e2e8f0 !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white; border-radius: 5px; font-weight: bold; width: 100%; border: 1px solid #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚙️ StuMech Pro: Teknik Çizim ve Analiz İstasyonu")
st.markdown("---")

# 2. GİRİŞ PARAMETRELERİ
st.sidebar.header("🏢 Sistem Geometrisi")
sistem_tipi = st.sidebar.selectbox("Kiris Tipi", ["Basit Mesnet (Kopru)", "Ankastre (Balkon)"])
L = st.sidebar.slider("Kiris Boyu (m)", 1.0, 15.0, 5.0)

st.sidebar.header("⚖️ Yukleme Durumu")
P = st.sidebar.number_input("Tekil Yuk (P) [N]", value=2000.0)
a = st.sidebar.slider("P Yukü Konumu (m)", 0.0, L, L/2)
q = st.sidebar.number_input("Yayili Yuk (q) [N/m]", value=0.0)

st.sidebar.header("🔬 Malzeme ve Kesit")
malzemeler = {"Celik (S235)": [235, 210000], "Aluminyum (6061)": [110, 70000]}
secilen_malzeme = st.sidebar.selectbox("Malzeme Secimi", list(malzemeler.keys())) # İsmi düzelttim
akma, E_mpa = malzemeler[secilen_malzeme]

b = st.sidebar.slider("Genislik b (mm)", 10, 300, 50) / 1000
h = st.sidebar.slider("Yukseklik h (mm)", 10, 300, 100) / 1000

# 3. HESAPLAMA MOTORU
x = np.linspace(0, L, 500)
I = (b * h**3) / 12  
E = E_mpa * 1e6      
EI = E * I

if "Kopru" in sistem_tipi:
    R1 = (P * (L - a) / L) + (q * L / 2)
    R2 = (P * a / L) + (q * L / 2)
    V = R1 - (q * x) - np.where(x > a, P, 0)
    M = (R1 * x) - (q * x**2 / 2) - np.where(x > a, P * (x - a), 0)
    ba = L - a
    y_p = (P * ba * x / (6 * L * EI)) * (L**2 - ba**2 - x**2)
    y_p = np.where(x > a, y_p + (P * (x - a)**3 / (6 * EI)), y_p)
    y_q = (q * x / (24 * EI)) * (L**3 - 2 * L * x**2 + x**3)
    y_son = y_p + y_q
else:
    R_duvar = P + (q * L)
    M_duvar = (P * a) + (q * L**2 / 2)
    V = R_duvar - (q * x) - np.where(x > a, P, 0)
    M = -(M_duvar) + (R_duvar * x) - (q * x**2 / 2) - np.where(x > a, P * (x - a), 0)
    y_p = np.where(x <= a, (P * x**2 / (6 * EI)) * (3 * a - x), (P * a**2 / (6 * EI)) * (3 * x - a))
    y_q = (q * x**2 / (24 * EI)) * (6 * L**2 - 4 * L * x + x**2)
    y_son = y_p + y_q

M_max = np.max(np.abs(M))
gerilme_max = ((M_max * (h/2)) / I) / 1e6
emniyet = akma / gerilme_max
sehim_max_mm = np.max(np.abs(y_son)) * 1000

# 4. TEKNIK CIZIM VE DIYAGRAMLAR
fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                    subplot_titles=("OLCEKLI TEKNIK CIZIM", "KESME KUVVETI (V)", "EGILME MOMENTI (M)", "SEHIM / COKME (mm)"))

fig.add_trace(go.Scatter(x=[0, L, L, 0, 0], y=[h/2, h/2, -h/2, -h/2, h/2], fill="toself", fillcolor='rgba(200,200,200,0.3)', line=dict(color='white', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=[0, L], y=[-h-0.2, -h-0.2], mode='lines+markers', line=dict(color='#fbbf24', width=1)), row=1, col=1)
fig.add_annotation(x=L/2, y=-h-0.4, text=f"L={L}m", showarrow=False, font=dict(color="#fbbf24"), row=1, col=1)

if "Kopru" in sistem_tipi:
    fig.add_trace(go.Scatter(x=[0, L], y=[-h/2-0.1], mode='markers', marker=dict(symbol='triangle-up', size=18, color='#38bdf8')), row=1, col=1)
else:
    fig.add_trace(go.Scatter(x=[0, 0], y=[-0.8, 0.8], mode='lines', line=dict(color='brown', width=8)), row=1, col=1)

if P > 0:
    fig.add_trace(go.Scatter(x=[a], y=[h/2+0.1], mode='markers', marker=dict(symbol='arrow-down', size=20, color='red')), row=1, col=1)

fig.add_trace(go.Scatter(x=x, y=V, fill='tozeroy', line_color='#38bdf8', name='Kesme'), row=2, col=1)
fig.add_trace(go.Scatter(x=x, y=M, fill='tozeroy', line_color='#4ade80', name='Moment'), row=3, col=1)
fig.add_trace(go.Scatter(x=x, y=-y_son*1000, fill='tozeroy', line_color='#fbbf24', name='Sehim'), row=4, col=1)

fig.update_layout(height=1100, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig, use_container_width=True)

# 5. METRIKLER VE RAPOR
c1, c2, c3 = st.columns(3)
c1.metric("Maks. Gerilme", f"{gerilme_max:.2f} MPa")
c2.metric("Emniyet Faktoru", f"{emniyet:.2f}")
with c3:
    if emniyet > 1.5: st.success("YAPI GUVENLI ✅")
    else: st.error("YAPI RISKLI ⚠️")

def pdf_olustur():
    pdf = FPDF()
    pdf.add_page()
    
    try:
        pdf.image('logo.png', 10, 8, 33)
    except:
        pass 
        
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(80) 
    pdf.cell(30, 10, 'StuMech Analiz Raporu', 0, 0, 'C')
    pdf.ln(20) 
    
    pdf.set_fill_color(230, 230, 230) 
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, ' Proje ve Sistem Detaylari', 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 11)
    veriler = [
        ["Kiris Uzunlugu:", f"{L} m"],
        ["Uygulanan Yuk (P):", f"{P} N"],
        ["Yuk Konumu (a):", f"{a} m"],
        ["Secilen Malzeme:", f"{secilen_malzeme}"], # Değişken adı düzeltildi
        ["Kesit Olculeri (b x h):", f"{b*1000:.0f} x {h*1000:.0f} mm"]
    ]
    
    for satir in veriler:
        pdf.cell(95, 10, satir[0], 1)
        pdf.cell(95, 10, satir[1], 1, 1)
        
    pdf.ln(10)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(200, 220, 255) 
    pdf.cell(0, 10, ' Muhendislik Hesaplamalari', 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(95, 10, "Maksimum Moment (Mmax):", 1)
    pdf.cell(95, 10, f"{M_max:.2f} Nm", 1, 1)
    
    pdf.cell(95, 10, "Maksimum Gerilme (Sigma):", 1)
    pdf.cell(95, 10, f"{gerilme_max:.2f} MPa", 1, 1)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(95, 10, "Emniyet Katsayisi (n):", 1)
    durum = "GUVENLI" if emniyet > 1.5 else "RISKLI"
    pdf.cell(95, 10, f"{emniyet:.2f} ({durum})", 1, 1)
    
    pdf.ln(20)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, 'Bu rapor StuMech Yazilimi tarafindan otomatik olarak olusturulmustur.', 0, 0, 'C')
    pdf.ln(5)
    pdf.cell(0, 10, 'Etik ve Kaliteli Muhendislik Icin.', 0, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
st.write("### 🗂️ Raporlama Merkezi")
st.download_button(label="📥 Profesyonel PDF Raporu Al", 
                   data=pdf_olustur(), 
                   file_name="StuMech_Teknik_Rapor.pdf", 
                   mime="application/pdf",
                   use_container_width=True)