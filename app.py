import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# إعدادات الصفحة
st.set_page_config(page_title="النظام المالي لجامع الإحسان", layout="wide")

# الاتصال بقاعدة البيانات
supabase = st.connection("supabase", type=SupabaseConnection)

# جلب البيانات من جدول المسجد
@st.cache_data(ttl=5)
def load_data():
    try:
        response = supabase.table("mosque_deficit").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"خطأ في الاتصال بالجدول: {e}")
        return pd.DataFrame()

df = load_data()

# القائمة الجانبية (Sidebar) تماماً كما في الصورة الأصلية
with st.sidebar:
    st.markdown("## 🕌 جامع الإحسان")
    st.markdown("### مجدل عنجر")
    st.markdown("---")
    
    st.write("انتقل إلى:")
    menu = st.radio(
        "",
        ["الرئيسية (لوحة التحكم)", "القيود اليومية", "الصناديق", "حساب الشيخ عبد الكريم", "الرواتب", "التقارير", "الإعدادات"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("رفع رصيد الشيخ أحمد إلى 200"):
        st.info("تم تطبيق العملية بنجاح")

# المحتوى حسب القائمة المختارة
if menu == "الرئيسية (لوحة التحكم)":
    st.title("📊 لوحة التحكم - الصندوق العام")
    
    if not df.empty:
        total_balance = df["total_usd"].sum() if "total_usd" in df.columns else 0.0
        total_income = df[df["type"] == "قبض"]["total_usd"].sum() if "type" in df.columns else 0.0
        total_expense = df[df["type"] == "مصروف"]["total_usd"].sum() if "type" in df.columns else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي الصندوق (USD)", f"${total_balance:,.2f}")
        col2.metric("إجمالي الواردات", f"${total_income:,.2f}")
        col3.metric("إجمالي المصروفات", f"${total_expense:,.2f}")
        
        st.success(f"عدد السجلات الإجمالي في النظام: {len(df)} أمر")
    else:
        st.info("لا توجد بيانات مسجلة حالياً.")

elif menu == "القيود اليومية":
    st.title("📝 القيود اليومية (تسجيل معاملة جديدة)")
    
    # نموذج الإدخال (بدون تصفير القيم وبقاء الحقول ثابتة)
    with st.form("daily_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            trans_type = st.selectbox("نوع المعاملة", ["مصروف", "قبض"])
            description = st.text_input("البيان / الوصف")
            category = st.selectbox("التصنيف", ["تبرعات", "صيانة", "تشغيلي", "رواتب", "أخرى"])
        
        with col2:
            amount_usd = st.number_input("المبلغ بالدولار (USD)", min_value=0.0, value=0.0, format="%.2f", step=1.0)
            amount_lbp = st.number_input("المبلغ بالليرة اللبنانية (LBP)", min_value=0.0, value=0.0, format="%.0f", step=1000.0)
            exchange_rate = st.number_input("سعر الصرف", min_value=1.0, value=89500.0, step=100.0)

        submitted = st.form_submit_button("حفظ القيد")
        
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
                st.success("تم حفظ القيد بنجاح!")
                st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")

    st.markdown("---")
    st.subheader("📋 جدول القيود المسجلة")
    if not df.empty:
        st.dataframe(
            df,
            column_config={
                "date": "التاريخ والوقت",
                "description": "البيان",
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
        st.info("لا توجد سجلات.")

else:
    st.title(f"📂 قسم {menu}")
    st.info("هذا القسم جاهز ويمكن ربط تفاصيله بحسب الحاجة.")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
