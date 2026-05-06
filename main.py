import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
import fitz  # PyMuPDF
import os

# --- 1. الإعدادات الأساسية للهوية ---
st.set_page_config(layout="wide", page_title="Tharaa Town - Wujood Project")

# روابط البيانات (Google Sheets)
PROJECT_DATA_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1905007491&single=true&output=csv"
USERS_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSp_VYSbi9RXan_i9IgmbIz6e3kPaifFMpnHdJBvgZ7O-lnw5GrD2tkd1oNnrQt2gPHh4MF7O6Y7NeC/pub?gid=1771432371&single=true&output=csv"

ADMIN_EMAIL = "mo50504172@gmail.com"

# --- 2. وظائف جلب البيانات (مع التحديث التلقائي) ---
@st.cache_data(ttl=10) # تحديث كل 10 ثوانٍ
def load_authorized_users():
    try:
        users_df = pd.read_csv(USERS_AUTH_URL)
        # جلب العمود الأول الذي يحتوي على الإيميلات وتنظيف البيانات
        return users_df.iloc[:, 0].astype(str).str.lower().str.strip().tolist()
    except Exception as e:
        return [ADMIN_EMAIL]

@st.cache_data(ttl=10)
def load_project_units():
    try:
        return pd.read_csv(PROJECT_DATA_URL)
    except Exception as e:
        st.error(f"Error loading units: {e}")
        return pd.DataFrame()

# --- 3. نظام بوابة الدخول (Gatekeeper) ---
def check_access():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Tharaa Town - Wujood Sales System")
        st.info("يرجى تسجيل الدخول للوصول إلى بيانات المشروع وصانع العروض.")
        
        allowed_emails = load_authorized_users()

        col1, col2 = st.columns(2)
        with col1:
            email_input = st.text_input("Enter Email:").lower().strip()
        with col2:
            pin_input = st.text_input("Access PIN:", type="password")
        
        if st.button("Login"):
            # التحقق من الإيميل (من الشيت أو إيميل المدير) والـ PIN
            if (email_input in allowed_emails or email_input == ADMIN_EMAIL) and pin_input == "2026":
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_input
                st.rerun()
            else:
                st.error("🚫 عذراً، الإيميل غير مصرح له أو الـ PIN غير صحيح.")
        return False
    return True

# --- 4. تشغيل البرنامج الرئيسي ---
if check_access():
    
    # القائمة الجانبية (Sidebar)
    st.sidebar.image("https://tharaatown.com/wp-content/uploads/2023/10/Tharaa-Town-Logo.png", width=150)
    st.sidebar.write(f"Logged in: **{st.session_state['user_email']}**")
    
    # لوحة المدير
    if st.session_state['user_email'] == ADMIN_EMAIL:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Admin Tools")
        st.sidebar.write("إدارة المستخدمين تتم حالياً عبر Google Sheet.")

    # --- القسم الأول: الماستر بلان التفاعلية ---
    st.title("🎯 Wujood Interactive Masterplan")
    
    df_raw = load_project_units()
    if not df_raw.empty:
        try:
            # فلترة الوحدات المتاحة
            df_available = df_raw[df_raw['Status'] == 'Available'].copy()
            df_available['X'] = pd.to_numeric(df_available['X'], errors='coerce')
            df_available['Y'] = pd.to_numeric(df_available['Y'], errors='coerce')
            df_available = df_available.dropna(subset=['X', 'Y'])
            
            # تجميع الوحدات بنفس الموقع للـ Hover
            df_grouped = df_available.groupby(['X', 'Y']).apply(lambda x: x.to_dict('records')).reset_index(name='units')
            
            hover_labels = []
            for _, row in df_grouped.iterrows():
                label = "<b>Units Available:</b><br>"
                for u in row['units']:
                    label += f"🏠 {u.get('Unit Code')} | 📏 {u.get('Area')}m | 💰 {u.get('Price')} EGP<br>"
                hover_labels.append(label)

            # عرض الصورة والخريطة
            if os.path.exists("Master Plan.jpeg"):
                img = Image.open("Master Plan.jpeg")
                fig = px.imshow(img)
                fig.add_scatter(
                    x=df_grouped['X'], y=df_grouped['Y'], mode='markers',
                    marker=dict(size=20, color='red', opacity=0.8, line=dict(width=2, color='white')),
                    hovertext=hover_labels, hoverinfo="text"
                )
                fig.update_layout(dragmode='pan', width=1100, height=800, margin=dict(l=0,r=0,t=20,b=0), showlegend=False)
                fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ ملف Master Plan.jpeg غير موجود في المجلد.")
        except Exception as e:
            st.error(f"Error displaying Map: {e}")

    # --- القسم الثاني: صانع العروض (Offer Builder) ---
    st.sidebar.markdown("---")
    st.sidebar.header("📄 Professional Offer Builder")
    
    target_unit = st.sidebar.text_input("1️⃣ Unit Code").upper()
    raw_price = st.sidebar.text_input("2️⃣ List Price", value="0")

    if st.sidebar.button("🚀 Generate PDF Offer"):
        if not target_unit or raw_price == "0":
            st.sidebar.error("يرجى إدخال الكود والسعر.")
        else:
            try:
                # عمليات الحساب
                price_val = float("".join(filter(str.isdigit, raw_price)))
                discount_val = price_val * 0.10
                final_price = price_val - discount_val

                # إنشاء الملف (هنا تضع منطق PyMuPDF الخاص بك)
                st.sidebar.success(f"تم حساب العرض لـ {target_unit}")
                st.sidebar.write(f"Net Price (10% Off): **{final_price:,.0f} EGP**")
                # ملاحظة: يمكنك إضافة دالة doc.save() هنا لتحميل الملف
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
