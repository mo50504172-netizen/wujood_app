import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# --- 1. إعدادات الصفحة ---
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

# دالة البحث الذكي عن المجلدات (لضمان إيجاد الصور بصرف النظر عن حالة الأحرف)
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

# --- 2. الجزء الأونلاين: الماستر بلان (الصفحة الرئيسية) ---
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
            label = "<b>Units Available:</b><br>"
            for unit in row['units']:
                try:
                    p_val = float(str(unit.get('Price', 0)).replace(',', ''))
                    p_str = f"{p_val:,.0f} EGP"
                except: p_str = "N/A"
                label += f"• {unit.get('Unit Code', 'N/A')} | {p_str} | {unit.get('Area', 'N/A')}m²<br>"
            hover_labels.append(label)

        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=20, color='red', opacity=0.8),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"إجمالي الوحدات المتاحة حالياً: {len(df)}")
    except Exception as e:
        st.error(f"Masterplan Error: {e}")

# --- 3. الجزء الأوفلاين: صانع العروض (الشريط الجانبي) ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    st.divider()

    unit_code = st.text_input("1️⃣ Unit Code (e.g. W-101)").upper()
    price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

    # البحث عن المجلدات
    static_path, static_files = find_folder_and_files(["static"])
    inv_path, inv_files = find_folder_and_files(["inventory"])
    lay_path, lay_files = find_folder_and_files(["layout"])
    rep_path, rep_files = find_folder_and_files(["last", "image", "rep", "team"])

    selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["No Files Found"])
    selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["No Files Found"])
    selected_rep = st.selectbox("5️⃣ Select Representative", rep_files if rep_files else ["No Files Found"])

    st.divider()

    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_raw == "0":
            st.error("❌ يرجى إدخال كود الوحدة والسعر")
        elif "No Files Found" in [selected_inv, selected_lay, selected_rep]:
            st.error("❌ تأكد من وجود ملفات داخل المجلدات المرفوعة")
        else:
            try:
                # --- معالجة الحسابات والخصم ---
                # تنظيف مدخلات السعر من أي رموز غير رقمية
                clean_price_str = "".join(filter(str.isdigit, price_raw))
                original_price = float(clean_price_str)
                
                # تطبيق خصم 10%
                discount_val = original_price * 0.10
                p_total = original_price - discount_val

                # حساب أنظمة السداد بناءً على السعر بعد الخصم
                p1_dp, p1_bull, p1_inst = p_total*0.10, p_total*0.10, (p_total*0.80)/39
                p2_dp1, p2_dp2, p2_inst = p_total*0.05, p_total*0.05, (p_total*0.90)/31
                p3_dp1, p3_dp2, p3_bull, p3_inst = p_total*0.05, p_total*0.05, p_total*0.15, (p_total*0.75)/38

                # إنشاء الـ PDF
                doc = fitz.open()

                # الترتيب 1: الصور الثابتة (static_images)
                if static_path:
                    for s_file in static_files:
                        full_s = os.path.join(static_path, s_file)
                        s_pdf = fitz.open(full_s)
                        if s_file.lower().endswith('.pdf'): doc.insert_pdf(s_pdf)
                        else: doc.insert_pdf(fitz.open("pdf", s_pdf.convert_to_pdf()))

                # الترتيب 2: صورة المبنى (Inventory)
                if inv_path:
                    full_inv = os.path.join(inv_path, selected_inv)
                    inv_pdf = fitz.open(full_inv)
                    if selected_inv.lower().endswith('.pdf'): doc.insert_pdf(inv_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", inv_pdf.convert_to_pdf()))

                # الترتيب 3: صفحة تفاصيل السعر والخصم والأقساط
                page = doc.new_page()
                page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22, color=(0,0,0))
                page.insert_text((72, 100), f"Unit Code: {unit_code} | Layout: {os.path.splitext(selected_lay)[0]}", fontsize=14)
                
                # عرض تفاصيل السعر بوضوح
                page.insert_text((72, 140), f"Original Price: {original_price:,.0f} EGP", fontsize=12)
                page.insert_text((72, 160), f"Special Discount (10%): -{discount_val:,.0f} EGP", fontsize=12, color=(0.8, 0, 0))
                page.insert_text((72, 190), f"Final Price: {p_total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                y = 240
                plans = [
                    ("Option 1 (10% DP):", f"DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bull:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                    ("Option 2 (5% + 5%):", f"DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                    ("Option 3 (Premium Plan):", f"DP1: {p3_dp1:,.0f} | DP2 (3m): {p3_dp2:,.0f} | Bullet: {p3_bull:,.0f} | 38 Quarters: {p3_inst:,.0f}")
                ]
                for title, detail in plans:
                    page.insert_text((72, y), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), detail, fontsize=10)
                    y += 75

                # الترتيب 4: صورة التقسيمة (Layouts)
                if lay_path:
                    full_lay = os.path.join(lay_path, selected_lay)
                    lay_pdf = fitz.open(full_lay)
                    if selected_lay.lower().endswith('.pdf'): doc.insert_pdf(lay_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", lay_pdf.convert_to_pdf()))

                # الترتيب 5: صورة المندوب (Last_Images)
                if rep_path:
                    full_rep = os.path.join(rep_path, selected_rep)
                    rep_pdf = fitz.open(full_rep)
                    if selected_rep.lower().endswith('.pdf'): doc.insert_pdf(rep_pdf)
                    else: doc.insert_pdf(fitz.open("pdf", rep_pdf.convert_to_pdf()))

                # تصدير الملف
                pdf_output = doc.write()
                st.sidebar.success(f"✅ Created: {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_output, f"Offer_{unit_code}.pdf", "application/pdf")

            except Exception as e:
                st.sidebar.error(f"خطأ تقني: {e}")
