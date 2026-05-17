import streamlit as st
import pandas as pd

# 1. إعداد الصفحة
st.set_page_config(page_title="DBR 14-Columns Robust Dashboard", layout="wide")
st.title("📊 لوحة التحكم الموحدة لتقارير الـ DBR (الـ 14 عمود كاملة)")

RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري مطابقة الأعمدة ديناميكياً وحساب البيانات... ثواني من فضلك.")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    all_dfs = {}
    all_agents = set()
    
    # لفة أولى لتنظيف وتجهيز الشيتات وتجميع الـ Agents
    for name in excel_file.sheet_names:
        df = excel_file.parse(name)
        df.columns = df.columns.astype(str).str.strip()
        all_dfs[name] = df
        if "Agent Name" in df.columns:
            agents_clean = df["Agent Name"].dropna().astype(str).str.strip()
            agents_clean = [a for a in agents_clean.unique() if a and a.lower() not in ["nan", "null", "0", "0.0"]]
            all_agents.update(agents_clean)
                
    # الجدول الأساسي الموحد للـ Agents
    master_df = pd.DataFrame(sorted(list(all_agents), key=str), columns=["Agent Name"])

    # دالة ذكية للبحث عن العمود بمجرد احتواء اسمه على الكلمة الأساسية (تجنباً لاختلاف الرموز والـ MVCC)
    def find_col(df_columns, keyword):
        for c in df_columns:
            if keyword.lower() in c.lower():
                return c
        return None

    # ----------------------------------------------------
    # 1. معالجة شيت [Calls MVCC] -> (Sum و AVG)
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_src = all_dfs["Calls MVCC"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        # البحث الديناميكي عن الأعمدة وحساب الـ Sum
        c_assigned = find_col(df_src.columns, "Assigned Calls")
        c_accepted = find_col(df_src.columns, "Accepted Calls")
        c_timeout  = find_col(df_src.columns, "Timed Out")
        c_cancel   = find_col(df_src.columns, "Cancelled MVCC") or find_col(df_src.columns, "Cancelled")
        c_abandon  = find_col(df_src.columns, "Abandoned")
        
        df_src["Assigned Calls MVCC_raw"] = pd.to_numeric(df_src[c_assigned], errors='coerce') if c_assigned else 0
        df_src["Accepted Calls MVCC_raw"] = pd.to_numeric(df_src[c_accepted], errors='coerce') if c_accepted else 0
        df_src["Timed Out MVCC_raw"] = pd.to_numeric(df_src[c_timeout], errors='coerce') if c_timeout else 0
        df_src["Cancelled MVCC_raw"] = pd.to_numeric(df_src[c_cancel], errors='coerce') if c_cancel else 0
        df_src["Abandoned MVCC_raw"] = pd.to_numeric(df_src[c_abandon], errors='coerce') if c_abandon else 0
        
        # معالجة النسب المئوية للـ AVG
        rate_cols_mapping = {}
        for r_col in ["CSR", "Abondand rate", "Cancelled Rate"]:
            actual_col = find_col(df_src.columns, r_col)
            if actual_col:
                df_src[r_col] = df_src[actual_col].astype(str).str.replace('%', '', regex=False)
                df_src[r_col] = pd.to_numeric(df_src[r_col], errors='coerce')
                if df_src[r_col].max() <= 1.0 and df_src[r_col].max() > 0:
                    df_src[r_col] = df_src[r_col] * 100
                rate_cols_mapping[r_col] = "mean"

        agg_rules = {
            "Assigned Calls MVCC_raw": "sum",
            "Accepted Calls MVCC_raw": "sum",
            "Timed Out MVCC_raw": "sum",
            "Cancelled MVCC_raw": "sum",
            "Abandoned MVCC_raw": "sum"
        }
        agg_rules.update(rate_cols_mapping)
        
        df_g = df_src.groupby("Agent Name", as_index=False).agg(agg_rules)
        df_g = df_g.rename(columns={
            "Assigned Calls MVCC_raw": "Assigned Calls MVCC",
            "Accepted Calls MVCC_raw": "Accepted Calls MVCC",
            "Timed Out MVCC_raw": "Timed Out MVCC",
            "Cancelled MVCC_raw": "Cancelled MVCC",
            "Abandoned MVCC_raw": "Abandoned MVCC"
        })
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 2. معالجة شيت [Calls Voyce] -> (Sum لكل الأعمدة)
    # ----------------------------------------------------
    if "Calls Voyce" in all_dfs:
        df_src = all_dfs["Calls Voyce"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        c_assigned_v = find_col(df_src.columns, "Assigned Calls")
        c_accepted_v = find_col(df_src.columns, "Accepted Calls")
        c_talk_v     = find_col(df_src.columns, "Talk Time")
        c_missing_v  = find_col(df_src.columns, "Missing Calls")
        
        df_src["Assigned Calls Voyce_raw"] = pd.to_numeric(df_src[c_assigned_v], errors='coerce') if c_assigned_v else 0
        df_src["Accepted Calls Voyce_raw"] = pd.to_numeric(df_src[c_accepted_v], errors='coerce') if c_accepted_v else 0
        df_src["Talk Time Voyce_raw"] = pd.to_numeric(df_src[c_talk_v], errors='coerce') if c_talk_v else 0
        df_src["Missing Calls Voyce_raw"] = pd.to_numeric(df_src[c_missing_v], errors='coerce') if c_missing_v else 0
        
        df_g = df_src.groupby("Agent Name", as_index=False).agg({
            "Assigned Calls Voyce_raw": "sum",
            "Accepted Calls Voyce_raw": "sum",
            "Talk Time Voyce_raw": "sum",
            "Missing Calls Voyce_raw": "sum"
        }).rename(columns={
            "Assigned Calls Voyce_raw": "Assigned Calls Voyce",
            "Accepted Calls Voyce_raw": "Accepted Calls Voyce",
            "Talk Time Voyce_raw": "Talk Time Voyce",
            "Missing Calls Voyce_raw": "Missing Calls Voyce"
        })
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 3. معالجة شيتات الـ CSAT للشركتين -> (AVG)
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs:
        df_src = all_dfs["CSAT MVCC"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        c_csat_m = find_col(df_src.columns, "CSAT")
        if c_csat_m:
            df_src["CSAT MVCC_raw"] = pd.to_numeric(df_src[c_csat_m], errors='coerce')
            df_g = df_src.groupby("Agent Name", as_index=False)["CSAT MVCC_raw"].mean().rename(columns={"CSAT MVCC_raw": "CSAT MVCC"})
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    if "CSAT Voyce" in all_dfs:
        df_src = all_dfs["CSAT Voyce"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        c_csat_v = find_col(df_src.columns, "CSAT")
        if c_csat_v:
            df_src["CSAT Voyce_raw"] = pd.to_numeric(df_src[c_csat_v], errors='coerce')
            df_g = df_src.groupby("Agent Name", as_index=False)["CSAT Voyce_raw"].mean().rename(columns={"CSAT Voyce_raw": "CSAT Voyce"})
            master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 4. بناء وترتيب الأعمدة الـ 14 المطلوبة بدقة هندسية
    # ----------------------------------------------------
    required_columns = [
        "Assigned Calls MVCC",   # 1 Sum
        "Accepted Calls MVCC",   # 2 Sum
        "CSR",                   # 3 AVG
        "Timed Out MVCC",        # 4 Sum
        "Cancelled MVCC",        # 5 Sum
        "Abandoned MVCC",        # 6 Sum
        "Abondand rate",         # 7 AVG
        "Cancelled Rate",        # 8 AVG
        "Assigned Calls Voyce",  # 9 Sum
        "Accepted Calls Voyce",  # 10 Sum
        "Talk Time Voyce",       # 11 Sum
        "Missing Calls Voyce",   # 12 Sum
        "CSAT MVCC",             # 13 AVG
        "CSAT Voyce"             # 14 AVG
    ]

    for col in required_columns:
        if col not in master_df.columns:
            master_df[col] = 0.0

    master_df[required_columns] = master_df[required_columns].fillna(0.0)
    master_df = master_df[~master_df["Agent Name"].isin(["0", "0.0", "nan", "None"])]

    # تنسيق النسب المئوية للـ Rates الثلاثة فقط
    rate_cols = ["CSR", "Abondand rate", "Cancelled Rate"]
    for r_col in rate_cols:
        master_df[r_col] = master_df[r_col].apply(lambda x: f"{x:.2f}%" if x > 0 else "0.00%")

    # الترتيب النهائي الحتمي
    final_order = ["Agent Name"] + required_columns
    master_df = master_df.reindex(columns=final_order)

    st.success("🎉 تم دمج الـ 14 عمود وحساب الـ Sum والـ AVG ديناميكياً وبأعلى دقة!")

    # 5. شريط البحث والتصفية
    st.sidebar.header("🔍 تصفية التقارير")
    search_query = st.sidebar.text_input("ابحث باسم الـ Agent:")
    
    filtered_df = master_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Agent Name"].str.contains(search_query, case=False)]

    # عرض الجدول النهائي الموحد
    st.subheader("📋 تقرير الـ DBR النهائي الـ 14 عمود الموحد والمكتمل:")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"حصل خطأ أثناء معالجة البيانات: {e}")
