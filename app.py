import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# إعدادات الصفحة
st.set_page_config(page_title="مدير المعاملات المالية", layout="wide")

# الاتصال بقاعدة البيانات
supabase = st.connection("supabase", type=SupabaseConnection)

# جلب البيانات من الجدول
@st.cache_data(ttl=10)
def load_data():
    response = supabase.table("personal_transactions").select("*").execute()
    return pd.DataFrame(response.data)

try:
    df = load_data()
except Exception:
    df = pd.DataFrame(columns=["date", "description", "type", "amount_usd", "amount_lbp", "total_usd", "category"])

# العنوان الرئيسي
st.title("💰 نظام إدارة المعاملات المالية")

# 1. قسم الصندوق وملخص الحسابات (في الأعلى)
st.markdown("---")
st.subheader("📊 ملخص الصندوق العام")

if not df.empty and "total_usd" in df.columns:
    total_balance = df["total_usd"].sum()
    total_income = df[df["type"] == "قبض"]["total_usd"].sum() if "type" in df.columns else 0
    total_expense = df[df["type"] == "مصروف"]["total_usd"].sum() if "type" in df.columns else 0
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("إجمالي الصندوق (USD)", f"${total_balance:,.2f}")
    col_m2.metric("إجمالي الواردات", f"${total_income:,.2f}")
    col_m3.metric("إجمالي المصروفات", f"${total_expense:,.2f}")
else:
    st.info("لا توجد بيانات مالية مسجلة حتى الآن.")

st.markdown("---")

# 2. إدخال معاملة جديدة (بدون تصفير الحقول وبقاء القيم ثابتة)
st.subheader("➕ إضافة معاملة جديدة")

with st.form("transaction_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        trans_type = st.selectbox("نوع المعاملة", ["مصروف", "قبض"])
        description = st.text_input("البيان / الوصف")
        category = st.selectbox("التصنيف", ["عام", "تشغيلي", "تبرعات", "صيانة", "أخرى"])
    
    with col2:
        amount_usd = st.number_input("المبلغ بالدولار (USD)", min_value=0.0, value=0.0, format="%.2f", step=1.0)
        amount_lbp = st.number_input("المبلغ بالليرة اللبنانية (LBP)", min_value=0.0, value=0.0, format="%.0f", step=1000.0)
        exchange_rate = st.number_input("سعر الصرف (LBP مقابل 1 USD)", min_value=1.0, value=89500.0, step=100.0)

    submitted = st.form_submit_button("حفظ المعاملة")
    
    if submitted:
        calculated_usd_from_lbp = amount_lbp / exchange_rate if exchange_rate > 0 else 0.0
        total_in_usd = amount_usd + calculated_usd_from_lbp
        
        final_total = -total_in_usd if trans_type == "مصروف" else total_in_usd
        
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "description": description if description else "بدون بيان",
            "type": trans_type,
            "amount_usd": amount_usd,
            "amount_lbp": amount_lbp,
            "total_usd": final_total,
            "category": category
        }
        
        try:
            supabase.table("personal_transactions").insert(new_record).execute()
            st.success("تم بنجاح حفظ المعاملة!")
            st.rerun()
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحفظ: {e}")

# 3. تنظيم وعرض المعاملات بجدول ملون وواضح (تحت الصندوق)
st.markdown("---")
st.subheader("📋 جدول المعاملات المفصلة")

if not df.empty:
    st.dataframe(
        df,
        column_config={
            "date": "التاريخ والوقت",
            "description": "البيان",
            "type": "النوع",
            "amount_usd": st.column_config.NumberColumn("المبلغ ($)", format="$%.2f"),
            "amount_lbp": st.column_config.NumberColumn("المبلغ (ل.ل)", format="LBP %,.0f"),
            "total_usd": st.column_config.NumberColumn("الإجمالي المصفى ($)", format="$%.2f"),
            "category": "التصنيف"
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("لا توجد سجلات لعرضها في الجدول حالياً.")
