import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# روابط البيانات
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# دالة فحص المجلدات (الحل الجذري للمسارات)
def get_valid_files(folder_name):
    # يبحث عن المجلد بكل الاحتمالات (كبير، صغير، أول حرف كبير)
    options = [folder_name, folder_name.lower(), folder_name.capitalize(), folder_name.replace("_", " "), folder_name.replace(" ", "_")]
    for opt in options:
        if os.path.exists(opt) and os.path.isdir(opt):
            files = sorted([f for f in os.listdir(opt) if not f.startswith('.')])
            if files:
                return opt, files
    return None, []

# --- 2. الجزء الأونلاين (الماستر بلان) في الصفحة الرئيسية ---
st.title("🎯 Wujood Interactive Masterplan")

df_all = load_data()
if not df_all.empty:
    try:
        # معالجة البيانات
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        # تجميع الوحدات
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

        # عرض الخريطة
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=20, color='red', symbol='circle', opacity=0.8),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"إجمالي الوحدات المتاحة: {len(df)}")
        else:
            st.warning("ملف 'Master Plan.jpeg' غير موجود في المجلد الرئيسي.")
    except Exception as e:
        st.error(f"خطأ في معالجة الماستر بلان: {e}")

# --- 3. الجزء الأوفلاين (صانع العروض) في الشريط الجانبي ---
with st.sidebar:
    st.header("📄 Offer Builder (Steps)")
    st.subheader("قم بملء البيانات بالترتيب:")

    # 1 & 2: مدخلات نصية
    unit_code = st.text_input("1️⃣ Enter Full Unit Code", placeholder="W-101").upper()
    price_raw = st.text_input("2️⃣ Enter Price (EGP)", value="0")

    # جلب الملفات من المجلدات مع التأكد من وجودها
    inv_path, inv_files = get_valid_files("Inventory")
    lay_path, lay_files = get_valid_files("layouts")
    rep_path, rep_files = get_valid_files("last_images") # سيبحث عن Last_Images أيضاً تلقائياً

    # 3 & 4 & 5: القوائم المنسدلة
    selected_inv = st.selectbox("3️⃣ Select Building Image", inv_files if inv_files else ["No files found"])
    selected_layout = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["No files found"])
    selected_rep = st.selectbox("5️⃣ Select Sales Representative", rep_files if rep_files else ["No files found"])

    if st.button("🚀 Generate PDF Offer"):
        # فحص الحماية من الـ NoneType والبيانات الناقصة
        if not unit_code or price_raw == "0":
            st.error("⚠️ يرجى إدخال كود الوحدة والسعر.")
        elif not (inv_path and lay_path and rep_path):
            st.error(f"⚠️ أحد المجلدات مفقود! Inventory: {bool(inv_path)}, Layouts: {bool(lay_path)}, Reps: {bool(rep_path)}")
        elif "No files found" in [selected_inv, selected_layout, selected_rep]:
            st.error("⚠️ يرجى التأكد من اختيار ملفات صحيحة من القوائم.")
        else:
            try:
                # الحسابات
                original_price = float(price_raw.replace(',', ''))
                discount_amount = original_price * 0.10
                p_total = original_price - discount_amount

                p1_dp, p1_bullet, p1_inst = p_total * 0.10, p_total * 0.10, (p_total * 0.80) / 39
                p2_dp1, p2_dp2, p2_inst = p_total * 0.05, p_total * 0.05, (p_total * 0.90) / 31
                p3_dp1, p3_dp2, p3_bullet, p3_inst = p_total * 0.05, p_total * 0.05, p_total * 0.15, (p_total * 0.75) / 38

                # بناء الـ PDF
                doc = fitz.open()

                # إضافة الصور الثابتة (اختياري)
                static_dir = "static_images"
                if os.path.exists(static_dir):
                    for img_n in sorted(os.listdir(static_dir)):
                        if not img_n.startswith('.'):
                            img_doc = fitz.open(os.path.join(static_dir, img_n))
                            doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                # إضافة الصفحات المختارة من المجلدات
                for folder, file in [(inv_path, selected_inv), (lay_path, selected_layout), (rep_path, selected_rep)]:
                    full_p = os.path.join(folder, file)
                    tmp_doc = fitz.open(full_p)
                    if file.lower().endswith('.pdf'): doc.insert_pdf(tmp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", tmp_doc.convert_to_pdf()))

                # صفحة الأسعار
                page = doc.new_page()
                page.insert_text((72, 50), "Project: Wujood", fontsize=24, color=(0,0,0))
                page.insert_text((72, 80), f"Unit: {unit_code} | Layout: {os.path.splitext(selected_layout)[0]}", fontsize=15)
                page.insert_text((72, 115), f"Original Price: {original_price:,.0f} EGP", fontsize=14)
                page.insert_text((72, 160), f"Final Price: {p_total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                y = 200
                options = [
                    ("Option 1 (10% DP):", f"- DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bullet:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                    ("Option 2 (5% + 5%):", f"- DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                    ("Option 3 (Premium):", f"- DP1: {p3_dp1:,.0f} | DP2 (3m): {p3_dp2:,.0f} | Bullet: {p3_bullet:,.0f} | 38 Quarters: {p3_inst:,.0f}")
                ]
                for title, detail in options:
                    page.insert_text((72, y), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), detail, fontsize=11)
                    y += 70

                pdf_out = doc.write()
                st.sidebar.success(f"✅ Created: {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_out, f"Offer_{unit_code}.pdf", "application/pdf")
            except Exception as e:
                st.sidebar.error(f"خطأ تقني: {e}")
