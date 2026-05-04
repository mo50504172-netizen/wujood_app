import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from fpdf import FPDF
import os

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Tharaa Town Project")

# 2. رابط البيانات
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5) 
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip()
    return data

# 3. دالة بناء الـ PDF (التعديل هنا)
def create_pdf(unit_row, consultant_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # صفحات البروشور
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210)
    
    # صفحة الماستر بلان
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        pdf.image("Master Plan.jpeg", 0, 0, 297, 210)
        pdf.set_draw_color(255, 0, 0)
        pdf.set_line_width(1)
        pos_x = (unit_row['X'] / 1000) * 297
        pos_y = (unit_row['Y'] / 1000) * 210
        pdf.ellipse(pos_x - 5, pos_y - 5, 10, 10)

    # صفحة الكونسلتنت
    consultant_img = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(consultant_img):
        pdf.add_page()
        pdf.image(consultant_img, 0, 0, 297, 210)

    # التعديل: تحويل الـ output لـ bytes بشكل صريح
    return bytes(pdf.output(dest='S'))

try:
    df_all = load_data()
    st.sidebar.title("Sales Portal")
    sel_sales = st.sidebar.selectbox("Property Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    tab1, tab2 = st.tabs(["📍 Available Units Only", "📄 Create PDF Offer"])

    with tab1:
        df = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

        hover_labels = []
        for _, row in df_grouped.iterrows():
            label = "<b>Units in this Building:</b><br>"
            for unit in row['units']:
                try:
                    p_val = float(str(unit.get('Price', 0)).replace(',', ''))
                    p_str = f"{p_val:,.0f} EGP"
                except: p_str = "N/A"
                label += f"• {unit.get('Unit Code')} | {p_str} | {unit.get('Area')}m²<br>"
            hover_labels.append(label)

        img = Image.open("Master Plan.jpeg") 
        fig = px.imshow(img)
        fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                        marker=dict(size=18, color='red', symbol='circle', opacity=0.8, line=dict(width=2, color='white')),
                        hovertext=hover_labels, hoverinfo="text")
        fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0), hovermode='closest')
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Generate Professional PDF Offer")
        unit_to_offer = st.selectbox("Select Unit Code:", df_all['Unit Code'].unique())
        unit_data = df_all[df_all['Unit Code'] == unit_to_offer].iloc[0]
        
        if st.button(f"Generate Offer for {unit_to_offer}"):
            with st.spinner("Preparing PDF..."):
                try:
                    # جلب البيانات بصيغة bytes
                    final_pdf = create_pdf(unit_data, sel_sales)
                    st.download_button(
                        label="📥 Download PDF Offer", 
                        data=final_pdf, 
                        file_name=f"Wujood_{unit_to_offer}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF Fixed! Click the button above to download.")
                except Exception as e:
                    st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error: {e}")
