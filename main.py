import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from fpdf import FPDF
import os

# 1. الإعدادات العامة للبرنامج
st.set_page_config(layout="wide", page_title="Wujood Professional Sales Portal")

# رابط البيانات من جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip()
    return data

# 2. دالة بناء الـ PDF الاحترافية (تثبيت الأبعاد والدائرة)
def create_pdf(unit_row, consultant_name):
    # إنشاء ملف PDF بالعرض (Landscape)
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    def add_standard_page(img_path, is_master_plan=False):
        if os.path.exists(img_path):
            pdf.add_page()
            # جعل الصورة تملأ عرض الصفحة بالكامل (297 مم)
            pdf.image(img_path, x=0, y=0, w=297)
            
            if is_master_plan:
                # رسم دائرة تعليم الوحدة بدقة
                pdf.set_draw_color(255, 0, 0)
                pdf.set_line_width(1.5)
                # حساب الإحداثيات بناءً على عرض الصورة في الـ PDF
                ux = (unit_row['X'] / 1000) * 297
                uy = (unit_row['Y'] / 1000) * (297 * (Image.open(img_path).height / Image.open(img_path).width))
                pdf.ellipse(ux - 4, uy - 4, 8, 8)

    # إضافة البروشور (الصور من 1 لـ 4)
    for i in range(1, 5):
        add_standard_page(f"static_images/{i}.jpeg")

    # إضافة الماستر بلان (مع الدائرة المظبوطة)
    add_standard_page("Master Plan.jpeg", is_master_plan=True)

    # إضافة تقسيمة الوحدة (البحث الذكي بالمساحة والحديقة)
    unit_area_str = str(unit_row['Area']).lower()
    area_key = unit_area_str.split('+')[0].strip()
    layout_folder = "layouts"
    if os.path.exists(layout_folder):
        target_layout = None
        for f in os.listdir(layout_folder):
            if area_key in f:
                if "garden" in unit_area_str and "garden" in f.lower():
                    target_layout = f
                    break
                elif "garden" not in unit_area_str and "garden" not in f.lower():
                    target_layout = f
                    break
        if target_layout:
            add_standard_page(os.path.join(layout_folder, target_layout))

    # إضافة صفحة السيلز المختار من القائمة
    sales_path = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(sales_path):
        add_standard_page(sales_path)

    return bytes(pdf.output(dest='S'))

# 3. واجهة المستخدم (UI)
try:
    df_all = load_data()
    st.sidebar.title("Sales Portal")
    
    # اختيار السيلز (سيؤثر فوراً على آخر صفحة في الـ PDF)
    sales_names = ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"]
    selected_consultant = st.sidebar.selectbox("Select Consultant:", sales_names)
    
    tab1, tab2 = st.tabs(["📍 Interactive Master Plan", "📄 Generate Professional Offer"])

    with tab1:
        # عرض الماستر بلان بدون محاور أرقام (Clean View)
        df_av = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        master_img = Image.open("Master Plan.jpeg")
        fig = px.imshow(master_img)
        
        fig.add_scatter(x=df_av['X'], y=df_av['Y'], mode='markers',
                        marker=dict(size=12, color='red', line=dict(width=1, color='white')),
                        hovertext=df_av['Unit Code'])
        
        # إخفاء الأرقام والمحاور تماماً
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        fig.update_layout(width=1100, height=850, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Create Unit Offer PDF")
        unit_code_sel = st.selectbox("Choose Unit Code:", sorted(df_all['Unit Code'].unique()))
        unit_info = df_all[df_all['Unit Code'] == unit_code_sel].iloc[0]
        
        if st.button(f"Generate PDF for {unit_code_sel}"):
            with st.spinner("Aligning high-res images and coordinates..."):
                try:
                    pdf_final = create_pdf(unit_info, selected_consultant)
                    st.download_button(
                        label="📥 Download Professional PDF",
                        data=pdf_final,
                        file_name=f"Offer_{unit_code_sel}.pdf",
                        mime="application/pdf"
                    )
                    st.success(f"PDF matches {selected_consultant} profile and {unit_code_sel} location.")
                except Exception as e:
                    st.error(f"Error: {e}")

except Exception as e:
    st.error(f"System Load Error: {e}")
