import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Tharaa Town Project")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except:
        return pd.DataFrame()

# دالة ذكية لجلب الملفات مع التأكد من اسم المجلد
def get_files(folder_name):
    # السيرفر بيفرق بين الحروف الكبيرة والصغيرة، دي محاولة لإيجاد المجلد أياً كان اسمه
    actual_folder = None
    if os.path.exists(folder_name):
        actual_folder = folder_name
    elif os.path.exists(folder_name.lower()):
        actual_folder = folder_name.lower()
    elif os.path.exists(folder_name.capitalize()):
        actual_folder = folder_name.capitalize()
    
    if actual_folder:
        files = sorted([f for f in os.listdir(actual_folder) if not f.startswith('.')])
        return actual_folder, files
    return None, []

# --- 2. الواجهة الرئيسية (الماستر بلان) ---
st.title("🎯 Wujood Interactive Masterplan")

df_all = load_data()
if not df_all.empty:
    try:
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

        hover_labels = []
        for _, row in df_grouped.iterrows():
            label = "<b>Units:</b><br>"
            for unit in row['units']:
                label += f"• {unit.get('Unit Code', 'N/A')} | {unit.get('Area', 'N/A')}m²<br>"
            hover_labels.append(label)

        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=18, color='red', opacity=0.8),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Masterplan Error: {e}")

# --- 3. الشريط الجانبي (صنع العروض) ---
with st.sidebar:
    st.header("📄 Offer Builder")
    
    unit_code = st.text_input("1️⃣ Unit Code").upper()
    price_input = st.text_input("2️⃣ Price (EGP)", value="0")
    
    # جلب الملفات والتأكد من المسارات
    inv_path, inv_files = get_files("Inventory")
    lay_path, lay_files = get_files("layouts")
    rep_path, rep_files = get_files("last_images") # جربنا المسار ده

    selected_inv = st.selectbox("3️⃣ Select Building", inv_files)
    selected_lay = st.selectbox("4️⃣ Select Layout", lay_files)
    selected_rep = st.selectbox("5️⃣ Select Representative", rep_files)

    if st.button("🚀 Generate PDF Offer"):
        # حل مشكلة NoneType: التأكد أن المستخدم اختار ملفات فعلاً
        if not (unit_code and selected_inv and selected_lay and selected_rep):
            st.error("⚠️ من فضلك تأكد من ملء جميع البيانات واختيار الصور!")
        else:
            try:
                original_price = float(price_input.replace(',', ''))
                discount_amount = original_price * 0.10
                p_total = original_price - discount_amount

                doc = fitz.open()

                # دمج الصفحات
                for folder, file in [(inv_path, selected_inv), (lay_path, selected_lay), (rep_path, selected_rep)]:
                    full_path = os.path.join(folder, file)
                    temp_doc = fitz.open(full_path)
                    if file.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # صفحة الأسعار (مختصرة)
                page = doc.new_page()
                page.insert_text((72, 70), f"Unit: {unit_code}", fontsize=20)
                page.insert_text((72, 120), f"Price: {p_total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                pdf_bytes = doc.write()
                st.success("✅ Ready!")
                st.download_button("📥 Download", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
