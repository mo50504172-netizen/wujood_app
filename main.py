import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة الأساسية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# رابط البيانات من جوجل شيت (تأكد من أنه متاح للجميع بصيغة CSV)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# دالة للبحث عن المجلدات والملفات (تجاهل الملفات المخفية)
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

# --- 2. الواجهة الأمامية: الماستر بلان (Masterplan) ---
st.title("🎯 Wujood Interactive Masterplan")

df_all = load_data()
if not df_all.empty:
    try:
        # فلترة الوحدات المتاحة
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])

        # تجميع الوحدات حسب الإحداثيات
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

        # عرض الخريطة التفاعلية
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=20, color='red', opacity=0.8),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("ملف 'Master Plan.jpeg' غير موجود في المجلد الرئيسي.")
    except Exception as e:
        st.error(f"Masterplan Error: {e}")

# --- 3. الشريط الجانبي: صانع العروض (Offer Builder) ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    st.divider()

    # مدخلات البيانات
    unit_code = st.text_input("1️⃣ Unit Code (e.g. W-101)").upper()
    price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

    # تحديد المجلدات
    static_path, static_files = find_folder_and_files(["static"])
    inv_path, inv_files = find_folder_and_files(["inventory"])
    lay_path, lay_files = find_folder_and_files(["layout"])
    rep_path, rep_files = find_folder_and_files(["last", "images"])

    # القوائم المنسدلة
    selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["No Files Found"])
    selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["No Files Found"])

    # قائمة Team Osama (تحويل أسماء الملفات لأسماء عرض)
    team_mapping = {}
    if rep_files:
        for f in rep_files:
            display_name = os.path.splitext(f)[0] # يأخذ الاسم بدون الامتداد
            team_mapping[display_name] = f
    
    selected_member = st.selectbox("5️⃣ Team Osama", list(team_mapping.keys()) if team_mapping else ["No Team Found"])

    st.divider()

    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_raw == "0":
            st.error("يرجى إدخال البيانات المطلوبة.")
        else:
            try:
                # --- الحسابات المالية ---
                clean_price_str = "".join(filter(str.isdigit, price_raw))
                original_price = float(clean_price_str)
                
                # خصم الـ 10%
                discount_amount = original_price * 0.10
                final_price = original_price - discount_amount

                # أنظمة السداد (على السعر النهائي)
                p1_dp, p1_bull, p1_inst = final_price*0.10, final_price*0.10, (final_price*0.80)/39
                p2_dp1, p2_dp2, p2_inst = final_price*0.05, final_price*0.05, (final_price*0.90)/31
                p3_dp1, p3_dp2, p3_bull, p3_inst = final_price*0.05, final_price*0.05, final_price*0.15, (final_price*0.75)/38

                # إنشاء مستند PDF
                doc = fitz.open()

                # الترتيب 1: الصور الثابتة (Static Images)
                if static_path:
                    for s in static_files:
                        img_path = os.path.join(static_path, s)
                        temp_doc = fitz.open(img_path)
                        if s.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                        else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # الترتيب 2: صورة المبنى (Inventory)
                if inv_path and selected_inv != "No Files Found":
                    img_path = os.path.join(inv_path, selected_inv)
                    temp_doc = fitz.open(img_path)
                    if selected_inv.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # الترتيب 3: صفحة تفاصيل الدفع والخصم
                page = doc.new_page()
                page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22, color=(0,0,0))
                page.insert_text((72, 110), f"Unit: {unit_code} | Original Price: {original_price:,.0f} EGP", fontsize=12)
                page.insert_text((72, 135), f"Discount (10%): -{discount_amount:,.0f} EGP", fontsize=12, color=(0.8, 0, 0))
                page.insert_text((72, 165), f"Net Price: {final_price:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                y_pos = 220
                plans = [
                    ("Option 1 (10% DP):", f"DP: {p1_dp:,.0f} | 3.5Y Bullet: {p1_bull:,.0f} | 39 Quarters: {p1_inst:,.0f}"),
                    ("Option 2 (5% + 5%):", f"DP1: {p2_dp1:,.0f} | DP2: {p2_dp2:,.0f} | 31 Quarters: {p2_inst:,.0f}"),
                    ("Option 3 (Premium):", f"DP1: {p3_dp1:,.0f} | DP2 (3m): {p3_dp2:,.0f} | Bullet: {p3_bull:,.0f} | 38 Quarters: {p3_inst:,.0f}")
                ]
                for title, detail in plans:
                    page.insert_text((72, y_pos), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y_pos + 20), detail, fontsize=10)
                    y_pos += 75

                # الترتيب 4: صورة التقسيمة (Layouts)
                if lay_path and selected_lay != "No Files Found":
                    img_path = os.path.join(lay_path, selected_lay)
                    temp_doc = fitz.open(img_path)
                    if selected_lay.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # الترتيب 5: صورة عضو الفريق (Team Osama)
                if rep_path and selected_member in team_mapping:
                    member_file = team_mapping[selected_member]
                    img_path = os.path.join(rep_path, member_file)
                    temp_doc = fitz.open(img_path)
                    if member_file.lower().endswith('.pdf'): doc.insert_pdf(temp_doc)
                    else: doc.insert_pdf(fitz.open("pdf", temp_doc.convert_to_pdf()))

                # حفظ وتنزيل الملف
                pdf_output = doc.write()
                st.sidebar.success(f"✅ Offer Ready: {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_output, f"Offer_{unit_code}.pdf", "application/pdf")

            except Exception as e:
                st.sidebar.error(f"حدث خطأ أثناء إنشاء الملف: {e}")
