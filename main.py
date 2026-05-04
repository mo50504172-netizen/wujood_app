import streamlit as st
import pandas as pd
from fpdf import FPDF
import os
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(layout="wide", page_title="THARAA - Wujood Project")

# 2. تحميل البيانات مع معالجة الأسماء والأسعار
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=2)
def load_data():
    data = pd.read_csv(sheet_url)
    # تنظيف أسماء الأعمدة من أي مسافات مخفية
    data.columns = data.columns.str.strip()
    # التأكد من أن السعر أرقام فقط
    if 'Price' in data.columns:
        data['Price'] = pd.to_numeric(data['Price'], errors='coerce')
    return data

try:
    df = load_data()
    st.sidebar.title("Sales Portal")
    sel_sales = st.sidebar.selectbox("Consultant:", ["Basmala", "Farag", "Gamal", "Jo", "Nady", "os", "Rawda", "Salma"])
    
    tab_map, tab_pdf = st.tabs(["📍 Live Master Plan", "📄 Create PDF Offer"])
    
    with tab_map:
        # عرض الوحدات المتاحة فقط
        available_df = df[df['Status'].str.contains('Available', case=False, na=False)].copy()
        
        # حل مشكلة تكرار الوحدات في نفس النقطة (عن طريق إضافة إزاحة بسيطة جداً لا تلاحظ إلا عند التكبير)
        # أو استخدام Plotly Hover الـ Clickable
        
        fig = px.scatter(available_df, x='X', y='Y', 
                         hover_name='Unit Code',
                         # عرض السعر والمساحة والحالة بدقة
                         hover_data={'X':False, 'Y':False, 'Price':':,.0f', 'Area':True, 'Status':True},
                         color_discrete_sequence=['red'])
        
        # إضافة الصورة بالخلفية مع تثبيت الحجم الأصلي (1000x1000) لضمان دقة النقط
        fig.add_layout_image(
            dict(source="https://raw.githubusercontent.com/mo50504172-netizen/wujood_app/main/Master%20Plan.jpeg",
                 xref="x", yref="y", x=0, y=1000, sizex=1000, sizey=1000, sizing="stretch", layer="below")
        )
        
        # إعدادات العرض (إخفاء المحاور وتثبيت المدى)
        fig.update_xaxes(visible=False, range=[0, 1000])
        fig.update_yaxes(visible=False, range=[0, 1000])
        
        # تحسين شكل النقطة وتفعيل التفاعل عند وجود وحدات مكررة
        fig.update_traces(marker=dict(size=14, opacity=0.8, line=dict(width=1, color='White')))
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=800,
            hovermode='closest' # يضمن إظهار أقرب وحدة للماوس بدقة
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 إذا وجدت نقطة تحتوي على أكثر من وحدة، استخدم أدوات الزوم (Zoom) أعلى الخريطة لتفريقهم.")

    with tab_pdf:
        # اختيار الوحدة لعمل الـ PDF
        sel_unit = st.selectbox("Select Unit:", df['Unit Code'].unique())
        # ... كود إنشاء الـ PDF اللي شغالين عليه ...
        st.write(f"Unit Selected: {sel_unit}")

except Exception as e:
    st.error(f"Please check spreadsheet headers or connection: {e}")
