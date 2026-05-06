import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 0. نظام حماية الوصول (Email Whitelist) ---
# أضف هنا جميع الإيميلات المسموح لها فقط بفتح التطبيق
ALLOWED_EMAILS = [
    "m.osama@tharaatown.com", 
    "basmala@gmail.com",
    "youssef@gmail.com",
    "farag@gmail.com",
    "nady@gmail.com",
    "gamal@gmail.com",
    "salma@gmail.com"
]

# التحقق من هوية المستخدم (يعمل عند رفع التطبيق على Streamlit Cloud)
if st.user.email not in ALLOWED_EMAILS:
    st.error("🚫 عذراً، هذا التطبيق خاص بموظفي Tharaa Town فقط. ليس لديك صلاحية للوصول.")
    st.info("يرجى التأكد من تسجيل الدخول بحساب جوجل المعتمد والمضاف في القائمة.")
    st.stop() # إيقاف تنفيذ الكود تماماً لمنع أي اختراق

# --- 1. إعدادات الصفحة ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# رابط بيانات الوحدات من جوجل شيت
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"

@st.cache_data(ttl=5)
def load_data():
    try: 
        return pd.read_csv(CSV_URL)
    except: 
        return pd.DataFrame()

# --- 2. الماستر بلان التفاعلية ---
st.title("🎯 Wujood Interactive Masterplan")
df_all = load_data()

if not df_all.empty:
    try:
        # فلترة الوحدات المتاحة فقط وتحويل الإحداثيات لأرقام
        df = df_all[df_all['Status'] == 'Available'].copy()
        df['X'] = pd.to_numeric(df['X'], errors='coerce')
        df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
        df = df.dropna(subset=['X', 'Y'])
        
        # تجميع الوحدات التي تشترك في نفس النقطة (X, Y)
        df_grouped = df.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')
        
        # تجهيز نصوص الـ Hover لتظهر بشكل احترافي
        hover_texts = []
        for _, row in df_grouped.iterrows():
            label = "<b>Available Units:</b><br>"
            for unit in row['units']:
                price = unit.get('Price', 'N/A')
                label += f"🏠 {unit.get('Unit Code', 'N/A')} | 💰 {price} | 📏 {unit.get('Area', 'N/A')}m²<br>"
            hover_texts.append(label)

        # رسم الخريطة إذا كانت الصورة موجودة
        if os.path.exists("Master Plan.jpeg"):
            img = Image.open("Master Plan.jpeg") 
            fig = px.imshow(img)
            
            # إضافة النقاط الحمراء التفاعلية
            fig.add_scatter(
                x=df_grouped['X'], 
                y=df_grouped['Y'], 
                mode='markers', 
                marker=dict(size=18, color='red', opacity=0.7),
                hovertext=hover_texts,
                hoverinfo="text",
                name=""
            )
            
            fig.update_layout(
                dragmode='pan', 
                width=1200, 
                height=850, 
                margin=dict(l=0, r=0, t=40, b=0),
                showlegend=False
            )
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e: 
        st.error(f"Masterplan Error: {e}")

# --- 3. صانع العروض (Offer Builder) في الشريط الجانبي ---
with st.sidebar:
    st.header("📄 Professional Offer Builder")
    # عرض إيميل المستخدم الحالي للتأكد من هويته
    st.write(f"Logged in as: `{st.user.email}`") 
    st.divider()

    unit_code = st.text_input("1️⃣ Unit Code").upper()
    price_raw = st.text_input("2️⃣ Original Price (EGP)", value="0")

    # تعريف مسارات الفولدرات
    static_folder = "static_images"
    inventory_folder = "Inventory"
    layouts_folder = "layouts"
    team_folder = "last_Images"

    # جلب قوائم الملفات من الفولدرات
    inv_files = sorted([f for f in os.listdir(inventory_folder) if not f.startswith('.')]) if os.path.exists(inventory_folder) else []
    lay_files = sorted([f for f in os.listdir(layouts_folder) if not f.startswith('.')]) if os.path.exists(layouts_folder) else []
    
    selected_inv = st.selectbox("3️⃣ Select Building (Inventory)", inv_files if inv_files else ["Folder Not Found"])
    selected_lay = st.selectbox("4️⃣ Select Unit Layout", lay_files if lay_files else ["Folder Not Found"])

    # تجهيز قائمة أعضاء الفريق
    team_mapping = {}
    if os.path.exists(team_folder):
        raw_team_files = sorted([f for f in os.listdir(team_folder) if not f.startswith('.')])
        for f in raw_team_files:
            display_name = os.path.splitext(f)[0]
            team_mapping[display_name] = f
    
    selected_member = st.selectbox("5️⃣ Team Osama", list(team_mapping.keys()) if team_mapping else ["Check last_Images"])

    st.divider()

    # زر إنشاء ملف الـ PDF
    if st.button("🚀 Generate PDF Offer"):
        if not unit_code or price_raw == "0":
            st.error("أدخل كود الوحدة والسعر أولاً")
        else:
            try:
                # العمليات الحسابية للعرض المالي
                clean_p = "".join(filter(str.isdigit, price_raw))
                original_p = float(clean_p)
                discount = original_p * 0.10
                net_price = original_p - discount

                # أنظمة السداد
                p1 = {"dp": net_price*0.10, "bull": net_price*0.10, "inst": (net_price*0.80)/39}
                p2 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "inst": (net_price*0.90)/31}
                p3 = {"dp1": net_price*0.05, "dp2": net_price*0.05, "bull": net_price*0.15, "inst": (net_price*0.75)/38}

                # إنشاء وثيقة PDF جديدة
                doc = fitz.open()

                # إضافة الصور الثابتة (Static Images)
                if os.path.exists(static_folder):
                    s_files = sorted([f for f in os.listdir(static_folder) if not f.startswith('.')])
                    for s in s_files:
                        img_path = os.path.join(static_folder, s)
                        img_doc = fitz.open(img_path)
                        doc.insert_pdf(fitz.open("pdf", img_doc.convert_to_pdf()))

                # إضافة صورة المبنى (Inventory)
                if selected_inv != "Folder Not Found":
                    inv_img = fitz.open(os.path.join(inventory_folder, selected_inv))
                    doc.insert_pdf(fitz.open("pdf", inv_img.convert_to_pdf()))

                # إنشاء صفحة البيانات المالية
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
                    page.insert_text((80, y_pos+20), text, fontsize=10)
                    y_pos += 75

                # إضافة مسقط الوحدة (Layout)
                if selected_lay != "Folder Not Found":
                    lay_img = fitz.open(os.path.join(layouts_folder, selected_lay))
                    doc.insert_pdf(fitz.open("pdf", lay_img.convert_to_pdf()))

                # إضافة بيانات التيم (Team Member Image)
                if selected_member in team_mapping:
                    member_img = fitz.open(os.path.join(team_folder, team_mapping[selected_member]))
                    doc.insert_pdf(fitz.open("pdf", member_img.convert_to_pdf()))

                # استخراج ملف PDF النهائي
                pdf_bytes = doc.write()
                st.sidebar.success(f"✅ Offer Ready for {unit_code}")
                st.sidebar.download_button("📥 Download PDF Offer", pdf_bytes, f"Offer_{unit_code}.pdf", "application/pdf")
            except Exception as e: 
                st.sidebar.error(f"Error generating PDF: {e}")
