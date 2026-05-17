import streamlit as st
import pandas as pd

# 1. إعداد الصفحة
st.set_page_config(page_title="DBR Multi-Sheet Merge", layout="wide")
st.title("📊 نظام تجميع ودمج تقارير الـ DBR")

# رابط ملف جوجل شيت الرئيسي (بصيغة إكسيل لقراءة كل الشيتات الفرعية)
RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري قراءة الملف ودمج البيانات... برجاء الانتظار ثواني.")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    # أسماء الـ 8 شيتات الفرعية
    target_sheets = [
        "CSAT MVCC", "CSAT Voyce", "Calls MVCC", "Calls Voyce", 
        "RT MVCC", "RT Voyce", "TM MVCC", "Voyce Dis"
    ]
    
    all_agents = set()
    all_dfs = {}
    
    # أولاً: لفة سريعة لتجميع كل الأسماء الفريدة من كل الشيتات
    for sheet_name in target_sheets:
        if sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)
            df.columns = df.columns.str.strip() # تنظيف أسماء الأعمدة
            all_dfs[sheet_name] = df
            if "Agent Name" in df.columns:
                agents_in_sheet = df["Agent Name"].dropna().str.strip().unique()
                all_agents.update(agents_in_sheet)
    
    # إنشاء الجدول الأساسي للأسماء (الموحد)
    master_df = pd.DataFrame(sorted(list(all_agents)), columns=["Agent Name"])
    
    # ----------------------------------------------------
    # خطوتنا الحالية: سحب الـ Avg Call Rating من شيت CSAT MVCC
    # ----------------------------------------------------
    sheet_csat_mvcc = "CSAT MVCC"
    if sheet_csat_mvcc in all_dfs:
        df_csat = all_dfs[sheet_csat_mvcc]
        
        # التأكد إن الأعمدة المطلوبة موجودة في الشيت ده
        if "Agent Name" in df_csat.columns and "Avg Call Rating" in df_csat.columns:
            # هناخد بس عمود الاسم وعمود الـ Avg Call Rating ونضفهم
            df_subset = df_csat[["Agent Name", "Avg Call Rating"]].copy()
            df_subset["Agent Name"] = df_subset["Agent Name"].astype(str).str.strip()
            
            # لو الـ Agent متكرر في الشيت، بنجيب متوسط تقييماته عشان ميتكررش في الجدول المدمج
            df_subset_grouped = df_subset.groupby("Agent Name", as_index=False)["Avg Call Rating"].mean()
            
            # دمج العمود جنب الأسماء (Left Join عشان نحافظ على كل الأسماء)
            master_df = pd.merge(master_df, df_subset_grouped, on="Agent Name", how="left")
            
            # تغيير اسم العمود عشان نكون عارفين إنه جاي من شيت MVCC
            master_df = master_df.rename(columns={"Avg Call Rating": "Avg Call Rating (MVCC)"})
            
            # استبدال الـ Nulls (الخلايا الفاضية) بـ 0 عشان التقرير يكون شكله نضيف
            master_df["Avg Call Rating (MVCC)"] = master_df["Avg Call Rating (MVCC)"].fillna(0)

    st.success("✅ تم رص الأسماء وسحب الـ Avg Call Rating بنجاح!")
    
    # 2. عرض الجدول بعد الخطوة الأولى
    st.subheader("📋 جدول البيانات الحالي:")
    st.dataframe(master_df, use_container_width=True)

except Exception as e:
    st.error(f"حصلت مشكلة أثناء معالجة البيانات: {e}")
