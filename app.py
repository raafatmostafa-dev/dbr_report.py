import streamlit as st
import pandas as pd

# 1. إعداد شكل الصفحة في المتصفح
st.set_page_config(page_title="DBR Report", layout="wide")
st.title("📊 نظام دمج تقارير الـ DBR الـ 8")

# الرابط الأساسي للملف
BASE_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=csv&gid="

# 2. قاموس يحتوي على الـ gid لكل شيت فرعي بناءً على الأسماء اللي عندك
SHETS_DICTIONARY = {
    "Data - CSAT MVCC": "1872342491",
    "Data - CSAT Voyce": "1611100582",
    "Data - RT Voyce": "314541743",
    "Data - Calls MVCC": "1290371302",
    "Data - RT MVCC": "371802931",
    "Data - Calls Voyce": "1982301923",
    "Data - TM MVCC": "582910293",
    "Data - Calls Voyce 2": "472910392"  # (تنويه: الـ gids دي أمثلة، هنظبطها سوا لو الاسم اختلف)
}

st.info("🔄 جاري قراءة الـ 8 شيتات من Google Sheets وتجميعهم... برجاء الانتظار ثواني.")

try:
    # قائمة لحفظ الجداول بعد قراءتها
    all_dfs = {}
    
    # الالتفاف على الـ 8 شيتات وقراءتهم واحد واحد
    for sheet_name, gid in SHETS_DICTIONARY.items():
        full_url = BASE_URL + gid
        # نقرأ الشيت، وإذا كان فيه أعمدة مكررة أو مساحات ننظفها
        df_sheet = pd.read_csv(full_url)
        # تنظيف أسماء الأعمدة من أي مسافات زائدة
        df_sheet.columns = df_sheet.columns.str.strip()
        all_dfs[sheet_name] = df_sheet
        
    st.success("✅ تم قراءة الـ 8 شيتات بنجاح في الخلفية!")
    
    # 3. عرض شريط جانبي (Sidebar) عشان تتنقل بين الشيتات وتتأكد إنها مقروءة صح
    st.sidebar.header("⚙️ لوحة التحكم")
    preview_sheet = st.sidebar.selectbox("اختر شيت لمعاينته بشكل منفصل:", list(SHETS_DICTIONARY.keys()))
    
    st.subheader(f"👀 معاينة بيانات شيت: {preview_sheet}")
    st.dataframe(all_dfs[preview_sheet].head(10))

except Exception as e:
    st.error(f"حصلت مشكلة أثناء قراءة الشيتات: {e}")
