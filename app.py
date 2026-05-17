import streamlit as st
import pandas as pd
import numpy as np

# 1. إعداد الصفحة في المتصفح
st.set_page_config(page_title="DBR Ultimate Dashboard", layout="wide")
st.title("📊 لوحة التحكم الموحدة لتقارير الـ DBR")

RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري معالجة الـ 8 شيتات وحساب الـ KPIs لجميع الوكلاء... برجاء الانتظار ثواني.")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    # الشيتات الأساسية المتواجدة في الصور
    target_sheets = ["CSAT MVCC", "CSAT Voyce", "Calls MVCC", "Calls Voyce", "RT MVCC", "RT Voyce", "TM MVCC", "Voyce Dis"]
    all_dfs = {}
    all_agents = set()
    
    # قراءة وتنظيف أولي لجميع الشيتات
    for name in target_sheets:
        if name in excel_file.sheet_names:
            df = excel_file.parse(name)
            df.columns = df.columns.str.strip() # تنظيف أسماء الأعمدة
            all_dfs[name] = df
            if "Agent Name" in df.columns:
                agents_clean = df["Agent Name"].dropna().astype(str).str.strip()
                agents_clean = [a for a in agents_clean.unique() if a and a.lower() not in ["nan", "null", ""]]
                all_agents.update(agents_clean)
                
    # الجدول الموحد للأسماء
    master_df = pd.DataFrame(sorted(list(all_agents), key=str), columns=["Agent Name"])

    # ----------------------------------------------------
    # 1. سحب البيانات من شيت [CSAT MVCC]
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs:
        df_src = all_dfs["CSAT MVCC"]
        if "Agent Name" in df_src.columns and "CSAT MVCC" in df_src.columns:
            df_sub = df_src[["Agent Name", "CSAT MVCC"]].copy()
            df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
            df_sub["CSAT MVCC"] = pd.to_numeric(df_sub["CSAT MVCC"], errors='coerce')
            # حساب المتوسط
            df_g = df_sub.groupby("Agent Name", as_index=False)["CSAT MVCC"].mean()
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 2. سحب البيانات من شيت [CSAT Voyce]
    # ----------------------------------------------------
    if "CSAT Voyce" in all_dfs:
        df_src = all_dfs["CSAT Voyce"]
        if "Agent Name" in df_src.columns and "CSAT" in df_src.columns:
            df_sub = df_src[["Agent Name", "CSAT"]].copy()
            df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
            df_sub["CSAT"] = pd.to_numeric(df_sub["CSAT"], errors='coerce')
            df_g = df_sub.groupby("Agent Name", as_index=False)["CSAT"].mean()
            df_g = df_g.rename(columns={"CSAT": "CSAT Voyce"})
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 3. سحب المقاييس المطلوبة من شيت [Calls MVCC]
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_src = all_dfs["Calls MVCC"]
        cols_to_sum = ["Assigned Calls", "Accepted Calls", "Timed Out MVCC", "Cancelled MVCC", "Abandoned MVCC"]
        # التأكد من مطابقة أسمائها بالضبط وتحويلها لأرقام
        df_sub = pd.DataFrame()
        df_sub["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        for col in cols_to_sum:
            if col in df_src.columns:
                df_sub[col] = pd.to_numeric(df_src[col], errors='coerce')
        
        # حساب المعدلات الإضافية المطلوبة: CSR, Abondand rate, Cancelled Rate
        if "CSR" in df_src.columns:
            df_sub["CSR"] = pd.to_numeric(df_src["CSR"].astype(str).str.replace('%',''), errors='coerce') / 100
        if "Abondand rate" in df_src.columns:
            df_sub["Abondand rate"] = pd.to_numeric(df_src["Abondand rate"].astype(str).str.replace('%',''), errors='coerce') / 100
        if "Cancelled Rate" in df_src.columns:
            df_sub["Cancelled Rate"] = pd.to_numeric(df_src["Cancelled Rate"].astype(str).str.replace('%',''), errors='coerce') / 100

        # تجميع المجاميع والمتوسطات
        agg_rules = {}
        for col in df_sub.columns:
            if col != "Agent Name":
                if "rate" in col.lower() or "rate" in col or "CSR" in col:
                    agg_rules[col] = "mean"
                else:
                    agg_rules[col] = "sum"
                    
        df_g = df_sub.groupby("Agent Name", as_index=False).agg(agg_rules)
        # إعادة تسمية الأعمدة لتطابق طلبك بالضبط
        df_g = df_g.rename(columns={
            "Assigned Calls": "Assigned Calls MVCC",
            "Accepted Calls": "Accepted Calls MVCC"
        })
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 4. سحب المقاييس المطلوبة من شيت [Calls Voyce]
    # ----------------------------------------------------
    if "Calls Voyce" in all_dfs:
        df_src = all_dfs["Calls Voyce"]
        # الأعمدة المطلوبة: Talk Time Voyce, Assigned Calls \, Accepted Calls \, Missing Calls \
        mapping = {
            "Talk Time Voyce": "Talk Time Voyce",
            "Assigned Calls \\": "Assigned Calls Voyce",
            "Accepted Calls \\": "Accepted Calls Voyce",
            "Missing Calls \\": "Missing Calls Voyce"
        }
        
        df_sub = pd.DataFrame()
        df_sub["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        for orig_col, new_col in mapping.items():
            if orig_col in df_src.columns:
                df_sub[new_col] = pd.to_numeric(df_src[orig_col], errors='coerce')
                
        df_g = df_sub.groupby("Agent Name", as_index=False).sum()
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 5. تنظيف واستبدال الـ Nulls بـ 0 وتنسيق النسب المئوية
    # ----------------------------------------------------
    numeric_cols = master_df.columns.drop("Agent Name")
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

    # تنسيق خانات الـ Rates كنسب مئوية مريحة للعين
    rate_cols = ["CSR", "Abondand rate", "Cancelled Rate"]
    for r_col in rate_cols:
        if r_col in master_df.columns:
            master_df[r_col] = master_df[r_col].apply(lambda x: f"{x*100:.2f}%" if x > 0 else "0.00%")

    st.success("🎉 تم تجميع ودمج كافة الأعمدة المطلوبة بنجاح تام!")

    # 6. إضافة فلتر البحث الذكي في السايد بار
    st.sidebar.header("🔍 فلترة وتصفية")
    search_query = st.sidebar.text_input("ابحث عن Agent معين:")
    
    filtered_df = master_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Agent Name"].str.contains(search_query, case=False)]

    # عرض الجدول النهائي الضخم والمدمج
    st.subheader(f"📋 جدول أداء الـ DBR الشامل (عدد الوكلاء الحالي: {len(filtered_df)}):")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"حصلت مشكلة أثناء تجميع ودمج البيانات: {e}")
