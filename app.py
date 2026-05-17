import streamlit as st
import pandas as pd

# 1. إعداد الصفحة في المتصفح
st.set_page_config(page_title="DBR Sorted Dashboard", layout="wide")
st.title("📊 لوحة التحكم الموحدة لتقارير الـ DBR (بالترتيب الدقيق)")

RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري معالجة البيانات وترتيب الأعمدة بدقة... ثواني من فضلك.")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    target_sheets = ["CSAT MVCC", "CSAT Voyce", "Calls MVCC", "Calls Voyce", "RT MVCC", "RT Voyce", "TM MVCC", "Voyce Dis"]
    all_dfs = {}
    all_agents = set()
    
    # قراءة وتنظيف أولي لجميع الشيتات
    for name in target_sheets:
        if name in excel_file.sheet_names:
            df = excel_file.parse(name)
            df.columns = df.columns.str.strip()
            all_dfs[name] = df
            if "Agent Name" in df.columns:
                agents_clean = df["Agent Name"].dropna().astype(str).str.strip()
                agents_clean = [a for a in agents_clean.unique() if a and a.lower() not in ["nan", "null", ""]]
                all_agents.update(agents_clean)
                
    # الجدول الموحد للأسماء (الأساس)
    master_df = pd.DataFrame(sorted(list(all_agents), key=str), columns=["Agent Name"])

    # ----------------------------------------------------
    # 1. سحب بيانات شيت [Calls MVCC] والـ Rates بتعتها
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_src = all_dfs["Calls MVCC"]
        df_sub = pd.DataFrame()
        df_sub["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        # المقاييس الرقمية المباشرة (جمع)
        cols_to_sum = ["Assigned Calls", "Accepted Calls", "Timed Out MVCC", "Cancelled MVCC", "Abandoned MVCC"]
        for col in cols_to_sum:
            if col in df_src.columns:
                df_sub[col] = pd.to_numeric(df_src[col], errors='coerce')
        
        # النسب المئوية (متوسط)
        if "CSR" in df_src.columns:
            df_sub["CSR"] = pd.to_numeric(df_src["CSR"].astype(str).str.replace('%',''), errors='coerce') / 100
        if "Abondand rate" in df_src.columns:
            df_sub["Abondand rate"] = pd.to_numeric(df_src["Abondand rate"].astype(str).str.replace('%',''), errors='coerce') / 100
        if "Cancelled Rate" in df_src.columns:
            df_sub["Cancelled Rate"] = pd.to_numeric(df_src["Cancelled Rate"].astype(str).str.replace('%',''), errors='coerce') / 100

        # تطبيق القواعد (الجمع للمكالمات والمتوسط للنسب)
        agg_rules = {}
        for col in df_sub.columns:
            if col != "Agent Name":
                agg_rules[col] = "mean" if ("rate" in col.lower() or "CSR" in col) else "sum"
                    
        df_g = df_sub.groupby("Agent Name", as_index=False).agg(agg_rules)
        df_g = df_g.rename(columns={
            "Assigned Calls": "Assigned Calls MVCC",
            "Accepted Calls": "Accepted Calls MVCC"
        })
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 2. سحب بيانات شيت [Calls Voyce]
    # ----------------------------------------------------
    if "Calls Voyce" in all_dfs:
        df_src = all_dfs["Calls Voyce"]
        mapping = {
            "Assigned Calls \\": "Assigned Calls Voyce",
            "Accepted Calls \\": "Accepted Calls Voyce",
            "Talk Time Voyce": "Talk Time Voyce",
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
    # 3. سحب شيتات الـ CSAT (الـ MVCC والـ Voyce)
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs and "CSAT MVCC" in all_dfs["CSAT MVCC"].columns:
        df_c_mvcc = all_dfs["CSAT MVCC"]
        df_sub = df_c_mvcc[["Agent Name", "CSAT MVCC"]].copy()
        df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
        df_sub["CSAT MVCC"] = pd.to_numeric(df_sub["CSAT MVCC"], errors='coerce')
        df_g = df_sub.groupby("Agent Name", as_index=False)["CSAT MVCC"].mean()
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    if "CSAT Voyce" in all_dfs and "CSAT" in all_dfs["CSAT Voyce"].columns:
        df_c_voyce = all_dfs["CSAT Voyce"]
        df_sub = df_c_voyce[["Agent Name", "CSAT"]].copy()
        df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
        df_sub["CSAT"] = pd.to_numeric(df_sub["CSAT"], errors='coerce')
        df_g = df_sub.groupby("Agent Name", as_index=False)["CSAT"].mean()
        df_g = df_g.rename(columns={"CSAT": "CSAT Voyce"})
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 4. ملء الخلايا الفاضية وتنسيق النسب المئوية
    # ----------------------------------------------------
    numeric_cols = master_df.columns.drop("Agent Name")
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

    # تحويل النسب لشكلها المئوي (%)
    rate_cols = ["CSR", "Abondand rate", "Cancelled Rate"]
    for r_col in rate_cols:
        if r_col in master_df.columns:
            master_df[r_col] = master_df[r_col].apply(lambda x: f"{x*100:.2f}%" if x > 0 else "0.00%")

    # ----------------------------------------------------
    # 5. الترتيب الإجباري والمثالي للأعمدة بناءً على طلبك بالظبط
    # ----------------------------------------------------
    final_sorted_columns = [
        "Agent Name",
        "Assigned Calls MVCC",
        "Accepted Calls MVCC",
        "CSR",
        "Timed Out MVCC",
        "Cancelled MVCC",
        "Abandoned MVCC",
        "Abondand rate",
        "Cancelled Rate",
        "Assigned Calls Voyce",
        "Accepted Calls Voyce",
        "Talk Time Voyce",
        "Missing Calls Voyce",
        "CSAT MVCC",
        "CSAT Voyce"
    ]
    
    # التأكد من عدم حدوث كراش لو عمود سقط من الشيت الأصلي
    final_columns_present = [col for col in final_sorted_columns if col in master_df.columns]
    master_df = master_df[final_columns_present]

    st.success("✅ تم الترتيب بالثانية وبدون أي لخبطة!")

    # 6. شريط البحث الجانبي
    st.sidebar.header("🔍 تصفية التقارير")
    search_query = st.sidebar.text_input("ابحث باسم الـ Agent:")
    
    filtered_df = master_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Agent Name"].str.contains(search_query, case=False)]

    # عرض الجدول النهائي المرتب
    st.subheader("📋 الجدول النهائي المرتب (Per Agent):")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"حصلت مشكلة أثناء الترتيب: {e}")
