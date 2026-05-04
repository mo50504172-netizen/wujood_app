import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# رابط الشيت النهائي
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5) # تحديث البيانات كل 5 ثواني
def load_data():
    return pd.read_csv(CSV_URL)

try:
    st.set_page_config(layout="wide", page_title="Tharaa Town Project")
    df_all = load_data()

    # فلترة الوحدات المتاحة فقط
    df = df_all[df_all['Status'] == 'Available'].copy()

    # التأكد من أن الإحداثيات أرقام
    df['X'] = pd.to_numeric(df['X'], errors='coerce')
    df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
    df = df.dropna(subset=['X', 'Y'])

    # تجميع الوحدات اللي في نفس المبنى (نفس X و Y)
    df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

    hover_labels = []
    for _, row in df_grouped.iterrows():
        label = "<b>Units in this Building:</b><br>"
        for unit in row['units']:
            # معالجة تنسيق السعر لتجنب خطأ Cannot specify ',' with 's'
            try:
                # تنظيف السعر من أي علامات غير رقمية وتحويله لـ float
                price_val = float(str(unit.get('Price', 0)).replace(',', ''))
                price_str = f"{price_val:,.0f} EGP"
            except:
                price_str = "N/A"
            
            unit_code = unit.get('Unit Code', 'N/A')
            area_val = unit.get('Area', 'N/A')
            
            label += f"• {unit_code} | {price_str} | {area_val}m²<br>"
        hover_labels.append(label)

    # تحميل صورة الماستر بلان
    img = Image.open("Master Plan.jpeg") 
    fig = px.imshow(img)

    # إضافة النقط على الخريطة
    fig.add_scatter(
        x=df_grouped['X'], 
        y=df_grouped['Y'],
        mode='markers',
        marker=dict(size=18, color='red', symbol='circle', opacity=0.8),
        hovertext=hover_labels,
        hoverinfo="text"
    )

    # إعدادات شكل الخريطة
    fig.update_layout(
        dragmode='pan', 
        width=1200, 
        height=850, 
        margin=dict(l=0, r=0, t=40, b=0)
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)

    st.title("🎯 Wujood Interactive Masterplan")
    st.write(f"إجمالي الوحدات المتاحة حالياً: {len(df)}")
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"حدث خطأ في عرض البيانات: {e}")