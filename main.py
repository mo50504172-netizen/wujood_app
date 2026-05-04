import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="THARAA - Wujood Project")

# 2. دالة بناء الـ PDF مع تمييز الوحدة المطلوبة
def create_pdf(unit_data, sales_person, last_image_path):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # صفحات البروشور الأساسية
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210)
    
    # صفحة تحديد مكان الوحدة على الماستر بلان
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        pdf.image("Master Plan.jpeg", 0, 0, 297, 210)
        # رسم دائرة حمراء "منورة" لتمييز الوحدة المختارة فقط
        pdf.set_draw_color(255, 0, 0)
        pdf.set_line_width(1.5)
        # تحويل إحداثيات الشيت لتناسب مقاس صفحة الـ PDF
        ux = (unit_data['X'] / 1000) * 297
        uy = (1 - (unit_data['Y'] / 1000)) * 210
        pdf.ellipse(ux - 5, uy - 5, 10, 10) 

    # صفحة الحسابات المالية
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"Unit Offer: {unit_data['Unit Code']}", ln=True, align='C')
    price_after = float(unit_data['Price'])
    pdf.set_font("Arial", size=14)
    pdf.cell(0, 10, f"Price After Discount: {price_after:,.0f} EGP", ln=True)
    
    plans = [
        ("1- Payment Plan: 0% Over 7Y", 0.035, 0.035, "7 Years"),
        ("2- Payment Plan: 5% Over 8Y", 0.05, 0.029, "8 Years"),
        ("3- Payment Plan: 5% Over 10Y", 0.05, 0.0192, "10 Years"),
        ("4- Payment Plan: 10% Over 10Y", 0.10, 0.02, "10 Years")
    ]
    for title, dp, q, per in plans:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, title, ln=True, fill=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 7, f"Down Payment: {price_after * dp:,.0f} EGP", ln=True)
        pdf.cell(0, 7, f"Quarterly: {price_after * q:,.0f} EGP", ln=True)
        pdf.ln(2)

    # صفحة الـ Layout
    lay_path = f"layouts/{unit_data['Area']}.jpeg"
    if os.path.exists(lay_path):
        pdf.add_page()
        pdf.image(lay_path, 10, 10, 277)

    if os.path.exists(last_image_path):
        pdf.add_page()
        pdf.image(last_image_path, 0, 0, 297, 210)
        
    return pdf.output(dest='S').encode('latin-1')

# 3. الربط مع البيانات والواجهة
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(sheet_url)

try:
    df = load_data()
    st.sidebar.title("Sales Portal")
    sel_sales = st.sidebar.selectbox("Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    t1, t2 = st.tabs(["📍 Available Units Only", "📄 Create PDF Offer"])
    
    with t1:
        st.subheader("Live Master Plan")
        # إظهار المتاح فقط
        available_only = df[df['Status'].str.contains('Available', case=False, na=False)]
        
        if os.path.exists("Master Plan.jpeg"):
            fig = px.scatter(available_only, x='X', y='Y', hover_name='Unit Code')
            # كود عرض صورة الخلفية بشكل صحيح
            fig.add_layout_image(
                dict(source="https://raw.githubusercontent.com/mo50504172-netizen/wujood_app/main/Master%20Plan.jpeg",
                     xref="x", yref="y", x=0, y=1000, sizex=1000, sizey=1000, sizing="stretch", layer="below")
            )
            fig.update_layout(xaxis=dict(range=[0,1000]), yaxis=dict(range=[0,1000]))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Master Plan image file not found in repository.")

    with t2:
        sel_unit = st.selectbox("Select Unit:", df['Unit Code'].unique())
        u_info = df[df['Unit Code'] == sel_unit].iloc[0]
        l_img = f"last_images/{sel_sales}.jpeg"
        
        if st.button(f"Generate PDF for {sel_unit}"):
            pdf_bytes = create_pdf(u_info, sel_sales, l_img)
            st.download_button("📥 Download PDF", pdf_bytes, f"Tharaa_{sel_unit}.pdf", "application/pdf")

except Exception as e:
    st.error(f"Error: {e}")
