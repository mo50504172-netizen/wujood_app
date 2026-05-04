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

# 3. دالة بناء الـ PDF الاحترافية (بأحجام طبيعية)
def create_pdf(unit_row, consultant_name):
    # إنشاء PDF بالعرض A4
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # صفحات البروشور الأساسية (1-4)
    for i in range(1, 5):
        img_path = f"static_images/{i}.jpeg"
        if os.path.exists(img_path):
            pdf.add_page()
            # استخدام عرض 297mm (كامل الصفحة) مع ترك الارتفاع يتحدد تلقائياً للحفاظ على الأبعاد
            pdf.image(img_path, x=0, y=0, w=297) 

    # صفحة الماستر بلان (بشكل مستطيل طبيعي)
    if os.path.exists("Master Plan.jpeg"):
        pdf.add_page()
        # وضع الصورة في المنتصف بحجمها الطبيعي المستطيل
        pdf.image("Master Plan.jpeg", x=0, y=0, w=297)
        
        # رسم دائرة الوحدة (باللون الأحمر)
        pdf.set_draw_color(255, 0, 0)
        pdf.set_line_width(1)
        # الإحداثيات مربوطة بالـ imshow (1000x1000)
        ux = (unit_row['X'] / 1000) * 297
        uy = (unit_row['Y'] / 1000) * 210
        pdf.ellipse(ux - 4, uy - 4, 8, 8)

    # صفحة الـ Layout (البحث التلقائي بمساحة الوحدة)
    # نأخذ الرقم الصحيح للمساحة (مثلاً 145 من 145.5)
    unit_area = str(unit_row['Area']).split('.')[0] 
    layout_folder = "layouts"
    if os.path.exists(layout_folder):
        # البحث عن ملف يبدأ بالمساحة المطلوبة
        match_files = [f for f in os.listdir(layout_folder) if f.startswith(unit_area)]
        if match_files:
            pdf.add_page()
            # إضافة بلان الوحدة بحجم مستطيل متناسق
            pdf.image(os.path.join(layout_folder, match_files[0]), x=10, y=10, w=277)

    # صفحة الكونسلتنت المختار
    consultant_img = f"last_images/{consultant_name}.jpeg"
    if os.path.exists(consultant_img):
        pdf.add_page()
        pdf.image(consultant_img, x=0, y=0, w=297)

    return bytes(pdf.output(dest='S'))

try:
    df_all = load_data()
    st.sidebar.title("Sales Portal")
    sel_sales = st.sidebar.selectbox("Property Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    tab1, tab2 = st.tabs(["📍 Live Master Plan", "📄 Create PDF Offer"])

    with tab1:
        # نظام الـ imshow لضمان دقة مكان النقطة على الشاشة
        df = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

        hover_labels = []
        for _, row in df_grouped.iterrows():
            label = "<b>Units Available:</b><br>"
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
        
        fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=0, b=0), hovermode='closest')
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Generate Professional Offer")
        unit_to_offer = st.selectbox("Select Unit Code:", sorted(df_all['Unit Code'].unique()))
        unit_data = df_all[df_all['Unit Code'] == unit_to_offer].iloc[0]
        
        if st.button(f"Create Offer for {unit_to_offer}"):
            with st.spinner("Searching for layout and consultant image..."):
                try:
                    pdf_bytes = create_pdf(unit_data, sel_sales)
                    st.download_button(
                        label="📥 Download PDF", 
                        data=pdf_bytes, 
                        file_name=f"Offer_{unit_to_offer}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF generated with original image ratios!")
                except Exception as e:
                    st.error(f"Error: {e}")

except Exception as e:
    st.error(f"An error occurred: {e}")
