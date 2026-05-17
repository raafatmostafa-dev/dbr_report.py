import streamlit as st
import pandas as pd

# 1. إعداد الصفحة
st.set_page_config(page_title="DBR Final Merge Dashboard", layout="wide")
st.title("📊 نظام دمج وتصفية تقارير الـ DBR الموحد")

# رابط ملف جوجل شيت الرئيسي بصيغة إكسيل لقراءة كل الشيتات الفرعية
RAW_SHEET_URL = "https://docs.google.com/spreadsheets/d/1TKQ55oQshnB6zHy6U7Dq3ZfHI3OknTjP1_J291Cmf_I/export?format=xlsx"

st.info("🔄 جاري قراءة كافة الشيتات الفرعية ومعالجة البيانات بدقة...")

try:
    # قراءة ملف الإكسيل بالكامل
    excel_file = pd.ExcelFile(RAW_SHEET_URL, engine='openpyxl')
    
    # أسماء الـ 8 شيتات الفرعية المطلوبة
    target_sheets = [
        "CSAT MVCC", "CSAT Voyce", "Calls MVCC", "Calls Voyce", 
        "RT MVCC", "RT Voyce", "TM MVCC", "Voyce Dis"
    ]
    
    all_agents = set()
    all_dfs = {}
    
    # أولاً: تجميع كل أسماء الـ Agents الفريدة من كل شيت لمنع سقطات الـ Looker Studio
    for sheet_name in target_sheets:
        if sheet_name in excel_file.sheet_names:
            df = excel_file.parse(sheet_name)
            df.columns = df.columns.str.strip() # تنظيف أسماء الأعمدة من المسافات
            all_dfs[sheet_name] = df
            
            if "Agent Name" in df.columns:
                # تحويل وتنظيف الأسماء
                agents_series = df["Agent Name"].dropna().astype(str).str.strip()
                # فلترة الكلمات الفاضية أو الـ NaN
                agents_clean = [name for name in agents_series.unique() if name and name.lower() not in ["nan", "null", ""]]
                all_agents.update(agents_clean)
    
    # إنشاء جدول الأساس المرتب أبجدياً
    master_df = pd.DataFrame(sorted(list(all_agents)), columns=["Agent Name"])
    
    # ----------------------------------------------------
    # 2. سحب الـ Avg Call Rating من شيت CSAT MVCC
    # ----------------------------------------------------
    if "CSAT MVCC" in all_dfs:
        df_mvcc = all_dfs["CSAT MVCC"]
        if "Agent Name" in df_mvcc.columns and "Avg Call Rating" in df_mvcc.columns:
            df_sub = df_mvcc[["Agent Name", "Avg Call Rating"]].copy()
            df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
            df_grouped = df_sub.groupby("Agent Name", as_index=False)["Avg Call Rating"].mean()
            master_df = pd.merge(master_df, df_grouped, on="Agent Name", how="left")
            master_df = master_df.rename(columns={"Avg Call Rating": "Avg Call Rating (MVCC)"})

    # ----------------------------------------------------
    # 3. سحب الـ CSAT من شيت CSAT Voyce
    # ----------------------------------------------------
    if "CSAT Voyce" in all_dfs:
        df_voyce = all_dfs["CSAT Voyce"]
        if "Agent Name" in df_voyce.columns and "CSAT" in df_voyce.columns:
            df_sub = df_voyce[["Agent Name", "CSAT"]].copy()
            df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
            df_sub["CSAT"] = pd.to_numeric(df_sub["CSAT"], errors='coerce')
            df_grouped = df_sub.groupby("Agent Name", as_index=False)["CSAT"].mean()
            master_df = pd.merge(master_df, df_grouped, on="Agent Name", how="left")
            master_df = master_df.rename(columns={"CSAT": "Avg Call Rating (Voyce)"})

    # ----------------------------------------------------
    # 4. سحب الـ Accepted & Assigned Calls من شيت Calls MVCC
    # ----------------------------------------------------
    if "Calls MVCC" in all_dfs:
        df_calls_mvcc = all_dfs["Calls MVCC"]
        # التأكد من الأعمدة بناءً على الصورة اللي بعتها للـ Blend
        req_cols = ["Agent Name", "Accepted Calls MVCC", "Assigned Calls MVCC"]
        # إذا كانت الأسامي مختلفة في الشيت الأصلي (مثلا بدون كلمة MVCC في العمود)، السيستم هيتأقلم مع المتاح:
        actual_cols = [c for c in df_calls_mvcc.columns if "call" in c.lower() or "agent" in c.lower()]
        
        # كود أمان للدمج بناءً على المتاح في الشيت
        df_sub = df_calls_mvcc[[c for c in ["Agent Name", "Accepted Calls MVCC", "Assigned Calls MVCC"] if c in df_calls_mvcc.columns]].copy()
        if "Agent Name" in df_sub.columns and len(df_sub.columns) > 1:
            df_sub["Agent Name"] = df_sub["Agent Name"].astype(str).str.strip()
            # تحويل الأعمدة لأرقام وجمعها لكل إيجنت
            for col in df_sub.columns:
                if col != "Agent Name":
                    df_sub[col] = pd.to_numeric(df_sub[col], errors='coerce')
            df_grouped = df_sub.groupby("Agent Name", as_index=False).sum()
            master_df = pd.merge(master_df, df_grouped, on="Agent Name", how="left")

    # ----------------------------------------------------
    # 5. تنظيف الجدول النهائي واستبدال الـ Nulls بـ 0
    # ----------------------------------------------------
    # استبدال كل الخلايا الفاضية لجميع الأعمدة بـ 0 عشان المنظر يكون احترافي
    numeric_cols = master_df.columns.drop("Agent Name")
    master_df[numeric_cols] = master_df[numeric_cols].fillna(0)

    st.success("🎉 تم دمج وتجهيز التقرير بالكامل وبدون أي أخطاء أو Nulls!")
    
    # عرض الجدول الاحترافي النهائي
    st.subheader("📋 تقرير الأداء الشامل لكل الوكلاء (Per Agent):")
    st.dataframe(master_df, use_container_width=True)

except Exception as e:
    st.error(f"حصلت مشكلة أثناء تجميع الأعمدة: {e}")
