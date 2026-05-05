import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Tharaa Town Project")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    return pd.read_csv(CSV_URL)

# دالة لجلب الملفات من المجلدات
def get_files(folder):
    if os.path.exists(folder):
        return sorted([f for f in os.listdir(folder) if not f.startswith('.')])
    return []

# --- 2. الواجهة الرئيسية (الماستر بلان أونلاين) ---
st.title("🎯 Wujood Interactive Masterplan")

try:
    df_all = load_data()
    df = df_all[df_all['Status'] == 'Available'].copy()
    df['X'] = pd.to_numeric(df['X'], errors='coerce')
    df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
    df = df.dropna(subset=['X', 'Y'])

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
    fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                    marker=dict(size=18, color='red', opacity=0.8),
                    hovertext=hover_labels, hoverinfo="text")
    fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    
    st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.error(f"Error loading Masterplan: {e}")

# --- 3. الشريط الجانبي (أداة صنع العروض - بنفس خطوات الأوفلاين) ---
with st.sidebar:
    st.header("📄 Offer Builder (Steps)")
    st.info("اتبع الخطوات أدناه لإنشاء العرض")

    # الخطوة 1: البيانات الأساسية
    unit_code = st.text_input("1️⃣ Enter Unit Code", placeholder="e.g. W-101").upper()
    price_input = st.text_input("2️⃣ Enter Price (EGP)", value="0")
    
    # الخطوة 2: اختيار المبنى
    inv_files = get_files("Inventory")
    selected_inv = st.selectbox("3️⃣ Select Building Image", inv_files)

    # الخطوة 3: اختيار التقسيمة
    layout_files = get_files("layouts")
    selected_layout = st.selectbox("4️⃣ Select Unit Layout", layout_files)

    # الخطوة 4: اختيار المندوب
    rep_folder = "last images" if os.path.exists("last images") else "last_images"
    rep_files = get_files(rep_folder)
    selected_rep = st.selectbox("5️⃣ Select Representative", rep_files)

    # زر التنفيذ
    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_input == "0":
            st.error("يرجى إدخال كود الوحدة والسعر أولاً!")
        else:
            try:
                original_price = float(price_input.replace(',', ''))
                discount_amount = original_price * 0.10
                p_total = original_price - discount_amount

                # الأنظمة المالية
                p1_dp, p1_bullet, p1_inst = p_total * 0.10, p_total * 0.10, (p_total * 0.80) / 39
                p2_dp1, p2_dp2, p2_inst = p_total * 0.05, p_total * 0.05, (p_total * 0.90) / 31
                p3_dp1, p3_dp2, p3_bullet, p3_inst = p_total * 0.05, p_total * 0.05, p_total * 0.15, (p_total * 0.75) / 38

                # إنشاء الـ PDF
                doc = fitz.open()

                # إضافة الصور الثابتة
                static_dir = "static_images"
                if os.path.exists(static_dir):
                    for img_name in sorted(os.listdir(static_dir)):
                        img_path = os.path.join(static_dir, img_name)
                        img_doc = fitz.open(img_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                # إضافة الصفحات المختارة
                for folder, file in [("Inventory", selected_inv), ("layouts", selected_layout), (rep_folder, selected_rep)]:
                    path = os.path.join(folder, file)
                    temp_doc = fitz.open(path)
                    if path.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # صفحة الأسعار
                page = doc.new_page()
                page.insert_text((72, 50), "Project: Wujood", fontsize=24)
                page.insert_text((72, 80), f"Unit: {unit_code} | Layout: {os.path.splitext(selected_layout)[0]}", fontsize=15)
                page.insert_text((72, 115), f"Original Price: {original_price:,.0f} EGP", fontsize=14)
                page.insert_text((72, 160), f"Final Price: {p_total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                y = 200
                options = [
                    ("Option 1 (10% DP):", f"- DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bullet:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                    ("Option 2 (5% + 5%):", f"- DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                    ("Option 3 (Premium):", f"- DP1: {p3_dp1:,.0f} | DP2: {p3_dp2:,.0f} | Bullet: {p3_bullet:,.0f} | 38 Quarters: {p3_inst:,.0f}")
                ]
                for title, detail in options:
                    page.insert_text((72, y), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), detail, fontsize=11)
                    y += 70

                pdf_bytes = doc.write()
                st.sidebar.success(f"✅ تم تجهيز عرض {unit_code}")
                st.sidebar.download_button(label="📥 Download PDF", data=pdf_bytes, file_name=f"Offer_{unit_code}.pdf", mime="application/pdf")
            
            except Exception as e:
                st.sidebar.error(f"حدث خطأ: {e}")
