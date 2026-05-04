import streamlit as st
import pandas as pd
from PIL import Image
from fpdf import FPDF
import os

# إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Tharaa Town - Professional PDF")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip()
    return data

def create_pdf(unit_row, consultant_name):
    # استخدام orientation='L' (عرضي) و format='A4'
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)

    # 1. صفحات البروشور (بجودة عالية)
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210) # ملء الصفحة بالكامل

    # 2. صفحة الـ Master Plan مع إخفاء البيانات وتعليم الوحدة
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        pdf.image("Master Plan.jpeg", 0, 0, 297, 210)
        
        # --- إخفاء الاسم والرقم بشكل احترافي ---
        # رسم مستطيلات بلون الخلفية (تقريباً أخضر غامق/زيتي) لإخفاء النصوص
        pdf.set_fill_color(34, 54, 44) # درجة تقريبية لخلفية الصورة
        pdf.rect(100, 105, 70, 10, 'F') # إخفاء "Mohamed Osama"
        pdf.rect(190, 105, 50, 10, 'F') # إخفاء الرقم
        
        # --- تعليم مكان الوحدة ---
        pdf.set_draw_color(255, 0, 0) # أحمر
        pdf.set_line_width(1.5)
        # تحويل الإحداثيات لتناسب حجم الورقة A4 عرضياً
        pos_x = (unit_row['X'] / 1000) * 297
        pos_y = (unit_row['Y'] / 1000) * 210
        pdf.ellipse(pos_x - 4, pos_y - 4, 8, 8) 

    # 3. صفحة الـ Layout (البحث بالمساحة)
    unit_area = str(unit_row['Area']).split('.')[0] # أخذ الرقم الصحيح للمساحة
    layout_folder = "layouts"
    if os.path.exists(layout_folder):
        # البحث عن ملف يبدأ بالمساحة
        files = [f for f in os.listdir(layout_folder) if f.startswith(unit_area)]
        if files:
            pdf.add_page()
            pdf.image(os.path.join(layout_folder, files[0]), 10, 10, 277, 190)

    # 4. صفحة الـ Consultant (آخر صفحة باسم الشخص المختار)
    consultant_img = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(consultant_img):
        pdf.add_page()
        pdf.image(consultant_img, 0, 0, 297, 210)

    return bytes(pdf.output(dest='S'))

# واجهة المستخدم
try:
    df_all = load_data()
    st.sidebar.title("Sales Portal")
    # اختيار الـ Consultant
    sel_sales = st.sidebar.selectbox("Property Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    st.subheader("Generate Professional PDF Offer")
    unit_code = st.selectbox("Select Unit Code:", df_all['Unit Code'].unique())
    unit_data = df_all[df_all['Unit Code'] == unit_code].iloc[0]
    
    if st.button(f"Generate High Quality Offer for {unit_code}"):
        with st.spinner("Processing Professional Layouts..."):
            pdf_bytes = create_pdf(unit_data, sel_sales)
            st.download_button(
                label="📥 Download Corrected PDF",
                data=pdf_bytes,
                file_name=f"Offer_{unit_code}_{sel_sales}.pdf",
                mime="application/pdf"
            )
            st.success("PDF generated with professional cleanup and high-res images.")

except Exception as e:
    st.error(f"Error: {e}")
