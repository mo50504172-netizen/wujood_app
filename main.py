import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from fpdf import FPDF
import os

# 1. إعدادات الصفحة الأساسية
st.set_page_config(layout="wide", page_title="Tharaa Town - Professional Portal")

# رابط بيانات جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    data = pd.read_csv(CSV_URL)
    data.columns = data.columns.str.strip()
    return data

# 2. دالة بناء الـ PDF الاحترافية (Full Bleed - بدون هوامش بيضاء)
def create_pdf(unit_row, consultant_name):
    # إنشاء ملف PDF بمقاس A4 عرضي
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # وظيفة داخلية لإضافة الصور لتملأ الصفحة بالكامل 297x210
    def add_page_image(img_path, draw_circle=False):
        if os.path.exists(img_path):
            pdf.add_page()
            # 0, 0 هي نقطة البداية، و 297, 210 هي أبعاد الصفحة كاملة لضمان عدم وجود بياض
            pdf.image(img_path, 0, 0, 297, 210)
            
            if draw_circle:
                # رسم دائرة تعليم مكان الوحدة (أحمر)
                pdf.set_draw_color(255, 0, 0)
                pdf.set_line_width(1.2)
                # تحويل الإحداثيات من نظام الـ imshow (1000) لمقاس الورقة
                ux = (unit_row['X'] / 1000) * 297
                uy = (unit_row['Y'] / 1000) * 210
                pdf.ellipse(ux - 5, uy - 5, 10, 10)

    # أ- إضافة أول 4 صور (البروشور)
    for i in range(1, 5):
        add_page_image(f"static_images/{i}.jpeg")

    # ب- إضافة الماستر بلان مع تعليم الوحدة
    add_page_image("Master Plan.jpeg", draw_circle=True)

    # ج- سحب تقسيمة الوحدة (Layout) تلقائياً بناءً على المساحة
    # الكود يبحث عن ملف يبدأ بنفس رقم المساحة في فولدر layouts
    unit_area = str(unit_row['Area']).split('.')[0]
    layout_folder = "layouts"
    if os.path.exists(layout_folder):
        match_files = [f for f in os.listdir(layout_folder) if f.startswith(unit_area)]
        if match_files:
            add_page_image(os.path.join(layout_folder, match_files[0]))

    # د- إضافة صفحة الكونسلتنت المختار (آخر صفحة)
    add_page_image(f"last_images/{consultant_name}.jpeg")

    return bytes(pdf.output(dest='S'))

# 3. واجهة البرنامج (Streamlit UI)
try:
    df_all = load_data()
    st.sidebar.title("Sales Management")
    # اختيار الشخص اللي هيظهر صورته في آخر الـ PDF
    sel_sales = st.sidebar.selectbox("Property Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    tab1, tab2 = st.tabs(["📍 Master Plan (Live)", "📄 PDF Offer Builder"])

    with tab1:
        # نظام الـ imshow لضمان دقة إحداثيات الوحدات على الشاشة
        df = df_all[df_all['Status'].str.contains('Available', case=False, na=False)].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        
        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')
        
        hover_labels = []
        for _, row in df_grouped.iterrows():
            txt = "<b>Available Units:</b><br>"
            for u in row['units']:
                txt += f"• {u['Unit Code']} | {u['Area']}m²<br>"
            hover_labels.append(txt)
        
        img_map = Image.open("Master Plan.jpeg")
        fig = px.imshow(img_map)
        fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                        marker=dict(size=15, color='red', line=dict(width=1, color='white')),
                        hovertext=hover_labels, hoverinfo="text")
        
        fig.update_layout(width=1100, height=800, margin=dict(l=0,r=0,b=0,t=0))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Generate Unit Offer")
        # اختيار كود الوحدة لعمل الـ PDF
        unit_codes = sorted(df_all['Unit Code'].unique())
        selected_code = st.selectbox("Select Unit Code:", unit_codes)
        unit_info = df_all[df_all['Unit Code'] == selected_code].iloc[0]
        
        if st.button(f"Generate High-Res PDF for {selected_code}"):
            with st.spinner("Aligning layouts and images..."):
                try:
                    pdf_output = create_pdf(unit_info, sel_sales)
                    st.download_button(
                        label="📥 Download Corrected PDF",
                        data=pdf_output,
                        file_name=f"Offer_{selected_code}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF generated perfectly! No white margins, and unit location is marked.")
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

except Exception as e:
    st.error(f"System Error: {e}")
