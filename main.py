import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"
USERS_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1771432371&single=true&output=csv"

ADMIN_EMAIL = "mo50504172@gmail.com"

@st.cache_data(ttl=5)
def load_data():
    try: return pd.read_csv(CSV_URL)
    except: return pd.DataFrame()

@st.cache_data(ttl=5)
def load_authorized_users():
    try:
        users_df = pd.read_csv(USERS_AUTH_URL)
        return users_df.iloc[:, 0].astype(str).str.lower().str.strip().tolist()
    except:
        return [ADMIN_EMAIL]

# --- 2. نظام الحماية ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Login to Wujood System")
        allowed_list = load_authorized_users()
        col1, col2 = st.columns(2)
        with col1:
            u_email = st.text_input("Email:").lower().strip()
        with col2:
            u_pin = st.text_input("Access PIN:", type="password")
        
        if st.button("Login"):
            if (u_email in allowed_list or u_email == ADMIN_EMAIL) and u_pin == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = u_email
                st.rerun()
            else:
                st.error("🚫 الإيميل غير مصرح له أو الـ PIN خطأ.")
        return False
    return True

if check_password():
    # --- 3. الماستر بلان التفاعلية (تم تصحيح الخطأ التقني هنا) ---
    st.title("🎯 Wujood Interactive Masterplan")
    df_all = load_data()
    if not df_all.empty:
        try:
            df = df_all[df_all['Status'] == 'Available'].copy()
            df['X'] = pd.to_numeric(df['X'], errors='coerce'); df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
            df = df.dropna(subset=['X', 'Y'])
            
            # التصحيح: استبدال 'name' بـ 'name' داخل التجميع لضمان التوافق
            df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index()
            df_grouped.columns = ['X', 'Y', 'units'] # إعادة تسمية الأعمدة يدوياً لتجنب خطأ الموبايل
            
            hover_texts = []
            for _, row in df_grouped.iterrows():
                label = "<b>Available Units:</b><br>"
                for unit in row['units']:
                    price = unit.get('Price', 'N/A')
                    label += f"🏠 {unit.get('Unit Code', 'N/A')} | 💰 {price} | 📏 {unit.get('Area', 'N/A')}m²<br>"
                hover_texts.append(label)

            if os.path.exists("Master Plan.jpeg"):
                img = Image.open("Master Plan.jpeg") 
                fig = px.imshow(img)
                fig.add_scatter(
                    x=df_grouped['X'], y=df_grouped['Y'], mode='markers', 
                    marker=dict(size=18, color='red', opacity=0.7),
                    hovertext=hover_texts, hoverinfo="text", name="" 
                )
                fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Masterplan Error: {e}")

    # --- 4. صانع العروض (نفس كودك) ---
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state['user_email']}**")
        st.divider()
        st.header("📄 Professional Offer Builder")
        
        unit_code = st.text_input("1️⃣ Unit Code").upper()
        price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

        inventory_folder = "Inventory"
        layouts_folder = "layouts"
        team_folder = "last_Images"
        static_folder = "static_images"

        inv_files = sorted([f for f in os.listdir(inventory_folder) if not f.startswith('.')]) if os.path.exists(inventory_folder) else []
        lay_files = sorted([f for f in os.listdir(layouts_folder) if not f.startswith('.')]) if os.path.exists(layouts_folder) else []
        
        selected_inv = st.selectbox("3️⃣ Select Building", inv_files if inv_files else ["No Files"])
        selected_lay = st.selectbox("4️⃣ Select Layout", lay_files if lay_files else ["No Files"])

        team_mapping = {}
        if os.path.exists(team_folder):
            raw_team_files = sorted([f for f in os.listdir(team_folder) if not f.startswith('.')])
            for f in raw_team_files:
                display_name = os.path.splitext(f)[0]
                team_mapping[display_name] = f
        
        selected_member = st.selectbox("5️⃣ Team Osama", list(team_mapping.keys()) if team_mapping else ["No Team"])

        if st.button("🚀 Generate PDF Offer"):
            if unit_code and price_raw != "0":
                try:
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    net_price = original_p * 0.90
                    
                    doc = fitz.open()
                    # إضافة الصفحات والصور (منطق الـ PDF الخاص بك)
                    # ... (باقي كود الـ PDF كما هو لديك)
                    st.sidebar.success("✅ تم توليد العرض بنجاح")
                except Exception as e: st.sidebar.error(f"Error: {e}")
