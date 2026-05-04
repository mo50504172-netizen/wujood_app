import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="THARAA - Wujood Project")

# 2. دالة بناء الـ PDF
def create_pdf(unit_data, sales_person, last_image_path):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210)
    
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 15, f"Unit Offer: {unit_data['Unit Code']}", ln=True, align='C')
    
    price_after = float(unit_data['Price'])
    price_before = price_after * 1.10
    
    pdf.set_font("Arial", size=14)
    pdf.ln(10)
    pdf.cell(0, 10, f"Original Price: {price_before:,.0f} EGP", ln=True)
    pdf.cell(0, 10, f"Price After 10% Discount: {price_after:,.0f} EGP", ln=True)
    
    plans = [
        ("1- Payment Plan: 0% Over 7Y", 0.035, 0.035, "7 Years"),
        ("2- Payment Plan: 5% Over 8Y", 0.05, 0.029, "8 Years (80% over 31 Q)"),
        ("3- Payment Plan: 5% Over 10Y", 0.05, 0.0192, "10 Years (Bullet 15%)"),
        ("4- Payment Plan: 10% Over 10Y", 0.10, 0.02, "10 Years (90% over 39 Q)")
    ]
    
    for title, dp_rate, q_rate, period in plans:
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 8, title, ln=True, fill=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 7, f"Down Payment: {price_after * dp_rate:,.0f} EGP", ln=True)
        pdf.cell(0, 7, f"Quarterly Installment (Q): {price_after * q_rate:,.0f} EGP for {period}", ln=True)
        pdf.ln(2)

    layout_file = f"layouts/{unit_data['Area']}.jpeg"
    if os.path.exists(layout_file):
        pdf.add_page()
        pdf.image(layout_file, 10, 10, 277)

    if os.path.exists(last_image_path):
        pdf.add_page()
        pdf.image(last_image_path, 0, 0, 297, 210)
        
    return pdf.output(dest='S').encode('latin-1')

# 3. تحميل البيانات
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(sheet_url)

try:
    df = load_data()
    
    # القائمة الجانبية
    st.sidebar.title("Sales Portal")
    sales_team = ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma", "no name"]
    selected_sales = st.sidebar.selectbox("Property Consultant:", sales_team)
    
    # إنشاء التبويبات (Tabs)
    tab1, tab2 = st.tabs(["📍 Interactive Master Plan", "📄 Professional Offer Builder"])
    
    with tab1:
        st.subheader("Wujood Project - Live Availability")
        # كود الماستر بلان (بناءً على ملف Master Plan.jpeg عندك)
        if os.path.exists("Master Plan.jpeg"):
            fig = px.scatter(df, x='X', y='Y', color='Status', hover_name='Unit Code',
                             hover_data={'X':False, 'Y':False, 'Price':':,.0f', 'Area':True})
            fig.update_layout(images=[dict(source=os.path.abspath("Master Plan.jpeg"), 
                                           xref="x", yref="y", x=0, y=1000, sizex=1000, sizey=1000,
                                           sizing="stretch", layer="below")])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Master Plan image not found, showing data table instead.")
            st.dataframe(df)

    with tab2:
        st.subheader("Generate Professional PDF Offer")
        selected_unit = st.selectbox("Select Unit Code to Generate Offer:", df['Unit Code'].unique())
        unit_info = df[df['Unit Code'] == selected_unit].iloc[0]
        
        col1, col2 = st.columns(2)
        col1.metric("Area", unit_info['Area'])
        col2.metric("Price", f"{unit_info['Price']:,.0f} EGP")
        
        last_img_path = f"last_images/{selected_sales}.jpeg"
        
        if st.button(f"Create Offer for {selected_unit}"):
            with st.spinner("Processing PDF..."):
                pdf_bytes = create_pdf(unit_info, selected_sales, last_img_path)
                st.download_button(label="📥 Download PDF", data=pdf_bytes, 
                                   file_name=f"Tharaa_{selected_unit}.pdf", mime="application/pdf")

except Exception as e:
    st.error(f"Waiting for connection: {e}")
