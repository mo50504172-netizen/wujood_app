import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from fpdf import FPDF
import os

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="Wujood Interactive Portal")

# 2. روابط البيانات
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip() # تنظيف أسماء الأعمدة
    return data

# 3. دالة إنشاء الـ PDF (مع جلب الصور من الفولدرات اللي رفعتها)
def create_pdf(unit_row, consultant_name):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # إضافة الصور التعريفية (1-4) من static_images
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            pdf.image(img_path, 0, 0, 297, 210)
    
    # إضافة صفحة الماستر بلان وعليها علامة الوحدة
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        pdf.image("Master Plan.jpeg", 0, 0, 297, 210)
        # رسم دائرة حول الوحدة (تحويل إحداثيات 1000 إلى مم A4)
        pdf.set_draw_color(255, 0, 0)
        pdf.set_line_width(1)
        # ملاحظة: تم تعديل الحسبة لتناسب الـ imshow
        pos_x = (unit_row['X'] / 1000) * 297
        pos_y = (unit_row['Y'] / 1000) * 210
        pdf.ellipse(pos_x - 5, pos_y - 5, 10, 10)

    # إضافة صورة الكونسلتنت من last_images
    consultant_img = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(consultant_img):
        pdf.add_page()
        pdf.image(consultant_img, 0, 0, 297, 210)

    return pdf.output(dest='S').encode('latin-1')

try:
    df_all = load_data()
    
    # الشريط الجانبي
    st.sidebar.image("static_images/1.jpeg", use_column_width=True) # لوجو المشروع
    sel_sales = st.sidebar.selectbox("Property Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    tab1, tab2 = st.tabs(["📍 Available Units Only", "📄 Create PDF Offer"])

    with tab1:
        # فلترة المتاح فقط وتحويل الإحداثيات
        df = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        # التجميع الذكي للوحدات في نفس النقطة (حل مشكلة عدم ظهور الوحدات المكررة)
        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

        hover_labels = []
        for _, row in df_grouped.iterrows():
            label = "<b>Units in this Building:</b><br>"
            for unit in row['units']:
                try:
                    p_val = float(str(unit.get('Price', 0)).replace(',', ''))
                    p_str = f"{p_val:,.0f} EGP"
                except: p_str = "Contact Sales"
                label += f"• {unit.get('Unit Code')} | {p_str} | {unit.get('Area')}m²<br>"
            hover_labels.append(label)

        # عرض الخريطة باستخدام imshow (لضمان دقة الإحداثيات 100%)
        img = Image.open("Master Plan.jpeg")
        fig = px.imshow(img)

        fig.add_scatter(
            x=df_grouped['X'], 
            y=df_grouped['Y'],
            mode='markers',
            marker=dict(size=18, color='red', symbol='circle', opacity=0.7, line=dict(width=2, color='white')),
            hovertext=hover_labels,
            hoverinfo="text"
        )

        fig.update_layout(
            dragmode='pan',
            margin=dict(l=0, r=0, t=0, b=0),
            height=800,
            hovermode='closest'
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)

        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Generate Professional PDF Offer")
        unit_to_offer = st.selectbox("Select Unit Code:", df_all['Unit Code'].unique())
        unit_data = df_all[df_all['Unit Code'] == unit_to_offer].iloc[0]
        
        if st.button(f"Generate Offer for {unit_to_offer}"):
            with st.spinner("Preparing PDF..."):
                pdf_data = create_pdf(unit_data, sel_sales)
                st.download_button(label="📥 Download PDF Offer", data=pdf_data, file_name=f"Wujood_Offer_{unit_to_offer}.pdf")
                st.success("PDF Generated successfully with all project layouts!")

except Exception as e:
    st.error(f"Waiting for connection or data format error: {e}")
