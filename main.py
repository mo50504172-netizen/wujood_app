import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة (يجب أن تكون أول أمر في Streamlit) ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# --- 2. نظام الحماية (Login System) ---
def check_password():
    """يرجع True إذا كان المستخدم أدخل بيانات صحيحة."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Tharaa Town - Access Control")
        
        # قائمة الإيميلات المصرح لها (الـ 50 إيميل بتوعك)
        AUTHORIZED_EMAILS = [
            "m.osama@tharaatown.com", 
            "basmala@gmail.com",
            "youssef@gmail.com",
            "farag@gmail.com",
            "nady@gmail.com",
            "gamal@gmail.com",
            "salma@gmail.com"
        ]

        col1, col2 = st.columns(2)
        with col1:
            user_email = st.text_input("Enter your authorized Email:").lower().strip()
        with col2:
            user_pin = st.text_input("Enter Access PIN:", type="password")
        
        if st.button("Login"):
            # الباسورد هنا هو 2026 (تقدر تغيره لأي رقم تاني)
            if user_email in AUTHORIZED_EMAILS and user_pin == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = user_email
                st.rerun()
            else:
                st.error("🚫 الإيميل غير مصرح له أو الـ PIN خطأ.")
        return False
    return True

# تفعيل النظام: إذا تم تسجيل الدخول، ابدأ تشغيل باقي الكود
if check_password():
    
    # --- 3. تحميل البيانات من جوجل شيت ---
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

    @st.cache_data(ttl=5)
    def load_data():
        try: 
            return pd.read_csv(CSV_URL)
        except: 
            return pd.DataFrame()

    # --- 4. واجهة الماستر بلان التفاعلية ---
    st.title("🎯 Wujood Interactive Masterplan")
    st.sidebar.success(f"User: {st.session_state['user_email']}")
    
    df_all = load_data()
    if not df_all.empty:
        try:
            # فلترة الوحدات المتاحة فقط
            df = df_all[df_all['Status'] == 'Available'].copy()
            df['X'] = pd.to_numeric(df['X'], errors='coerce')
            df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
            df = df.dropna(subset=['X', 'Y'])
            
            # تجميع الوحدات بنفس الإحداثيات عشان الـ Hover
            df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')
            
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
                fig.update_layout(
                    dragmode='pan', width=1200, height=850, 
                    margin=dict(l=0, r=0, t=40, b=0), showlegend=False
                )
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: 
            st.error(f"Masterplan Error: {e}")

    # --- 5. صانع العروض (Offer Builder) في السايدبار ---
    with st.sidebar:
        st.header("📄 Professional Offer Builder")
        st.divider()

        unit_code = st.text_input("1️⃣ Unit Code").upper()
        price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

        # تعريف المجلدات
        static_folder = "static_images"
        inventory_folder = "Inventory"
        layouts_folder = "layouts"
        team_folder = "last_Images"

        # قراءة الملفات من المجلدات
        inv_files = sorted([f for f in os.listdir(inventory_folder) if not f.startswith('.')]) if os.path.exists(inventory_folder) else []
        lay_files = sorted([f for f in os.listdir(layouts_folder) if not f.startswith('.')]) if os.path.exists(layouts_folder) else []
        
        selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["No Files Found"])
        selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["No Files Found"])

        team_mapping = {}
        if os.path.exists(team_folder):
            raw_team_files = sorted([f for f in os.listdir(team_folder) if not f.startswith('.')])
            for f in raw_team_files:
                display_name = os.path.splitext(f)[0]
                team_mapping[display_name] = f
        
        selected_member = st.selectbox("5️⃣ Team Member", list(team_mapping.keys()) if team_mapping else ["Check last_Images"])

        if st.button("🚀 Generate PDF Offer"):
            if not unit_code or price_raw == "0":
                st.error("أدخل كود الوحدة والسعر")
            else:
                try:
                    # حسابات الخصم وأنظمة السداد
                    clean_p = "".join(filter(str.isdigit, price_raw))
                    original_p = float(clean_p)
                    discount = original_p * 0.10
                    net_price = original_p - discount

                    # إنشاء ملف الـ PDF
                    doc = fitz.open()

                    # إضافة الصور الثابتة (اللوجو والمقدمة)
                    if os.path.exists(static_folder):
                        s_files = sorted([f for f in os.listdir(static_folder) if not f.startswith('.')])
                        for s in s_files:
                            img_doc = fitz.open(os.path.join(static_folder, s))
                            doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                    # إضافة صورة المشروع/المبنى
                    if selected_inv != "No Files Found":
                        inv_img = fitz.open(os.path.join(inventory_folder, selected_inv))
                        doc.insert_pdf(fitz.open("pdf", inv_img.convert_to_pdf()))

                    # صفحة بيانات الدفع
                    page = doc.new_page()
                    page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22)
                    page.insert_text((72, 110), f"Unit: {unit_code} | Original: {original_p:,.0f} EGP", fontsize=12)
                    page.insert_text((72, 135), f"Discount 10%: -{discount:,.0f} | Final Price: {net_price:,.0f} EGP", fontsize=14, color=(0, 0.4, 0))
                    
                    # عرض الأنظمة
                    y_pos = 200
                    plans = [
                        ("Option 1 (10% DP):", f"DP: {net_price*0.10:,.0f} | 39 Quarters: {(net_price*0.80)/39:,.0f}"),
                        ("Option 2 (5% + 5%):", f"DP1: {net_price*0.05:,.0f} | 31 Quarters: {(net_price*0.90)/31:,.0f}"),
                    ]
                    for title, text in plans:
                        page.insert_text((72, y_pos), title, fontsize=14, color=(0, 0.2, 0.6))
                        page.insert_text((80, y_pos+20), text, fontsize=10); y_pos += 75

                    # إضافة مسقط الوحدة وصورة الموظف
                    if selected_lay != "No Files Found":
                        lay_img = fitz.open(os.path.join(layouts_folder, selected_lay))
                        doc.insert_pdf(fitz.open("pdf", lay_img.convert_to_pdf()))

                    if selected_member in team_mapping:
                        member_img = fitz.open(os.path.join(team_folder, team_mapping[selected_member]))
                        doc.insert_pdf(fitz.open("pdf", member_img.convert_to_pdf()))

                    pdf_bytes = doc.write()
                    st.sidebar.success(f"✅ Offer Ready")
                    st.sidebar.download_button("📥 Download PDF", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
                except Exception as e: 
                    st.sidebar.error(f"Error: {e}")
