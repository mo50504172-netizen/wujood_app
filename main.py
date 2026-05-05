import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# 1. إعدادات الصفحة ورابط البيانات
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(CSV_URL)

# --- الجزء الأول: عرض الماستر بلان ---
st.title("🎯 Wujood Interactive Masterplan")

try:
    df_all = load_data()
    df = df_all[df_all['Status'] == 'Available'].copy()
    
    # تحويل الإحداثيات والأسعار
    df['X'] = pd.to_numeric(df['X'], errors='coerce')
    df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
    df = df.dropna(subset=['X', 'Y'])

    # تجميع الوحدات في المباني
    df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

    hover_labels = []
    for _, row in df_grouped.iterrows():
        label = "<b>Units in this Building:</b><br>"
        for unit in row['units']:
            try:
                price_val = float(str(unit.get('Price', 0)).replace(',', ''))
                price_str = f"{price_val:,.0f} EGP"
            except: price_str = "N/A"
            label += f"• {unit.get('Unit Code', 'N/A')} | {price_str} | {unit.get('Area', 'N/A')}m²<br>"
        hover_labels.append(label)

    img = Image.open("Master Plan.jpeg") 
    fig = px.imshow(img)
    fig.add_scatter(
        x=df_grouped['X'], y=df_grouped['Y'],
        mode='markers', marker=dict(size=18, color='red', opacity=0.8),
        hovertext=hover_labels, hoverinfo="text"
    )
    fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"إجمالي الوحدات المتاحة حالياً: {len(df)}")

except Exception as e:
    st.error(f"خطأ في عرض الماستر بلان: {e}")

st.markdown("---")

# --- الجزء الثاني: صانع العروض الاحترافي (Wujood Offer Builder) ---
st.header("📄 Create Professional Offer PDF")

col1, col2 = st.columns(2)

with col1:
    unit_code = st.text_input("Enter Full Unit Code (e.g., W-101)").strip().upper()
    original_price = st.number_input("Enter Original Price (EGP)", min_value=0.0, format="%.2f")

    # تحديد المجلدات (تأكد أن المجلدات مرفوعة بنفس الأسماء)
    inv_folder = "Inventory"
    layout_folder = "layouts"
    rep_folder = "last images" if os.path.exists("last images") else "last_images"

    # وظيفة لجلب الملفات من المجلدات
    def get_files(folder):
        if os.path.exists(folder):
            return sorted([f for f in os.listdir(folder) if not f.startswith('.')])
        return []

    selected_inv_file = st.selectbox("Step 1: Select Building Image", get_files(inv_folder))
    selected_layout_file = st.selectbox("Step 2: Select Unit Layout", get_files(layout_folder))
    selected_rep_file = st.selectbox("Step 3: Select Sales Representative", get_files(rep_folder))

if st.button("Generate & Download PDF Offer"):
    if not unit_code or original_price <= 0:
        st.warning("Please enter Unit Code and Price!")
    else:
        try:
            # الحسابات المالية
            discount_amount = original_price * 0.10
            p_total = original_price - discount_amount
            # نظام 1
            p1_dp, p1_bullet, p1_inst = p_total * 0.10, p_total * 0.10, (p_total * 0.80) / 39
            # نظام 2
            p2_dp1, p2_dp2, p2_inst = p_total * 0.05, p_total * 0.05, (p_total * 0.90) / 31
            # نظام 3
            p3_dp1, p3_dp2, p3_bullet, p3_inst = p_total * 0.05, p_total * 0.05, p_total * 0.15, (p_total * 0.75) / 38

            # إنشاء ملف PDF في الذاكرة
            doc = fitz.open()

            # 1. إضافة الصور الثابتة
            static_dir = "static_images"
            if os.path.exists(static_dir):
                for img_name in sorted(os.listdir(static_dir)):
                    img_path = os.path.join(static_dir, img_name)
                    img_doc = fitz.open(img_path)
                    doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

            # 2. إضافة صفحة المبنى والمساحة والمندوب
            for folder, file in [(inv_folder, selected_inv_file), (layout_folder, selected_layout_file), (rep_folder, selected_rep_file)]:
                path = os.path.join(folder, file)
                temp_doc = fitz.open(path)
                if path.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

            # 3. صفحة تفاصيل الأسعار
            page = doc.new_page()
            page.insert_text((72, 50), f"Project: Wujood", fontsize=24)
            page.insert_text((72, 80), f"Unit Code: {unit_code} | Area: {os.path.splitext(selected_layout_file)[0]}", fontsize=15)
            page.insert_text((72, 115), f"Original Price: {original_price:,.0f} EGP", fontsize=14)
            page.insert_text((72, 160), f"Final Price: {p_total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

            # الأنظمة
            y_pos = 200
            systems = [
                ("Option 1 (10% DP):", f"- DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bullet:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                ("Option 2 (5% + 5%):", f"- DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                ("Option 3 (Premium Plan):", f"- DP1: {p3_dp1:,.0f} | DP2 (3m): {p3_dp2:,.0f} | Bullet: {p3_bullet:,.0f} | 38 Quarters: {p3_inst:,.0f}")
            ]
            for title, detail in systems:
                page.insert_text((72, y_pos), title, fontsize=14, color=(0, 0.2, 0.6))
                page.insert_text((80, y_pos+20), detail, fontsize=11)
                y_pos += 70

            # حفظ الملف للإرسال للمستخدم
            pdf_bytes = doc.write()
            st.success(f"✅ Offer for {unit_code} is ready!")
            st.download_button(label="Download PDF Offer", data=pdf_bytes, file_name=f"Wujood_Offer_{unit_code}.pdf", mime="application/pdf")

        except Exception as e:
            st.error(f"حدث خطأ أثناء إنشاء الملف: {e}")
