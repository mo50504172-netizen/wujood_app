import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# رابط البيانات من جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: return pd.read_csv(CSV_URL)
    except: return pd.DataFrame()

# --- 2. الماستر بلان التفاعلية ---
st.title("🎯 Wujood Interactive Masterplan")
df_all = load_data()
if not df_all.empty:
    try:
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce'); df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')
        
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            fig.add_scatter(x=df_grouped['X'], y=df_grouped['Y'], mode='markers', marker=dict(size=20, color='red', opacity=0.8))
            fig.update_layout(dragmode='pan', width=1200, height=850, margin=dict(l=0, r=0, t=40, b=0))
            fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e: st.error(f"Masterplan Error: {e}")

# --- 3. صانع العروض (Professional Offer Builder) ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    st.divider()

    unit_code = st.text_input("1️⃣ Unit Code").upper()
    price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

    # تحديد أسماء المجلدات بدقة كما في هيكل ملفاتك
    static_folder = "static_images"
    inventory_folder = "Inventory"
    layouts_folder = "layouts"
    team_folder = "last_Images" # المجلد المسؤول عن أسماء التيم

    # جلب ملفات الوحدات والتقسيمات
    inv_files = sorted([f for f in os.listdir(inventory_folder) if not f.startswith('.')]) if os.path.exists(inventory_folder) else []
    lay_files = sorted([f for f in os.listdir(layouts_folder) if not f.startswith('.')]) if os.path.exists(layouts_folder) else []
    
    selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["Folder Not Found"])
    selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["Folder Not Found"])

    # --- معالجة قائمة Team Osama (الأسماء من مجلد last_Images) ---
    team_mapping = {}
    if os.path.exists(team_folder):
        # قراءة الملفات مباشرة من مجلد last_Images
        raw_team_files = sorted([f for f in os.listdir(team_folder) if not f.startswith('.')])
        for f in raw_team_files:
            display_name = os.path.splitext(f)[0] # يحذف .jpeg ليظهر الاسم فقط
            team_mapping[display_name] = f
    
    # القائمة الآن ستعرض الأسماء (Basmala, Farag, etc.) بدلاً من الأرقام
    selected_member = st.selectbox("5️⃣ Team Osama", list(team_mapping.keys()) if team_mapping else ["Check last_Images Folder"])

    st.divider()

    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_raw == "0":
            st.error("أدخل كود الوحدة والسعر")
        else:
            try:
                # الحسابات المالية (خصم 10%)
                clean_p = "".join(filter(str.isdigit, price_raw))
                original_p = float(clean_p)
                discount = original_p * 0.10
                net_price = original_p - discount

                # أنظمة السداد
                p1 = {"dp": net_price*0.10, "bull": net_price*0.10, "inst": (net_price*0.80)/39}
                p2 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "inst": (net_price*0.90)/31}
                p3 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "bull": net_price*0.15, "inst": (net_price*0.75)/38}

                doc = fitz.open()

                # الترتيب 1: الصور الثابتة
                if os.path.exists(static_folder):
                    s_files = sorted([f for f in os.listdir(static_folder) if not f.startswith('.')])
                    for s in s_files:
                        img_doc = fitz.open(os.path.join(static_folder, s))
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                # الترتيب 2: صورة المبنى
                if selected_inv != "Folder Not Found":
                    inv_img = fitz.open(os.path.join(inventory_folder, selected_inv))
                    doc.insert_pdf(fitz.open("pdf", inv_img.convert_to_pdf()))

                # الترتيب 3: صفحة السداد
                page = doc.new_page()
                page.insert_text((72, 60), "Wujood Project - Payment Plan", fontsize=22)
                page.insert_text((72, 110), f"Unit: {unit_code} | Original: {original_p:,.0f} EGP", fontsize=12)
                page.insert_text((72, 135), f"Discount 10%: -{discount:,.0f} | Final: {net_price:,.0f} EGP", fontsize=14, color=(0, 0.4, 0))
                
                y_pos = 200
                plans = [
                    ("Option 1 (10% DP):", f"DP: {p1['dp']:,.0f} | Bullet: {p1['bull']:,.0f} | 39 Quarters: {p1['inst']:,.0f}"),
                    ("Option 2 (5% + 5%):", f"DP1: {p2['dp1']:,.0f} | DP2: {p2['dp2']:,.0f} | 31 Quarters: {p2['inst']:,.0f}"),
                    ("Option 3 (Premium):", f"DP1: {p3['dp1']:,.0f} | Bullet: {p3['bull']:,.0f} | 38 Quarters: {p3['inst']:,.0f}")
                ]
                for title, text in plans:
                    page.insert_text((72, y_pos), title, fontsize=14, color=(0, 0.2, 0.6))
                    page.insert_text((80, y_pos+20), text, fontsize=10); y_pos += 75

                # الترتيب 4: صورة التقسيمة
                if selected_lay != "Folder Not Found":
                    lay_img = fitz.open(os.path.join(layouts_folder, selected_lay))
                    doc.insert_pdf(fitz.open("pdf", lay_img.convert_to_pdf()))

                # الترتيب 5: صورة التيم المختارة
                if selected_member in team_mapping:
                    member_file = team_mapping[selected_member]
                    member_img = fitz.open(os.path.join(team_folder, member_file))
                    doc.insert_pdf(fitz.open("pdf", member_img.convert_to_pdf()))

                # التحميل
                pdf_bytes = doc.write()
                st.sidebar.success(f"✅ Created: {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
            except Exception as e: st.sidebar.error(f"Error: {e}")
