import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="النظام المالي للمسجد", layout="wide")

# 2. الاتصال بـ Supabase عبر Secrets
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

st.title("🕌 النظام المالي للمسجد")

# 3. جلب سعر الصرف والصناديق من السحابة مع حماية ضد الأخطاء
@st.cache_data(ttl=5)
def get_funds():
    try:
        res = supabase.table("funds").select("name").execute()
        if res.data:
            return [row["name"] for row in res.data]
    except Exception:
        pass
    return ["صندوق المسجد العام"]

@st.cache_data(ttl=5)
def get_rate():
    try:
        res = supabase.table("settings").select("value").eq("key", "dollar_rate").execute()
        if res.data and len(res.data) > 0:
            return float(res.data[0]["value"])
    except Exception:
        pass
    return 89500.0

dollar_rate = get_rate()
funds_list = get_funds()

# Sidebar: إعدادات سريعة
st.sidebar.header("⚙️ إعدادات النظام")
st.sidebar.info(f"سعر صرف الدولار الحالي: {dollar_rate:,.0f} ل.ل")

# 4. تبويبات البرنامج الرئيسية
tab1, tab2, tab3 = st.tabs(["📝 إدخال حركة مالية", "📊 كشف الحسابات والقيود", "⚙️ إدارة الصناديق والموظفين"])

# --- التبويب الأول: إدخال سند ---
with tab1:
    st.subheader("إضافة سند (قبض / صرف)")
    
    col1, col2 = st.columns(2)
    with col1:
        trans_type = st.radio("نوع الحركة", ["قبض (إيراد)", "صرف (مصروف)"], horizontal=True)
        fund = st.selectbox("الصندوق المستهدف", funds_list)
        date_val = st.date_input("التاريخ", datetime.now())
        account_type = st.selectbox("تصنيف الحساب", ["تبرعات", "سلفة / ذمة", "صيانة ومصاريف", "رواتب", "أخرى"])

    with col2:
        amount_usd = st.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0)
        amount_lbp = st.number_input("المبلغ بالليرة اللبنانية (ل.ل)", min_value=0, step=50000)
        ref_name = st.text_input("اسم الجهة / الشخص (اختياري)")
        description = st.text_area("البيان / التفاصيل")

    # حساب الإجمالي المعادل بالدولار
    total_usd = amount_usd + (amount_lbp / dollar_rate if dollar_rate > 0 else 0)
    st.write(f"**إجمالي الحركة بالدولار:** `${total_usd:,.2f}`")

    if st.button("💾 حفظ السند", type="primary", use_container_width=True):
        if total_usd <= 0:
            st.warning("يرجى إدخال مبلغ أكبر من الصفر.")
        else:
            payload = {
                "date": str(date_val),
                "description": description,
                "type": trans_type,
                "amount_usd": amount_usd,
                "amount_lbp": amount_lbp,
                "total_usd": total_usd,
                "fund": fund,
                "account_type": account_type,
                "ref_name": ref_name
            }
            supabase.table("transactions").insert(payload).execute()
            st.success("تم حفظ السند في السحابة بنجاح! 🎉")
            st.cache_data.clear()

# --- التبويب الثاني: عرض البيانات ---
with tab2:
    st.subheader("📜 جدول القيود المالية")
    try:
        res = supabase.table("transactions").select("*").order("id", desc=True).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            cols_order = ["id", "date", "type", "fund", "account_type", "amount_usd", "amount_lbp", "total_usd", "ref_name", "description"]
            df = df[[c for c in cols_order if c in df.columns]]
            df.rename(columns={
                "id": "رقم السند",
                "date": "التاريخ",
                "type": "النوع",
                "fund": "الصندوق",
                "account_type": "التصنيف",
                "amount_usd": "المبلغ ($)",
                "amount_lbp": "المبلغ (ل.ل)",
                "total_usd": "الإجمالي ($)",
                "ref_name": "الاسم",
                "description": "البيان"
            }, inplace=True)
            
            st.dataframe(df, use_container_width=True)
        else:
            st.info("لا توجد قيود مسجلة حتى الآن.")
    except Exception as e:
        st.error("جاري تحميل البيانات...")

# --- التبويب الثالث: إدارة الصناديق ---
with tab3:
    st.subheader("➕ إضافة صندوق جديد")
    new_fund = st.text_input("اسم الصندوق الجديد")
    if st.button("إضافة الصندوق"):
        if new_fund:
            try:
                supabase.table("funds").insert({"name": new_fund}).execute()
                st.success(f"تمت إضافة {new_fund} بنجاح!")
                st.cache_data.clear()
            except Exception:
                st.error("الصندوق موجود مسبقاً أو حدث خطأ.")
