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
    
    # أولاً: لفة على كل الشيتات وتجميع الأسماء وتحويلها لنصوص بنسبة 100% لمنع خطأ الترتيب
    for sheet_name in target_sheets:
        if sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)
            df.columns = df.columns.str.strip() # تنظيف أسماء الأعمدة
            all_dfs[sheet_name] = df
            
            if "Agent Name" in df.columns:
                # تحويل العمود بالكامل لنصوص، وحذف الخلايا الفاضية أو القيم الغريبة
                agents_in_sheet = df["Agent Name"].dropna().astype(str).str.strip()
                # فلترة للتأكد إن الخلية مش فاضية بعد التنظيف ومش كلمة نل
                agents_in_sheet = agents_in_sheet[
                    (agents_in_sheet != "") & 
                    (agents_in_sheet.lower() != "nan") & 
                    (agents_in_sheet.lower() != "null")
                ]
                all_agents.update(agents_in_sheet.unique())
    
    # إنشاء الجدول الأساسي الموحد للأسماء وترتيبه بشكل آمن تماماً كـ نصوص
    sorted_agents = sorted(list(all_agents), key=str)
    master_df = pd.DataFrame(sorted_agents, columns=["Agent Name"])
    
    # ----------------------------------------------------
    # ثانياً: دمج الـ Avg Call Rating من شيت CSAT MVCC
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs:
        df_mvcc = all_dfs["CSAT MVCC"]
        if "Agent Name" in df_mvcc.columns and "Avg Call Rating" in df_mvcc.columns:
            df_subset = df_mvcc[["Agent Name", "Avg Call Rating"]].copy()
            df_subset["Agent Name"] = df_subset["Agent Name"].astype(str).str.strip()
            
            # حساب المتوسط لكل إيجنت
            df_grouped = df_subset.groupby("Agent Name", as_index=False)["Avg Call Rating"].mean()
            
            # الدمج
            master_df = pd.merge(master_df, df_grouped, on="Agent Name", how="left")
            master_df = master_df.rename(columns={"Avg Call Rating": "Avg Call Rating (MVCC)"})
            master_df["Avg Call Rating (MVCC)"] = master_df["Avg Call Rating (MVCC)"].fillna(0)

    # ----------------------------------------------------
    # ثالثاً: دمج الـ Avg Call Rating (أو الـ CSAT) من شيت CSAT Voyce
    # ----------------------------------------------------
    if "CSAT Voyce" in all_dfs:
        df_voyce = all_dfs["CSAT Voyce"]
        # ملحوظة: في شيت Voyce العمود مكتوب اسمه CSAT زي ما باين في صورتك، هنحسب متوسطه
        if "Agent Name" in df_voyce.columns and "CSAT" in df_voyce.columns:
            df_subset_v = df_voyce[["Agent Name", "CSAT"]].copy()
            df_subset_v["Agent Name"] = df_subset_v["Agent Name"].astype(str).str.strip()
            
            # تحويل القيم لأرقام عشان لو فيها نصوص متعملش مشكلة
            df_subset_v["CSAT"] = pd.to_numeric(df_subset_v["CSAT"], errors='coerce')
            df_grouped_v = df_subset_v.groupby("Agent Name", as_index=False)["CSAT"].mean()
            
            # الدمج
            master_df = pd.merge(master_df, df_grouped_v, on="Agent Name", how="left")
            master_df = master_df.rename(columns={"CSAT": "Avg Call Rating (Voyce)"})
            master_df["Avg Call Rating (Voyce)"] = master_df["Avg Call Rating (Voyce)"].fillna(0)

    st.success("✅ تم معالجة وتوحيد الأسماء وسحب التقييمات بنجاح!")
    
    # 2. عرض الجدول النهائي النظيف
    st.subheader("📋 تقرير الأداء المدمج الحالي (Per Agent):")
    st.dataframe(master_df, use_container_width=True)

except Exception as e:
    st.error(f"حصلت مشكلة أثناء معالجة البيانات: {e}")
