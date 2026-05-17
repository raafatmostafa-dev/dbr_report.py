import streamlit as st
import pandas as pd

# 1. إعداد الصفحة في المتصفح
st.set_page_config(page_title="DBR 14-Columns Complete Dashboard", layout="wide")
st.title("📊 لوحة التحكم الموحدة لتقارير الـ DBR (الـ 14 عمود كاملة)")

RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري تجميع الـ 14 عمود بالكامل وفرض الترتيب الصارم... ثواني من فضلك.")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    all_dfs = {}
    all_agents = set()
    
    for name in excel_file.sheet_names:
        df = excel_file.parse(name)
        df.columns = df.columns.astype(str).str.strip()
        all_dfs[name] = df
        
        if "Agent Name" in df.columns:
            agents_clean = df["Agent Name"].dropna().astype(str).str.strip()
            agents_clean = [a for a in agents_clean.unique() if a and a.lower() not in ["nan", "null", "0", "0.0"]]
            all_agents.update(agents_clean)
                
    # إنشاء الجدول الأساسي بأسماء الـ Agents الفعليين
    master_df = pd.DataFrame(sorted(list(all_agents), key=str), columns=["Agent Name"])

    # ----------------------------------------------------
    # 1. شيت [Calls MVCC] والـ Rates بتعتها (بناءً على المسميات الحقيقية في الشيت)
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_src = all_dfs["Calls MVCC"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        # السحب بالمسميات الحرفية الموجودة في الشيت الفعلي لمنع الـ KeyError
        df_src["Assigned Calls MVCC_calc"] = pd.to_numeric(df_src["Assigned Calls"], errors='coerce') if "Assigned Calls" in df_src.columns else 0
        df_src["Accepted Calls MVCC_calc"] = pd.to_numeric(df_src["Accepted Calls"], errors='coerce') if "Accepted Calls" in df_src.columns else 0
        df_src["Timed Out MVCC_calc"] = pd.to_numeric(df_src["Timed Out MVCC"], errors='coerce') if "Timed Out MVCC" in df_src.columns else 0
        df_src["Cancelled MVCC_calc"] = pd.to_numeric(df_src["Cancelled MVCC"], errors='coerce') if "Cancelled MVCC" in df_src.columns else 0
        df_src["Abandoned MVCC_calc"] = pd.to_numeric(df_src["Abandoned MVCC"], errors='coerce') if "Abandoned MVCC" in df_src.columns else 0
        
        for r_col in ["CSR", "Abondand rate", "Cancelled Rate"]:
            if r_col in df_src.columns:
                df_src[r_col] = df_src[r_col].astype(str).str.replace('%', '', regex=False)
                df_src[r_col] = pd.to_numeric(df_src[r_col], errors='coerce')
                if df_src[r_col].max() <= 1.0 and df_src[r_col].max() > 0:
                    df_src[r_col] = df_src[r_col] * 100

        agg_rules = {
            "Assigned Calls MVCC_calc": "sum",
            "Accepted Calls MVCC_calc": "sum",
            "Timed Out MVCC_calc": "sum",
            "Cancelled MVCC_calc": "sum",
            "Abandoned MVCC_calc": "sum"
        }
        if "CSR" in df_src.columns: agg_rules["CSR"] = "mean"
        if "Abondand rate" in df_src.columns: agg_rules["Abondand rate"] = "mean"
        if "Cancelled Rate" in df_src.columns: agg_rules["Cancelled Rate"] = "mean"
        
        df_g = df_src.groupby("Agent Name", as_index=False).agg(agg_rules)
        # إعادة التسمية للمسميات الـ 14 المطلوبة للجدول النهائي
        df_g = df_g.rename(columns={
            "Assigned Calls MVCC_calc": "Assigned Calls MVCC",
            "Accepted Calls MVCC_calc": "Accepted Calls MVCC",
            "Timed Out MVCC_calc": "Timed Out MVCC",
            "Cancelled MVCC_calc": "Cancelled MVCC",
            "Abandoned MVCC_calc": "Abandoned MVCC"
        })
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 2. شيت [Calls Voyce]
    # ----------------------------------------------------
    if "Calls Voyce" in all_dfs:
        df_src = all_dfs["Calls Voyce"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        df_src["Assigned Calls Voyce"] = pd.to_numeric(df_src["Assigned Calls \\"], errors='coerce') if "Assigned Calls \\" in df_src.columns else 0
        df_src["Accepted Calls Voyce"] = pd.to_numeric(df_src["Accepted Calls \\"], errors='coerce') if "Accepted Calls \\" in df_src.columns else 0
        df_src["Talk Time Voyce"] = pd.to_numeric(df_src["Talk Time Voyce"], errors='coerce') if "Talk Time Voyce" in df_src.columns else 0
        df_src["Missing Calls Voyce"] = pd.to_numeric(df_src["Missing Calls \\"], errors='coerce') if "Missing Calls \\" in df_src.columns else 0
        
        df_g = df_src.groupby("Agent Name", as_index=False)[["Assigned Calls Voyce", "Accepted Calls Voyce", "Talk Time Voyce", "Missing Calls Voyce"]].sum()
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 3. شيتات الـ CSAT للشركتين
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs:
        df_src = all_dfs["CSAT MVCC"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        if "CSAT MVCC" in df_src.columns:
            df_src["CSAT MVCC"] = pd.to_numeric(df_src["CSAT MVCC"], errors='coerce')
            df_g = df_src.groupby("Agent Name", as_index=False)["CSAT MVCC"].mean()
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    if "CSAT Voyce" in all_dfs:
        df_src = all_dfs["CSAT Voyce"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        if "CSAT" in df_src.columns:
            df_src["CSAT Voyce"] = pd.to_numeric(df_src["CSAT"], errors='coerce')
            df_g = df_src.groupby("Agent Name", as_index=False)["CSAT Voyce"].mean()
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 4. بناء وتأمين الـ 14 عمود بالترتيب الحرفي الصارم
    # ----------------------------------------------------
    required_columns = [
        "Assigned Calls MVCC",   # 1
        "Accepted Calls MVCC",   # 2
        "CSR",                   # 3
        "Timed Out MVCC",        # 4
        "Cancelled MVCC",        # 5
        "Abandoned MVCC",        # 6
        "Abondand rate",         # 7
        "Cancelled Rate",        # 8
        "Assigned Calls Voyce",  # 9
        "Accepted Calls Voyce",  # 10
        "Talk Time Voyce",       # 11
        "Missing Calls Voyce",   # 12
        "CSAT MVCC",             # 13
        "CSAT Voyce"             # 14
    ]

    for col in required_columns:
        if col not in master_df.columns:
            master_df[col] = 0.0

    master_df[required_columns] = master_df[required_columns].fillna(0.0)
    master_df = master_df[~master_df["Agent Name"].isin(["0", "0.0", "nan", "None"])]

    # تنسيق النسب المئوية
    rate_cols = ["CSR", "Abondand rate", "Cancelled Rate"]
    for r_col in rate_cols:
        master_df[r_col] = master_df[r_col].apply(lambda x: f"{x:.2f}%" if x > 0 else "0.00%")

    final_order = ["Agent Name"] + required_columns
    master_df = master_df.reindex(columns=final_order)

    st.success("✅ تم حل مشكلة مسميات الأعمدة والـ 14 عمود جاهزون بالترتيب الصحيح!")

    # 5. شريط البحث والتصفية
    st.sidebar.header("🔍 تصفية التقارير")
    search_query = st.sidebar.text_input("ابحث باسم الـ Agent:")
    
    filtered_df = master_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Agent Name"].str.contains(search_query, case=False)]

    # عرض الجدول
    st.subheader("📋 تقرير الـ DBR النهائي الـ 14 عمود:")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"حصل خطأ أثناء معالجة البيانات: {e}")
