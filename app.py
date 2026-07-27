import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# 1. إعداد الصفحة
st.set_page_config(page_title="النظام المالي للمسجد والمركز الإسلامي", layout="wide", page_icon="🕌")

@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

st.title("🕌 النظام المالي للمسجد والمركز الإسلامي")

# 2. دوال جلب البيانات من السحابة
def load_transactions():
    try:
        res = supabase.table("transactions").select("*").order("id", desc=True).execute()
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def load_funds():
    try:
        res = supabase.table("funds").select("name").execute()
        if res.data:
            return [r["name"] for r in res.data]
    except Exception:
        pass
    return [
        "صندوق المسجد العام", 
        "صندوق بناء المركز الإسلامي", 
        "مشروع المقبرة", 
        "صندوق الزكاة والصدقات", 
        "مشروع الطاقة الشمسية والكهرباء", 
        "ذمة وسلف الشيخ عبد الكريم"
    ]

def get_dollar_rate():
    try:
        res = supabase.table("settings").select("value").eq("key", "dollar_rate").execute()
        if res.data and len(res.data) > 0:
            return float(res.data[0]["value"])
    except Exception:
        pass
    return 89500.0

dollar_rate = get_dollar_rate()
funds_list = load_funds()

# الشريط الجانبي للإحصائيات السريعة
st.sidebar.header("⚙️ حالة النظام")
st.sidebar.info(f"💵 سعر صرف الدولار: **{dollar_rate:,.0f} ل.ل**")

# 3. التبويبات الرئيسية المعتادة
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 الحركة اليومية (السندات)", 
    "📦 الصناديق والمشاريع", 
    "📊 التقرير المالي والشامل", 
    "⚙️ إعدادات النظام"
])

# --- التبويب الأول: الحركة اليومية ---
with tab1:
    st.subheader("إدخال حركة مالية جديدة (قبض / صرف)")
    
    col1, col2 = st.columns(2)
    with col1:
        trans_type = st.radio("نوع الحركة", ["قبض (إيراد)", "صرف (مصروف)"], horizontal=True)
        fund = st.selectbox("الصندوق / المشروع", funds_list)
        account_type = st.selectbox(
            "تصنيف الحساب", 
            ["تبرعات واشتراكات", "زكاة أموال / فطرة", "صدقات وكفارات", "صيانة وتشغيل", "رواتب ومكافآت", "سلفة / استرداد", "مشتريات ومعدات", "عامة"]
        )
        date_val = st.date_input("تاريخ السند", datetime.now())

    with col2:
        amount_usd = st.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0)
        amount_lbp = st.number_input("المبلغ بالليرة (ل.ل)", min_value=0, step=50000)
        ref_name = st.text_input("اسم المتبرع / المستفيد / الجهة (اختياري)")
        description = st.text_area("البيان / تفاصيل الملاحظات")

    total_in_usd = amount_usd + (amount_lbp / dollar_rate if dollar_rate > 0 else 0)
    st.write(f"💵 **إجمالي القيمة المعادلة بالدولار:** `${total_in_usd:,.2f}`")

    if st.button("💾 حفظ السند", type="primary", use_container_width=True):
        if total_in_usd <= 0:
            st.warning("يرجى إدخال مبلغ أكبر من الصفر.")
        else:
            payload = {
                "date": str(date_val),
                "description": description,
                "type": trans_type,
                "amount_usd": amount_usd,
                "amount_lbp": amount_lbp,
                "total_usd": total_in_usd,
                "fund": fund,
                "account_type": account_type,
                "ref_name": ref_name
            }
            try:
                supabase.table("transactions").insert(payload).execute()
                st.success("تم حفظ السند بنجاح! 🎉")
            except Exception:
                st.error("حدث خطأ أثناء الاتصال بالسحابة.")

    st.divider()
    st.subheader("📋 سجل الحركات اليومية الأخير")
    df = load_transactions()
    if not df.empty:
        cols = {"id": "رقم السند", "date": "التاريخ", "type": "النوع", "fund": "الصندوق", "account_type": "التصنيف", "amount_usd": "المبلغ ($)", "amount_lbp": "المبلغ (ل.ل)", "total_usd": "الإجمالي ($)", "ref_name": "الاسم", "description": "البيان"}
        st.dataframe(df[[c for c in cols.keys() if c in df.columns]].rename(columns=cols), use_container_width=True)
    else:
        st.info("لا توجد قيود مسجلة بعد.")

# --- التبويب الثاني: الصناديق والمشاريع ---
with tab2:
    st.subheader("📦 أرصدة الصناديق والمشاريع")
    df = load_transactions()
    if not df.empty and "fund" in df.columns and "total_usd" in df.columns:
        # حساب صافي كل صندوق
        df['net'] = df.apply(lambda r: r['total_usd'] if r['type'] == 'قبض (إيراد)' else -r['total_usd'], axis=1)
        summary = df.groupby('fund')['net'].sum().reset_index()
        summary.columns = ['اسم الصندوق / المشروع', 'الرصيد الحالي ($)']
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("لا توجد عمليات كافية لحساب أرصدة الصناديق.")

# --- التبويب الثالث: التقرير المالي ---
with tab3:
    st.subheader("📊 ملخص التقرير المالي الشامل")
    df = load_transactions()
    if not df.empty:
        total_in = df[df['type'] == 'قبض (إيراد)']['total_usd'].sum() if 'type' in df.columns else 0
        total_out = df[df['type'] == 'صرف (مصروف)']['total_usd'].sum() if 'type' in df.columns else 0
        net_balance = total_in - total_out

        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي الإيرادات ($)", f"${total_in:,.2f}")
        c2.metric("إجمالي المصروفات ($)", f"${total_out:,.2f}")
        c3.metric("صافي رصيد النظام ($)", f"${net_balance:,.2f}")
    else:
        st.info("لا توجد بيانات كافية لإصدار التقرير.")

# --- التبويب الرابع: إعدادات النظام ---
with tab4:
    st.subheader("⚙️ إعدادات الصناديق وسعر الصرف")
    
    st.write("#### 1. تحديث سعر صرف الدولار")
    new_rate = st.number_input("سعر الصرف الجديد (ل.ل)", value=float(dollar_rate), step=500.0)
    if st.button("تحديث سعر الصرف"):
        try:
            supabase.table("settings").upsert({"key": "dollar_rate", "value": str(new_rate)}).execute()
            st.success("تم تحديث سعر الصرف بنجاح!")
        except Exception:
            st.error("تعذر تحديث سعر الصرف.")

    st.divider()
    st.write("#### 2. إضافة صندوق أو مشروع جديد")
    new_fund_name = st.text_input("اسم الصندوق/المشروع الجديد")
    if st.button("إضافة الصندوق"):
        if new_fund_name:
            try:
                supabase.table("funds").insert({"name": new_fund_name}).execute()
                st.success(f"تمت إضافة {new_fund_name} بنجاح!")
            except Exception:
                st.error("الصندوق موجود مسبقاً أو تعذر إضافته.")
