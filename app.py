import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# إعدادات الصفحة
st.set_page_config(page_title="نظام الحسابات المالية", layout="wide")

# الاتصال بقاعدة البيانات
supabase = st.connection("supabase", type=SupabaseConnection)

# جلب البيانات من الجدول الصحيح mosque_deficit
@st.cache_data(ttl=5)
def load_mosque_data():
    try:
        response = supabase.table("mosque_deficit").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"خطأ في الاتصال بالجدول: {e}")
        return pd.DataFrame()

df_mosque = load_mosque_data()

# العنوان الرئيسي
st.title("🕌 نظام إدارة حسابات المسجد والحساب الشخصي")

# 1. ملخص صندوق المسجد العام (في الأعلى)
st.markdown("---")
st.subheader("📊 ملخص صندوق المسجد العام")

if not df_mosque.empty:
    total_balance = df_mosque["total_usd"].sum() if "total_usd" in df_mosque.columns else 0.0
    total_income = df_mosque[df_mosque["type"] == "قبض"]["total_usd"].sum() if "type" in df_mosque.columns else 0.0
    total_expense = df_mosque[df_mosque["type"] == "مصروف"]["total_usd"].sum() if "type" in df_mosque.columns else 0.0

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("إجمالي الصندوق (USD)", f"${total_balance:,.2f}")
    col_m2.metric("إجمالي الواردات / التبرعات", f"${total_income:,.2f}")
    col_m3.metric("إجمالي المصروفات", f"${total_expense:,.2f}")
    
    st.info(f"عدد السجلات المعروضة: {len(df_mosque)} أمر")
else:
    st.info("جاري تحميل بيانات المسجد أو لا توجد سجلات بعد.")

st.markdown("---")

# 2. إضافة معاملة جديدة للمسجد (بدون أي تصفير للقيم)
st.subheader("➕ تسجيل معاملة جديدة للمسجد")

with st.form("mosque_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    
    with col1:
        trans_type = st.selectbox("نوع المعاملة", ["مصروف", "قبض"])
        description = st.text_input("البيان / التفاصيل")
        category = st.selectbox("التصنيف", ["تبرعات", "صيانة ومرافق", "تشغيلي", "رواتب ومستحقات", "أخرى"])
    
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
            supabase.table("mosque_deficit").insert(new_record).execute()
            st.success("تم حفظ المعاملة بنجاح!")
            st.rerun()
        except Exception as e:
            st.error(f"حدث خطأ أثناء الحفظ: {e}")

# 3. جدول معاملات المسجد المفصلة (ملون وواضح)
st.markdown("---")
st.subheader("📋 جدول حركة حسابات المسجد المفصلة")

if not df_mosque.empty:
    st.dataframe(
        df_mosque,
        column_config={
            "date": "التاريخ والوقت",
            "description": "البيان / الوصف",
            "type": "النوع",
            "amount_usd": st.column_config.NumberColumn("المبلغ ($)", format="$%.2f"),
            "amount_lbp": st.column_config.NumberColumn("المبلغ (ل.ل)", format="LBP %,.0f"),
            "total_usd": st.column_config.NumberColumn("الصافي ($)", format="$%.2f"),
            "category": "التصنيف"
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("لا توجد سجلات معروضة حالياً.")
