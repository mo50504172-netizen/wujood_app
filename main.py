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

# وظائف تحميل البيانات
@st.cache_data(ttl=5)
def load_data():
    try: 
        data = pd.read_csv(CSV_URL)
        return data.dropna(how='all') # حذف الصفوف الفارغة تماماً
    except: 
        return pd.DataFrame()

@st.cache_data(ttl=5)
def load_authorized_users():
    try:
        users_df = pd.read_csv(USERS_AUTH_URL)
        return users_df.iloc[:, 0].astype(str).str.lower().str.strip().tolist()
    except:
        return [ADMIN_EMAIL]

# --- 2. نظام الحماية والدخول (Gatekeeper) ---
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

# --- يبدأ التطبيق فقط بعد تسجيل الدخول بنجاح ---
if check_password():
    
    # --- 3. الماستر بلان التفاعلية (تم تعديل جزء الـ Grouping لحل مشكلة الـ Mismatch) ---
    st.title("🎯 Wujood Interactive Masterplan")
    df_all = load_data()
    
    if not df_all.empty:
        try:
            # فلترة المتاح والتأكد من الأرقام
            df = df_all[df_all['Status'] == 'Available'].copy()
            df['X'] = pd.to_numeric(df['X'], errors='coerce')
            df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
            df = df.dropna(subset=['X', 'Y'])
            
            # حل مشكلة Length mismatch: استخدام تجميع يدوي أضمن
            df_grouped = df.groupby(['X', 'Y'])
            
            plot_x = []
            plot_y = []
            hover_texts = []
            
            for (x, y), group in df_grouped:
                plot_x.append(x)
                plot_y.append(y)
                label = "<b>Available Units:</b><br>"
                for _, unit in group.iterrows():
                    u_code = unit.get('Unit Code', 'N/A')
                    u_price = unit.get('Price', 'N/A')
                    u_area = unit.get('Area', 'N/A')
                    label += f"🏠 {u_code} | 💰 {u_price} | 📏 {u_area}m²<br>"
                hover_texts.append(label)

            if os.path.exists("Master Plan.jpeg"):
                img = Image.open("Master Plan.jpeg") 
                fig = px.imshow(img)
                fig.add_scatter(
                    x=plot_x, y=plot_y, mode='markers', 
                    marker=dict(size=18, color='red', opacity=0.7),
                    hovertext=hover_texts, hoverinfo="text", name="" 
                )
                fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ ملف 'Master Plan.jpeg' غير موجود في الفولدر الرئيسي.")
        except Exception as e: 
            st.error(f"Masterplan Error: {e}")

    # --- 4. صانع العروض (نفس كودك مع تحسينات بسيطة) ---
    with st.sidebar:
        st.write(f"Logged in: **{st.session_state['user_email']}**")
        st.divider()
        st.header("📄 Professional Offer Builder")
        
        unit_code = st.text_input("1️⃣ Unit Code").upper()
        price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

        # إعداد المسارات
        static_folder = "static_images"
        inventory_folder = "Inventory"
        layouts_folder = "layouts"
        team_folder = "last_Images"

        # دالة مساعدة لجلب الملفات
        def get_files(folder):
            if os.path.exists(folder):
                return sorted([f for f in os.listdir(folder) if not f.startswith('.')])
            return []

        inv_files = get_files(inventory_folder)
        lay_files = get_files(layouts_folder)
        
        selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["No Files Found"])
        selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["No Files Found"])

        team_mapping = {}
        team_files = get_files(team_folder)
        for f in team_files:
            display_name = os.path.splitext(f)[0]
            team_mapping[display_name] = f
        
        selected_member = st.selectbox("5️⃣ Team Osama", list(team_mapping.keys()) if team_mapping else ["No Team Photos Found"])

        if st.button("🚀 Generate PDF Offer"):
            if not unit_code or price_raw == "0":
                st.error("أدخل كود الوحدة والسعر")
            else:
                try:
                    # الحسابات
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    discount = original_p * 0.10
                    net_price = original_p - discount

                    p1 = {"dp": net_price*0.10, "bull": net_price*0.10, "inst": (net_price*0.80)/39}
                    p2 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "inst": (net_price*0.90)/31}
                    p3 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "bull": net_price*0.15, "inst": (net_price*0.75)/38}

                    doc = fitz.open()

                    # 1. الصور الثابتة (Intro)
                    static_files = get_files(static_folder)
                    for s in static_files:
                        img_path = os.path.join(static_folder, s)
                        img_doc = fitz.open(img_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # 2. صورة المبنى
                    if selected_inv != "No Files Found":
                        inv_path = os.path.join(inventory_folder, selected_inv)
                        img_doc = fitz.open(inv_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # 3. صفحة الحسابات
                    page = doc.new_page()
                    page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22)
                    page.insert_text((72, 110), f"Unit: {unit_code} | Original: {original_p:,.0f} EGP", fontsize=12)
                    page.insert_text((72, 135), f"Discount 10%: -{discount:,.0f} | Final: {net_price:,.0f} EGP", fontsize=14, color=(0, 0.4, 0))
                    
                    y_pos = 200
                    plans = [
                        ("Option 1 (10% DP):", f"DP: {p1['dp']:,.0f} | Bullet: {p1['bull']:,.0f} | 39 Quarters: {p1['inst']:,.0f}"),
                        ("Option 2 (5% + 5%):", f"DP1: {p2['dp1']:,.0f} | DP2: {p2['dp2']:,.0f} | 31 Quarters: {p2['inst']:,.0f}"),
                        ("Option 3 (Premium):", f"DP1: {p3['dp1']:,.0f} | Bullet: {p3['bull']:,.0f} | 38 Quarters: {p3['inst']:,.0f}")
                    ]
                    for title, text in plans:
                        page.insert_text((72, y_pos), title, fontsize=14, color=(0, 0.2, 0.6))
                        page.insert_text((80, y_pos+20), text, fontsize=10); y_pos += 75

                    # 4. الـ Layout وصورة الموظف
                    if selected_lay != "No Files Found":
                        lay_path = os.path.join(layouts_folder, selected_lay)
                        img_doc = fitz.open(lay_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    if selected_member in team_mapping:
                        member_path = os.path.join(team_folder, team_mapping[selected_member])
                        img_doc = fitz.open(member_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    pdf_bytes = doc.write()
                    st.sidebar.success(f"✅ Offer Ready")
                    st.sidebar.download_button("📥 Download PDF Offer", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
                except Exception as e: 
                    st.sidebar.error(f"Error generating PDF: {e}")
