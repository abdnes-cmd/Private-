import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="إدارة الصناديق المالية", layout="wide")

st.title("📊 نظام إدارة الصناديق المالية (المسجد والشخصي)")

# محاكاة قاعدة البيانات (يمكنك استبدالها باتصال قاعدة البيانات الفعلية لديك)
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'id', 'date', 'section', 'type', 'category', 'amount', 'notes'
    ])

# ==================== الشريط الجانبي (Sidebar) ====================
st.sidebar.header("⚙️ لوحة التحكم والإدخال")

# اختيار القسم الرئيسي
active_section = st.sidebar.selectbox(
    "اختر الصندوق / القسم:",
    ["صندوق المسجد", "الصندوق الشخصي"]
)

st.sidebar.markdown("---")
st.sidebar.subheader(f"إضافة معاملة جديدة إلى: {active_section}")

with st.sidebar.form("transaction_form"):
    trans_type = st.selectbox("نوع الحركة", ["إيراد", "مصروف"])
    
    # تغيير التصنيفات بناءً على القسم المختار
    if active_section == "صندوق المسجد":
        categories = ["تبرعات", "رواتب", "صيانة واستهلاكيات", "أخرى"]
    else:
        categories = ["دخل شخصي", "مصروفات معيشية", "فواتير", "أخرى"]
        
    category = st.selectbox("التصنيف الفرعي", categories)
    amount = st.number_input("المبلغ", min_value=0.0, step=0.5)
    date = st.date_input("التاريخ", datetime.today())
    notes = st.text_area("ملاحظات")
    
    submit_button = st.form_submit_button("حفظ المعاملة")
    
    if submit_button:
        new_row = {
            'id': len(st.session_state.data) + 1,
            'date': str(date),
            'section': active_section,
            'type': trans_type,
            'category': category,
            'amount': amount,
            'notes': notes
        }
        # إضافة السطر للبيانات (في التطبيق الحقيقي سيتم حفظها في قاعدة البيانات السحابية)
        st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
        st.sidebar.success("تم الحفظ بنجاح!")

# ==================== العرض الرئيسي للبيانات ====================
st.header(f"عرض بيانات: {active_section}")

# تصفية البيانات حسب القسم المختار حالياً
df = st.session_state.data
section_df = df[df['section'] == active_section] if not df.empty else df

if not section_df.empty:
    # حساب الإجماليات
    total_income = section_df[section_df['type'] == 'إيراد']['amount'].sum()
    total_expense = section_df[section_df['type'] == 'مصروف']['amount'].sum()
    net_balance = total_income - total_expense
    
    # عرض مؤشرات سريعة (Metrics)
    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الإيرادات", f"{total_income:,.2f}")
    col2.metric("إجمالي المصروفات", f"{total_expense:,.2f}")
    col3.metric("الرصيد الحالي", f"{net_balance:,.2f}", delta=f"{net_balance:,.2f}")
    
    st.markdown("---")
    
    # عرض جدول المعاملات
    st.subheader("سجل المعاملات")
    st.dataframe(section_df, use_container_width=True)
else:
    st.info(f"لا توجد بيانات مسجلة حتى الآن في {active_section}. استخدم القائمة الجانبية لإضافة أول معاملة.")

# ==================== تقرير عام شامل (اختياري) ====================
with st.expander("📈 عرض تقرير شامل للمنظومة (المسجد والشخصي معاَ)"):
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("لا توجد بيانات متاحة.")
