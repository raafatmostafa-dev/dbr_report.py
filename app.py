import streamlit as st
import pandas as pd

# 1. إعداد شكل الصفحة في المتصفح
st.set_page_config(page_title="DBR Report", layout="wide")
st.title("📊 نظام دمج تقارير الـ DBR")

# 2. رابط الشيت بتاعك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=csv&gid=1872342491"

st.info("جاري محاولة الاتصال بـ Google Sheets وقراءة البيانات...")

try:
    # 3. قراءة البيانات باستخدام مكتبة Pandas
    df = pd.read_csv(SHEET_URL)
    
    st.success("تم الاتصال وقراءة الجدول الأول بنجاح! 🎉")
    
    # 4. عرض أول 10 صفوف من الشيت للتأكد
    st.subheader("👀 معاينة البيانات المرفوعة:")
    st.dataframe(df.head(10))

except Exception as e:
    st.error(f"حصلت مشكلة أثناء قراءة الشيت: {e}")
