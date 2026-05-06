import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# الروابط الخاصة بك
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"
USERS_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1771432371&single=true&output=csv"

ADMIN_EMAIL = "mo50504172@gmail.com"

# وظائف تحميل البيانات مع تنظيف جذري
@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(CSV_URL)
        # تنظيف أسماء الأعمدة من أي مسافات مخفية
        data.columns = data.columns.str.strip()
        # حذف الصفوف التي لا تحتوي على بيانات أساسية
        return data.dropna(how='all')
    except Exception as e:
        st.error(f"Error Loading Sheet: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_authorized_users():
    try:
        users_df = pd.read_csv(USERS_AUTH_URL)
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
            if (u_email in allowed_list or u_email == ADMIN_EMAIL) and u_pin == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = u_email
                st.rerun()
            else:
                st.error("🚫 الإيميل غير مصرح له أو الـ PIN خطأ.")
        return False
    return True

if check_password():
    
    # --- 3. الماستر بلان التفاعلية (الحل الجذري للنقط الحمراء) ---
    st.title("🎯 Wujood Interactive Masterplan")
    df_all = load_data()
    
    if not df_all.empty:
        try:
            # تنظيف عمود الحالة والإحداثيات لضمان الفلترة
            df_all['Status'] = df_all['Status'].astype(str).str.strip().str.capitalize()
            df_all['X'] = pd.to_numeric(df_all['X'], errors='coerce')
            df_all['Y'] = pd.to_numeric(df_all['Y'], errors='coerce')
            
            # فلترة الوحدات المتاحة فقط
            df_available = df_all[df_all['Status'] == 'Available'].dropna(subset=['X', 'Y']).copy()
            
            if df_available.empty:
                st.warning("⚠️ لا توجد وحدات متاحة (Available) حالياً في الشيت أو الإحداثيات مفقودة.")
            
            # تجميع البيانات يدوياً لضمان عدم حدوث Length Mismatch
            plot_points = []
            df_grouped = df_available.groupby(['X', 'Y'])
            
            for (x, y), group in df_grouped:
                label = "<b>Available Units:</b><br>"
                for _, unit in group.iterrows():
                    label += f"🏠 {unit.get('Unit Code', 'N/A')} | 💰 {unit.get('Price', 'N/A')} | 📏 {unit.get('Area', 'N/A')}m²<br>"
                plot_points.append({'X': x, 'Y': y, 'Hover': label})
            
            # تحويل النتائج لـ DataFrame جديد للعرض
            df_plot = pd.DataFrame(plot_points)

            if os.path.exists("Master Plan.jpeg"):
                img = Image.open("Master Plan.jpeg") 
                fig = px.imshow(img)
                
                if not df_plot.empty:
                    fig.add_scatter(
                        x=df_plot['X'], y=df_plot['Y'], mode='markers', 
                        marker=dict(size=20, color='red', opacity=0.8, line=dict(width=2, color='white')),
                        hovertext=df_plot['Hover'], hoverinfo="text", name="" 
                    )
                
                fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ ملف 'Master Plan.jpeg' غير موجود في المجلد.")
        except Exception as e: 
            st.error(f"Masterplan Error: {e}")

    # --- 4. صانع العروض ---
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state['user_email']}**")
        st.divider()
        st.header("📄 Professional Offer Builder")
        
        unit_code = st.text_input("1️⃣ Unit Code").upper()
        price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

        # تعريف المجلدات
        folders = {
            "static": "static_images",
            "inv": "Inventory",
            "lay": "layouts",
            "team": "last_Images"
        }

        def get_files(folder_name):
            if os.path.exists(folder_name):
                return sorted([f for f in os.listdir(folder_name) if not f.startswith('.')])
            return []

        selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", get_files(folders["inv"]) or ["No Files Found"])
        selected_lay = st.selectbox("4️⃣ Select Unit Layout", get_files(folders["lay"]) or ["No Files Found"])

        team_files = get_files(folders["team"])
        team_names = [os.path.splitext(f)[0] for f in team_files]
        selected_member = st.selectbox("5️⃣ Team Osama", team_names or ["No Team Photos"])

        if st.button("🚀 Generate PDF Offer"):
            if not unit_code or price_raw == "0":
                st.error("الرجاء إدخال كود الوحدة والسعر الصحيح")
            else:
                try:
                    # الحسابات المالية (10% خصم)
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    net_price = original_p * 0.90
                    discount = original_p * 0.10

                    doc = fitz.open()

                    # إضافة الصور من المجلدات المختلفة
                    def add_image_to_pdf(folder, filename):
                        if filename and filename != "No Files Found":
                            path = os.path.join(folder, filename)
                            if os.path.exists(path):
                                img_doc = fitz.open(path)
                                doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # 1. الصور الثابتة
                    for s in get_files(folders["static"]): add_image_to_pdf(folders["static"], s)
                    # 2. صورة المبنى
                    add_image_to_pdf(folders["inv"], selected_inv)
                    
                    # 3. صفحة الحسابات
                    page = doc.new_page()
                    page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22)
                    page.insert_text((72, 110), f"Unit: {unit_code} | Original: {original_p:,.0f} EGP", fontsize=12)
                    page.insert_text((72, 135), f"Discount 10%: -{discount:,.0f} | Final Price: {net_price:,.0f} EGP", fontsize=14, color=(0, 0.4, 0))
                    
                    # خطط السداد
                    p1_dp = net_price * 0.10
                    p1_inst = (net_price * 0.80) / 39
                    
                    y = 200
                    page.insert_text((72, y), "Standard Plan (10% DP):", fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), f"Down Payment: {p1_dp:,.0f} | 39 Quarters: {p1_inst:,.0f}", fontsize=10)

                    # 4. الـ Layout وصورة الموظف
                    add_image_to_pdf(folders["lay"], selected_lay)
                    if selected_member in team_names:
                        add_image_to_pdf(folders["team"], team_files[team_names.index(selected_member)])

                    pdf_bytes = doc.write()
                    st.sidebar.success("✅ PDF Generated")
                    st.sidebar.download_button("📥 Download Offer", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
                except Exception as e:
                    st.sidebar.error(f"PDF Error: {e}")
