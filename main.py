import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# --- 1. إعدادات الصفحة العامة ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# رابط البيانات من جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# دالة البحث الذكي عن المجلدات (لضمان العثور عليها مهما كان اسم المجلد)
def find_folder_and_files(keywords):
    try:
        current_dirs = [d for d in os.listdir(".") if os.path.isdir(d)]
        for folder in current_dirs:
            if any(key.lower() in folder.lower() for key in keywords):
                files = sorted([f for f in os.listdir(folder) if not f.startswith('.')])
                if files:
                    return folder, files
    except:
        pass
    return None, []

# --- 2. الجزء الأونلاين: الماستر بلان (في الصفحة الرئيسية) ---
st.title("🎯 Wujood Interactive Masterplan")

df_all = load_data()
if not df_all.empty:
    try:
        # فلترة الوحدات المتاحة وتجهيز الإحداثيات
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        # تجميع الوحدات في نفس المبنى
        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')

        hover_labels = []
        for _, row in df_grouped.iterrows():
            label = "<b>Units Available:</b><br>"
            for unit in row['units']:
                try:
                    price_val = float(str(unit.get('Price', 0)).replace(',', ''))
                    price_str = f"{price_val:,.0f} EGP"
                except: price_str = "N/A"
                label += f"• {unit.get('Unit Code', 'N/A')} | {price_str} | {unit.get('Area', 'N/A')}m²<br>"
            hover_labels.append(label)

        # تحميل وعرض خريطة المشروع
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=20, color='red', opacity=0.8, symbol='circle'),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"إجمالي الوحدات المتاحة حالياً: {len(df)}")
        else:
            st.warning("⚠️ ملف 'Master Plan.jpeg' مفقود من المجلد الرئيسي.")
    except Exception as e:
        st.error(f"Masterplan Error: {e}")

# --- 3. الجزء الأوفلاين: صانع العروض (في الشريط الجانبي) ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    st.divider()

    # الخطوة 1 و 2: إدخال البيانات
    unit_code = st.text_input("1️⃣ Enter Full Unit Code").upper()
    price_raw = st.text_input("2️⃣ Enter Original Price (EGP)", value="0")

    # البحث عن المجلدات المطلوبة
    static_path, static_files = find_folder_and_files(["static"])
    inv_path, inv_files = find_folder_and_files(["inventory"])
    lay_path, lay_files = find_folder_and_files(["layout"])
    rep_path, rep_files = find_folder_and_files(["last", "image", "rep", "team"])

    # الخطوات 3 و 4 و 5: الاختيارات
    selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["Folder Missing"])
    selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["Folder Missing"])
    selected_rep = st.selectbox("5️⃣ Select Representative", rep_files if rep_files else ["Folder Missing"])

    st.divider()

    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_raw == "0":
            st.error("❌ يرجى إدخال كود الوحدة والسعر أولاً")
        elif "Folder Missing" in [selected_inv, selected_lay, selected_rep]:
            st.error("❌ تأكد من رفع المجلدات (Inventory, layouts, last_images) وبها ملفات")
        else:
            try:
                # الحسابات المالية (خصم 10%)
                original_price = float(price_raw.replace(',', ''))
                discount_amount = original_price * 0.10
                p_total = original_price - discount_amount

                p1_dp, p1_bull, p1_inst = p_total*0.10, p_total*0.10, (p_total*0.80)/39
                p2_dp1, p2_dp2, p2_inst = p_total*0.05, p_total*0.05, (p_total*0.90)/31
                p3_dp1, p3_dp2, p3_bull, p3_inst = p_total*0.05, p_total*0.05, p_total*0.15, (p_total*0.75)/38

                # إنشاء مستند PDF جديد
                doc = fitz.open()

                # --- الترتيب الإجباري المطلوب ---

                # 1. الصور الثابتة (static_images) بالترتيب الأبجدي/الرقمي
                if static_path:
                    for s_file in static_files:
                        full_s = os.path.join(static_path, s_file)
                        s_pdf = fitz.open(full_s)
                        if s_file.lower().endswith('.pdf'): doc.insert_pdf(s_pdf)
                        else: doc.insert_pdf(fitz.open("pdf", s_pdf.convert_to_pdf()))

                # 2. صورة المبنى المختارة (Inventory)
                if inv_path:
                    full_inv = os.path.join(inv_path, selected_inv)
                    inv_pdf = fitz.open(full_inv)
                    if selected_inv.lower().endswith('.pdf'): doc.insert_pdf(inv_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", inv_pdf.convert_to_pdf()))

                # 3. صفحة الـ Payment Plan (التي يتم توليدها بالكود)
                page = doc.new_page()
                page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22, color=(0,0,0))
                page.insert_text((72, 100), f"Unit: {unit_code} | Total Price: {p_total:,.0f} EGP", fontsize=16, color=(0, 0.4, 0))
                
                y = 180
                plans = [
                    ("Option 1 (10% DP):", f"DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bull:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                    ("Option 2 (5% + 5%):", f"DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                    ("Option 3 (Premium):", f"DP1: {p3_dp1:,.0f} | DP2 (3m): {p3_dp2:,.0f} | Bullet: {p3_bull:,.0f} | 38 Quarters: {p3_inst:,.0f}")
                ]
                for title, txt in plans:
                    page.insert_text((72, y), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), txt, fontsize=10)
                    y += 75

                # 4. صورة التقسيمة المختارة (Layouts)
                if lay_path:
                    full_lay = os.path.join(lay_path, selected_lay)
                    lay_pdf = fitz.open(full_lay)
                    if selected_lay.lower().endswith('.pdf'): doc.insert_pdf(lay_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", lay_pdf.convert_to_pdf()))

                # 5. صورة المندوب المختارة (Last_Images)
                if rep_path:
                    full_rep = os.path.join(rep_path, selected_rep)
                    rep_pdf = fitz.open(full_rep)
                    if selected_rep.lower().endswith('.pdf'): doc.insert_pdf(rep_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", rep_pdf.convert_to_pdf()))

                # النتيجة النهائية للتحميل
                pdf_bytes = doc.write()
                st.sidebar.success(f"✅ Ready: {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")

            except Exception as e:
                st.sidebar.error(f"خطأ تقني: {e}")
