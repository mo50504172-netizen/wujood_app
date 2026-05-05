import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Wujood Interactive System")

# روابط البيانات من جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try:
        return pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return pd.DataFrame()

# --- دالة البحث الذكي عن المجلدات (لحل مشكلة Reps: False) ---
def find_folder_and_files(keywords):
    """تبحث عن مجلد يحتوي على الكلمات الدليلية وتجلب ملفاته"""
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

# --- 2. الجزء الرئيسي: الماستر بلان (Online) ---
st.title("🎯 Wujood Interactive Masterplan")

df_all = load_data()
if not df_all.empty:
    try:
        # تجهيز البيانات
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

        # عرض الماستر بلان
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                            marker=dict(size=20, color='red', opacity=0.8),
                            hovertext=hover_labels, hoverinfo="text")
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"✅ إجمالي الوحدات المتاحة حالياً: {len(df)}")
        else:
            st.warning("⚠️ ملف 'Master Plan.jpeg' غير موجود في المسار الرئيسي.")
    except Exception as e:
        st.error(f"Masterplan Error: {e}")

# --- 3. الشريط الجانبي: صانع العروض (Steps) ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    st.divider()

    # الخطوة 1 و 2
    unit_code = st.text_input("1️⃣ Unit Code (e.g. W-101)").upper()
    price_str = st.text_input("2️⃣ Unit Price (EGP)", value="0")

    # البحث التلقائي عن المجلدات (أهم جزء لضمان ظهور الملفات)
    inv_path, inv_files = find_folder_and_files(["inventory", "inv"])
    lay_path, lay_files = find_folder_and_files(["layout"])
    rep_path, rep_files = find_folder_and_files(["last", "image", "rep", "team"])

    # الخطوات 3، 4، 5 (القوائم المنسدلة)
    selected_inv = st.selectbox("3️⃣ Select Building", inv_files if inv_files else ["Folder Not Found"])
    selected_lay = st.selectbox("4️⃣ Select Layout", lay_files if lay_files else ["Folder Not Found"])
    selected_rep = st.selectbox("5️⃣ Select Representative", rep_files if rep_files else ["Folder Not Found"])

    st.divider()

    if st.button("🚀 Generate PDF Offer"):
        # التحقق من البيانات
        if not unit_code or price_str == "0":
            st.error("❌ ادخل كود الوحدة والسعر أولاً")
        elif not (inv_path and lay_path and rep_path):
            st.error(f"❌ مفقود: Inv:{bool(inv_path)}, Lay:{bool(lay_path)}, Reps:{bool(rep_path)}")
        elif "Folder Not Found" in [selected_inv, selected_lay, selected_rep]:
            st.error("❌ تأكد من وجود ملفات داخل المجلدات المرفوعة")
        else:
            try:
                # الحسابات المالية
                price = float(price_str.replace(',', ''))
                discount = price * 0.10
                total = price - discount

                # الأنظمة
                p1 = {"dp": total*0.10, "bull": total*0.10, "inst": (total*0.80)/39}
                p2 = {"dp1": total*0.05, "dp2": total*0.05, "inst": (total*0.90)/31}
                p3 = {"dp1": total*0.05, "dp2": total*0.05, "bull": total*0.15, "inst": (total*0.75)/38}

                # إنشاء الـ PDF
                doc = fitz.open()

                # دمج الصفحات المختارة
                for fld, fl in [(inv_path, selected_inv), (lay_path, selected_lay), (rep_path, selected_rep)]:
                    full_p = os.path.join(fld, fl)
                    temp_pdf = fitz.open(full_p)
                    if fl.lower().endswith('.pdf'):
                        doc.insert_pdf(temp_pdf)
                    else:
                        doc.insert_pdf(fitz.open("pdf", temp_pdf.convert_to_pdf()))

                # صفحة بيانات الأسعار
                page = doc.new_page()
                page.insert_text((72, 60), "Wujood Project - Offer Details", fontsize=22, color=(0,0,0))
                page.insert_text((72, 100), f"Unit: {unit_code} | Area: {os.path.splitext(selected_lay)[0]}", fontsize=14)
                page.insert_text((72, 140), f"Price After 10% Discount: {total:,.0f} EGP", fontsize=18, color=(0, 0.4, 0))

                y = 200
                plans = [
                    ("Plan 1 (10% DP):", f"DP: {p1['dp']:,.0f} | 3.5Y Bullet: {p1['bull']:,.0f} | 39 Quarters: {p1['inst']:,.0f}"),
                    ("Plan 2 (5% + 5%):", f"DP1: {p2['dp1']:,.0f} | DP2: {p2['dp2']:,.0f} | 31 Quarters: {p2['inst']:,.0f}"),
                    ("Plan 3 (Premium):", f"DP1: {p3['dp1']:,.0f} | DP2 (3m): {p3['dp2']:,.0f} | Bullet: {p3['bull']:,.0f} | 38 Quarters: {p3['inst']:,.0f}")
                ]
                for title, txt in plans:
                    page.insert_text((72, y), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y+20), txt, fontsize=10)
                    y += 70

                # زر التحميل
                pdf_bytes = doc.write()
                st.sidebar.success(f"✅ تم إنشاء عرض {unit_code}")
                st.sidebar.download_button("📥 اضغط هنا لتحميل الملف", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")

            except Exception as e:
                st.sidebar.error(f"خطأ: {e}")
