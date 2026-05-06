import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import time

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# الروابط الخاصة بك
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"
USERS_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1771432371&single=true&output=csv"

ADMIN_EMAIL = "mo50504172@gmail.com"

# وظيفة تحميل البيانات مع نظام محاولات متكررة لضمان الاستقرار أثناء تحديث الشيت
def load_data_robust(url):
    for i in range(3):  # يحاول 3 مرات في حالة وجود تهنيج من جوجل
        try:
            df = pd.read_csv(url)
            if not df.empty:
                df.columns = df.columns.str.strip()
                return df.dropna(how='all')
        except:
            time.sleep(1)
    return pd.DataFrame()

# تحميل المستخدمين بدون Cache طويل لضمان سرعة التحديث عند إضافة موظف جديد
@st.cache_data(ttl=2)
def load_authorized_users():
    df = load_data_robust(USERS_AUTH_URL)
    if not df.empty:
        # استخراج أول عمود، حذف الفراغات، تحويل لحروف صغيرة
        return df.iloc[:, 0].dropna().astype(str).str.lower().str.strip().tolist()
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
            # تصحيح تلقائي لغلطة gamil الشهيرة لضمان دخول الموظف
            processed_email = u_email.replace("gamil.com", "gmail.com")
            
            if (processed_email in allowed_list or processed_email == ADMIN_EMAIL) and u_pin == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = processed_email
                st.rerun()
            else:
                st.error("🚫 الإيميل غير مسجل أو الـ PIN خطأ. تأكد من كتابة البيانات صحيحة.")
        return False
    return True

# --- يبدأ التطبيق فقط بعد تسجيل الدخول بنجاح ---
if check_password():
    
    # --- 3. الماستر بلان التفاعلية (الحل الجذري للنقط الحمراء) ---
    st.title("🎯 Wujood Interactive Masterplan")
    df_all = load_data_robust(CSV_URL)
    
    if not df_all.empty:
        try:
            # تنظيف البيانات لضمان الفلترة الصحيحة
            df_all['Status'] = df_all['Status'].astype(str).str.strip().str.capitalize()
            df_all['X'] = pd.to_numeric(df_all['X'], errors='coerce')
            df_all['Y'] = pd.to_numeric(df_all['Y'], errors='coerce')
            
            # فلترة الوحدات المتاحة فقط
            df_available = df_all[df_all['Status'] == 'Available'].dropna(subset=['X', 'Y']).copy()
            
            if df_available.empty:
                st.warning("⚠️ لا توجد وحدات متاحة (Available) حالياً، أو جاري تحديث البيانات من الشيت.")
            
            # تجميع البيانات للنقط يدوياً لضمان عدم حدوث لغبطة في الإحداثيات
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
                
                if not df_plot.empty:
                    fig.add_scatter(
                        x=df_plot['X'], y=df_plot['Y'], mode='markers', 
                        marker=dict(size=22, color='red', opacity=0.8, line=dict(width=2, color='white')),
                        hovertext=df_plot['Hover'], hoverinfo="text", name="" 
                    )
                
                fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("❌ ملف 'Master Plan.jpeg' مفقود.")
        except Exception as e: 
            st.info("🔄 جاري مزامنة البيانات مع شيت جوجل...")

    # --- 4. صانع العروض الاحترافي ---
    with st.sidebar:
        st.write(f"المستخدم: **{st.session_state['user_email']}**")
        if st.button("تسجيل الخروج"):
            st.session_state["authenticated"] = False
            st.rerun()
            
        st.divider()
        st.header("📄 Professional Offer Builder")
        
        unit_code = st.text_input("1️⃣ Unit Code").upper()
        price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

        # تعريف المجلدات
        static_folder = "static_images"
        inventory_folder = "Inventory"
        layouts_folder = "layouts"
        team_folder = "last_Images"

        def get_files(folder):
            if os.path.exists(folder):
                return sorted([f for f in os.listdir(folder) if not f.startswith('.')])
            return []

        selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", get_files(inventory_folder) or ["No Files Found"])
        selected_lay = st.selectbox("4️⃣ Select Unit Layout", get_files(layouts_folder) or ["No Files Found"])

        team_files = get_files(team_folder)
        team_names = [os.path.splitext(f)[0] for f in team_files]
        selected_member = st.selectbox("5️⃣ Team Osama", team_names or ["No Team Photos"])

        if st.button("🚀 Generate PDF Offer"):
            if not unit_code or price_raw == "0":
                st.error("أدخل كود الوحدة والسعر")
            else:
                try:
                    # الحسابات المالية (خصم 10%)
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    net_price = original_p * 0.90
                    discount = original_p * 0.10

                    doc = fitz.open()

                    # دالة إضافة الصور للـ PDF
                    def add_img(f_path, f_name):
                        if f_name != "No Files Found":
                            p = os.path.join(f_path, f_name)
                            if os.path.exists(p):
                                img_doc = fitz.open(p)
                                doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # دمج الصفحات
                    for s in get_files(static_folder): add_img(static_folder, s)
                    add_img(inventory_folder, selected_inv)
                    
                    # صفحة الحسابات
                    page = doc.new_page()
                    page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22)
                    page.insert_text((72, 110), f"Unit: {unit_code} | Original: {original_p:,.0f} EGP", fontsize=12)
                    page.insert_text((72, 135), f"Discount 10%: -{discount:,.0f} | Final: {net_price:,.0f} EGP", fontsize=14, color=(0, 0.4, 0))
                    
                    # مثال لخطة سداد
                    y = 200
                    page.insert_text((72, y), "10% Down Payment Plan:", fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), f"DP: {net_price*0.10:,.0f} | 39 Quarters: {(net_price*0.80)/39:,.0f}", fontsize=10)

                    add_img(layouts_folder, selected_lay)
                    if selected_member in team_names:
                        add_img(team_folder, team_files[team_names.index(selected_member)])

                    pdf_bytes = doc.write()
                    st.sidebar.success("✅ Offer Ready")
                    st.sidebar.download_button("📥 Download PDF", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
                except Exception as e:
                    st.sidebar.error(f"Error: {e}")
