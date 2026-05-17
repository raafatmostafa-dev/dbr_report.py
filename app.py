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
    
    # قراءة وتنظيف أولي لجميع الشيتات لضمان عدم سقوط أي بيانات
    all_dfs = {}
    all_agents = set()
    
    for name in excel_file.sheet_names:
        df = excel_file.parse(name)
        df.columns = df.columns.str.strip()
        all_dfs[name] = df
        if "Agent Name" in df.columns:
            agents_clean = df["Agent Name"].dropna().astype(str).str.strip()
            agents_clean = [a for a in agents_clean.unique() if a and a.lower() not in ["nan", "null", "0", "0.0"]]
            all_agents.update(agents_clean)
                
    # إنشاء الجدول الأساسي بأسماء الـ Agents الفعليين
    master_df = pd.DataFrame(sorted(list(all_agents), key=str), columns=["Agent Name"])

    # ----------------------------------------------------
    # 1. شيت [Calls MVCC] والـ Rates بتعتها
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_src = all_dfs["Calls MVCC"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        # تجهيز الأعمدة الفردية وتأكيد تحويلها لأرقام
        df_src["Assigned Calls MVCC"] = pd.to_numeric(df_src["Assigned Calls"], errors='coerce')
        df_src["Accepted Calls MVCC"] = pd.to_numeric(df_src["Accepted Calls"], errors='coerce')
        df_src["Timed Out MVCC"] = pd.to_numeric(df_src["Timed Out MVCC"], errors='coerce')
        df_src["Cancelled MVCC"] = pd.to_numeric(df_src["Cancelled MVCC"], errors='coerce')
        df_src["Abandoned MVCC"] = pd.to_numeric(df_src["Abandoned MVCC"], errors='coerce')
        
        # التعامل مع النسب المئوية
        for r_col in ["CSR", "Abondand rate", "Cancelled Rate"]:
            if r_col in df_src.columns:
                df_src[r_col] = df_src[r_col].astype(str).str.replace('%', '', regex=False)
                df_src[r_col] = pd.to_numeric(df_src[r_col], errors='coerce')
                # لو الأرقام مخزنة كنسبة عشرية (مثلاً 0.98 بدلاً من 98)
                if df_src[r_col].max() <= 1.0 and df_src[r_col].max() > 0:
                    df_src[r_col] = df_src[r_col] * 100

        # تجميع البيانات: جمع للمكالمات ومتوسط للنسب
        agg_rules = {
            "Assigned Calls MVCC": "sum",
            "Accepted Calls MVCC": "sum",
            "Timed Out MVCC": "sum",
            "Cancelled MVCC": "sum",
            "Abandoned MVCC": "sum"
        }
        if "CSR" in df_src.columns: agg_rules["CSR"] = "mean"
        if "Abondand rate" in df_src.columns: agg_rules["Abondand rate"] = "mean"
        if "Cancelled Rate" in df_src.columns: agg_rules["Cancelled Rate"] = "mean"
        
        df_g = df_src.groupby("Agent Name", as_index=False).agg(agg_rules)
        master_df = pd.merge(master_df, df_g, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 2. شيت [Calls Voyce]
    # ----------------------------------------------------
    if "Calls Voyce" in all_dfs:
        df_src = all_dfs["Calls Voyce"].copy()
        df_src["Agent Name"] = df_src["Agent Name"].astype(str).str.strip()
        
        # مطابقة الأعمدة بناءً على شكل الشيت الحقيقي
        df_src["Assigned Calls Voyce"] = pd.to_numeric(df_src["Assigned Calls \\"], errors='coerce')
        df_src["Accepted Calls Voyce"] = pd.to_numeric(df_src["Accepted Calls \\"], errors='coerce')
        df_src["Talk Time Voyce"] = pd.to_numeric(df_src["Talk Time Voyce"], errors='coerce')
        df_src["Missing Calls Voyce"] = pd.to_numeric(df_src["Missing Calls \\"], errors='coerce')
        
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
    # 4. الـ 14 عمود بالترتيب الإجباري (خلق الأعمدة لو مش موجودة)
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

    # التأكد من خلق العمود حتى لو الشيت سقط علشان يظهر الجدول كامل 14 عمود
    for col in required_columns:
        if col not in master_df.columns:
            master_df[col] = 0.0

    # ملء الخلايا الفاضية بأصفار قبل التنسيق
    master_df[required_columns] = master_df[required_columns].fillna(0.0)

    # تصفية أسماء الـ Agents الوهمية أو الصفرية الناتجة عن دمج الشيتات
    master_df = master_df[~master_df["Agent Name"].isin(["0", "0.0", "nan", "None"])]

    # تنسيق النسب المئوية بشكل يضمن ظهور الـ % بشكل احترافي
    rate_cols = ["CSR", "Abondand rate", "Cancelled Rate"]
    for r_col in rate_cols:
        master_df[r_col] = master_df[r_col].apply(lambda x: f"{x:.2f}%" if x > 0 else "0.00%")

    # ترتيب الجدول النهائي بشكل صارم (اسم العميل أولاً ثم الـ 14 عمود بالترتيب)
    final_order = ["Agent Name"] + required_columns
    master_df = master_df.reindex(columns=final_order)

    st.success("✅ تم إجبار وظهور الـ 14 عمود كاملين بالترتيب الهندسي المظبوط!")

    # 5. شريط البحث الجانبي
    st.sidebar.header("🔍 تصفية التقارير")
    search_query = st.sidebar.text_input("ابحث باسم الـ Agent:")
    
    filtered_df = master_df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["Agent Name"].str.contains(search_query, case=False)]

    # عرض الجدول الموحد الكامل
    st.subheader("📋 تقرير الـ DBR النهائي (14 عمود كاملة):")
    st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"حصل خطأ أثناء تحصين الأعمدة: {e}")
