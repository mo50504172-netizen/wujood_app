import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import time

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# الروابط الخاصة بك (تأكد أنها روابط CSV من شيت Final_Data)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"
USERS_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1771432371&single=true&output=csv"

ADMIN_EMAIL = "mo50504172@gmail.com"

# وظيفة إضافة "مانع الكاش" للروابط لضمان التحديث اللحظي
def get_live_url(url):
    return f"{url}&cache_buster={int(time.time())}"

@st.cache_data(ttl=10)
def load_data(url):
    try: 
        data = pd.read_csv(get_live_url(url))
        data.columns = data.columns.str.strip()
        return data.dropna(how='all')
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_authorized_users():
    try:
        users_df = pd.read_csv(get_live_url(USERS_AUTH_URL))
        return users_df.iloc[:, 0].astype(str).str.lower().str.strip().tolist()
    except:
        return [ADMIN_EMAIL]

# --- 2. نظام الحماية والدخول ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Tharaa Town - Sales System Login")
        allowed_list = load_authorized_users()

        col1, col2 = st.columns(2)
        with col1:
            u_email = st.text_input("Email:").lower().strip()
        with col2:
            u_pin = st.text_input("Access PIN:", type="password")
        
        if st.button("Login"):
            # تصحيح تلقائي للإيميل
            u_email = u_email.replace("gamil.com", "gmail.com")
            
            if (u_email in allowed_list or u_email == ADMIN_EMAIL) and u_pin == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = u_email
                st.rerun()
            else:
                st.error("🚫 الإيميل غير مسجل أو الـ PIN خطأ.")
        return False
    return True

if check_password():
    
    # --- 3. الماستر بلان التفاعلية ---
    st.title("🎯 Wujood Interactive Masterplan")
    
    # زر تحديث يدوي اختياري
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    df_all = load_data(CSV_URL)
    
    if not df_all.empty:
        try:
            df_all['Status'] = df_all['Status'].astype(str).str.strip().str.capitalize()
            df_all['X'] = pd.to_numeric(df_all['X'], errors='coerce')
            df_all['Y'] = pd.to_numeric(df_all['Y'], errors='coerce')
            
            # فلترة الوحدات المتاحة
            df_available = df_all[(df_all['Status'] == 'Available') & (df_all['X'].notnull())].copy()
            
            if df_available.empty:
                st.warning("⚠️ لا توجد وحدات متاحة حالياً.")
            else:
                plot_points = []
                for (x, y), group in df_available.groupby(['X', 'Y']):
                    label = "<b>Available Units:</b><br>"
                    for _, unit in group.iterrows():
                        label += f"🏠 {unit.get('Unit Code','?')} | 💰 {unit.get('Price','?')} | 📏 {unit.get('Area','?')}m²<br>"
                    plot_points.append({'X': x, 'Y': y, 'Hover': label})
                
                df_plot = pd.DataFrame(plot_points)

                if os.path.exists("Master Plan.jpeg"):
                    img = Image.open("Master Plan.jpeg") 
                    fig = px.imshow(img)
                    fig.add_scatter(
                        x=df_plot['X'], y=df_plot['Y'], mode='markers', 
                        marker=dict(size=22, color='red', opacity=0.8, line=dict(width=2, color='white')),
                        hovertext=df_plot['Hover'], hoverinfo="text"
                    )
                    fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ ملف Master Plan.jpeg مفقود.")
        except Exception as e: 
            st.info("جاري تحديث الخريطة...")

    # --- 4. صانع العروض الاحترافي (Sidebar) ---
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state['user_email']}**")
        if st.button("تسجيل الخروج"):
            st.session_state["authenticated"] = False
            st.rerun()
            
        st.divider()
        st.header("📄 Offer Builder")
        
        unit_code = st.text_input("Unit Code").upper()
        price_raw = st.text_input("Original Price (EGP)", value="0")

        # المجلدات
        static_f = "static_images"
        inv_f = "Inventory"
        lay_f = "layouts"
        team_f = "last_Images"

        def get_files(folder):
            return sorted([f for f in os.listdir(folder) if not f.startswith('.')]) if os.path.exists(folder) else []

        selected_inv = st.selectbox("Select Building", get_files(inv_f) or ["Empty"])
        selected_lay = st.selectbox("Select Layout", get_files(lay_f) or ["Empty"])
        
        team_files = get_files(team_f)
        team_names = [os.path.splitext(f)[0] for f in team_files]
        selected_member = st.selectbox("Team Member", team_names or ["Empty"])

        if st.button("🚀 Generate PDF"):
            if not unit_code or price_raw == "0":
                st.error("أدخل البيانات")
            else:
                try:
                    # حسابات الخصم
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    net_price = original_p * 0.90
                    
                    doc = fitz.open()

                    def add_pdf_img(path, file):
                        full_path = os.path.join(path, file)
                        if os.path.exists(full_path) and file != "Empty":
                            img_doc = fitz.open(full_path)
                            doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # دمج الصفحات
                    for s in get_files(static_f): add_pdf_img(static_f, s)
                    add_pdf_img(inv_f, selected_inv)
                    
                    # صفحة السعر
                    page = doc.new_page()
                    page.insert_text((72, 70), f"Unit: {unit_code}", fontsize=20)
                    page.insert_text((72, 120), f"Price: {net_price:,.0f} EGP (After 10% Discount)", fontsize=15, color=(0, 0.5, 0))
                    
                    add_pdf_img(lay_f, selected_lay)
                    if selected_member in team_names:
                        add_pdf_img(team_f, team_files[team_names.index(selected_member)])

                    pdf_bytes = doc.write()
                    st.success("✅ Ready")
                    st.download_button("📥 Download PDF", pdf_bytes, f"{unit_code}_Offer.pdf")
                except Exception as e:
                    st.error(f"Error: {e}")
