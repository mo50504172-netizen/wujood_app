import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="THARAA - Wujood Project")

# 2. دالة الـ PDF (التي تضع علامة حمراء على الوحدة المختارة فقط)
def create_pdf(unit_data, sales_person, last_image_path):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    # الصفحات الثابتة
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210)
    
    # صفحة الماستر بلان مع تحديد مكان الوحدة
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        pdf.image("Master Plan.jpeg", 0, 0, 297, 210)
        pdf.set_draw_color(255, 0, 0) # أحمر
        pdf.set_line_width(1.5)
        # تحويل الإحداثيات لمقاس الصفحة
        ux = (unit_data['X'] / 1000) * 297
        uy = (1 - (unit_data['Y'] / 1000)) * 210
        pdf.ellipse(ux - 4, uy - 4, 8, 8)

    # صفحة البيانات المالية
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"Unit: {unit_data['Unit Code']}", ln=True, align='C')
    # ... بقية حسابات الأوفر ...
    
    return pdf.output(dest='S').encode('latin-1')

# 3. تحميل البيانات والواجهة
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(sheet_url)

try:
    df = load_data()
    st.sidebar.title("Sales Portal")
    sel_sales = st.sidebar.selectbox("Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    t1, t2 = st.tabs(["📍 Live Master Plan", "📄 Create PDF Offer"])
    
    with t1:
        # فلترة المتاح فقط للمعاينة
        available_df = df[df['Status'].str.contains('Available', case=False, na=False)]
        
        # رسم الخريطة التفاعلية بدون محاور (Clean View)
        fig = px.scatter(available_df, x='X', y='Y', 
                         hover_name='Unit Code',
                         # هنا التفاصيل اللي بتظهر لما تقف بالماوس
                         hover_data={'X':False, 'Y':False, 'Area':True, 'Floor':True, 'Price':':,.0f'})
        
        fig.add_layout_image(
            dict(source="https://raw.githubusercontent.com/mo50504172-netizen/wujood_app/main/Master%20Plan.jpeg",
                 xref="x", yref="y", x=0, y=1000, sizex=1000, sizey=1000, sizing="stretch", layer="below")
        )
        
        # إخفاء المحاور والأرقام تماماً لتنظيف الشكل
        fig.update_xaxes(showgrid=False, zeroline=False, visible=False, range=[0, 1000])
        fig.update_yaxes(showgrid=False, zeroline=False, visible=False, range=[0, 1000])
        
        fig.update_traces(marker=dict(size=12, color='red', symbol='circle')) # علامات حمراء واضحة
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=700)
        
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        # اختيار الوحدة لعمل الأوفر
        sel_unit = st.selectbox("Select Unit:", df['Unit Code'].unique())
        u_info = df[df['Unit Code'] == sel_unit].iloc[0]
        
        if st.button(f"Generate Offer for {sel_unit}"):
            pdf_bytes = create_pdf(u_info, sel_sales, f"last_images/{sel_sales}.jpeg")
            st.download_button("📥 Download PDF", pdf_bytes, f"Offer_{sel_unit}.pdf")

except Exception as e:
    st.error(f"Waiting for connection... {e}")
