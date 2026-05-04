import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from fpdf import FPDF
import os

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Wujood Interactive Portal")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip()
    return data

# 2. دالة بناء الـ PDF الاحترافية (الحل الجذري)
def create_pdf(unit_row, consultant_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    def add_auto_image(img_path, draw_circle=False):
        if os.path.exists(img_path):
            pdf.add_page()
            # حفظ أبعاد الصورة الأصلية لمنع "الكشة"
            img = Image.open(img_path)
            w, h = img.size
            aspect = w / h
            
            # حساب الأبعاد لتملأ الصفحة (297x210) مع الحفاظ على التناسب
            if aspect > (297/210):
                pdf.image(img_path, x=0, y=(210 - (297/aspect))/2, w=297)
            else:
                pdf.image(img_path, x=(297 - (210*aspect))/2, y=0, h=210)

            if draw_circle:
                pdf.set_draw_color(255, 0, 0)
                pdf.set_line_width(1.5)
                # إحداثيات دقيقة مربوطة بمركز الصورة
                ux = (unit_row['X'] / 1000) * 297
                uy = (unit_row['Y'] / 1000) * 210
                pdf.ellipse(ux - 5, uy - 5, 10, 10)

    # إضافة البروشور
    for i in range(1, 5):
        add_auto_image(f"static_images/{i}.jpeg")

    # إضافة الماستر بلان
    add_auto_image("Master Plan.jpeg", draw_circle=True)

    # إضافة التقسيمة (Layout) - البحث الذكي بالمساحة وكلمة Garden
    area_val = str(unit_row['Area']).split('+')[0].strip()
    layout_folder = "layouts"
    if os.path.exists(layout_folder):
        all_layouts = os.listdir(layout_folder)
        # البحث عن ملف يحتوي على المساحة وإذا كانت بحديقة
        target_file = None
        for f in all_layouts:
            if area_val in f:
                if "garden" in str(unit_row['Area']).lower() and "garden" in f.lower():
                    target_file = f
                    break
                elif "garden" not in str(unit_row['Area']).lower() and "garden" not in f.lower():
                    target_file = f
                    break
        
        if target_file:
            add_auto_image(os.path.join(layout_folder, target_file))

    # إضافة صورة الكونسلتنت (الربط المباشر بالاختيار)
    consult_path = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(consult_path):
        add_auto_image(consult_path)

    return bytes(pdf.output(dest='S'))

# 3. واجهة البرنامج
try:
    df_all = load_data()
    st.sidebar.image("static_images/1.jpeg", width=150)
    # القائمة التي تختار منها السيلز
    sales_list = ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"]
    selected_sales = st.sidebar.selectbox("Property Consultant:", sales_list)
    
    tab1, tab2 = st.tabs(["📍 Master Plan", "📄 PDF Offer"])

    with tab1:
        df = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        
        img_map = Image.open("Master Plan.jpeg")
        fig = px.imshow(img_map)
        fig.add_scatter(x=df['X'], y=df['Y'], mode='markers',
                        marker=dict(size=12, color='red', line=dict(width=1, color='white')),
                        hovertext=df['Unit Code'])
        fig.update_layout(width=1000, height=750, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Generate Professional Unit Offer")
        u_code = st.selectbox("Select Unit:", sorted(df_all['Unit Code'].unique()))
        u_info = df_all[df_all['Unit Code'] == u_code].iloc[0]
        
        if st.button(f"Generate High-Res PDF for {u_code}"):
            with st.spinner("Processing..."):
                try:
                    pdf_data = create_pdf(u_info, selected_sales)
                    st.download_button(
                        label="📥 Download PDF Offer",
                        data=pdf_data,
                        file_name=f"Offer_{u_code}.pdf",
                        mime="application/pdf"
                    )
                    st.success(f"PDF matches {selected_sales} profile and {u_code} layouts!")
                except Exception as e:
                    st.error(f"Error: {e}")

except Exception as e:
    st.error(f"System Error: {e}")
