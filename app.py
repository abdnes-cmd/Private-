import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3

st.set_page_config(page_title="الحساب الشخصي", layout="wide")

# ==================== إعداد قاعدة البيانات الشخصية ====================
def init_db():
    conn = sqlite3.connect('personal_finance.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            category TEXT,
            amount REAL,
            notes TEXT
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

st.title("👤 نظام إدارة الحساب الشخصي (على السحابة)")

# ==================== الشريط الجانبي (الإدخال) ====================
st.sidebar.header("⚙️ لوحة التحكم والإدخال الشخصي")

with st.sidebar.form("personal_form", clear_on_submit=True):
    trans_type = st.selectbox("نوع الحركة", ["إيراد", "مصروف"])
    categories = ["دخل/راتب", "مصروفات معيشية", "فواتير", "تعديل رصيد / تسوية", "أخرى"]
    category = st.selectbox("التصنيف", categories)
    amount = st.number_input("المبلغ", min_value=0.0, step=0.5)
    date = st.date_input("التاريخ", datetime.today())
    notes = st.text_area("ملاحظات")
    
    submit_button = st.form_submit_button("حفظ المعاملة")
    
    if submit_button:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (date, type, category, amount, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (str(date), trans_type, category, amount, notes))
        conn.commit()
        st.sidebar.success("تم الحفظ بنجاح!")
        st.rerun()

# ==================== قراءة البيانات وعرضها ====================
query = "SELECT * FROM transactions"
df = pd.read_sql(query, conn)

# زر إضافي لضبط رصيد الشيخ أحمد ليكون 200 دولار (إذا لم تقم بإضافته مسبقاً)
st.sidebar.markdown("---")
if st.sidebar.button("رفع رصيد الشيخ أحمد إلى 200$ (إضافة تسوية 50$)"):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (date, type, category, amount, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (str(datetime.today().date()), "إيراد", "تعديل رصيد / تسوية", 50.0, "رفع رصيد الشيخ أحمد من 150 إلى 200 دولار"))
    conn.commit()
    st.sidebar.success("تم تعديل الرصيد بنجاح وأصبح 200$ مع الحفاظ على السجل القديم!")
    st.rerun()

# حساب الإجماليات
if not df.empty:
    total_income = df[df['type'] == 'إيراد']['amount'].sum()
    total_expense = df[df['type'] == 'مصروف']['amount'].sum()
    net_balance = total_income - total_expense
else:
    total_income = 0.0
    total_expense = 0.0
    net_balance = 0.0

# عرض المؤشرات المالية
col1, col2, col3 = st.columns(3)
col1.metric("إجمالي الإيرادات", f"{total_income:,.2f} $")
col2.metric("إجمالي المصروفات", f"{total_expense:,.2f} $")
col3.metric("الرصيد الحالي", f"{net_balance:,.2f} $")

st.markdown("---")

# عرض جدول المعاملات
st.subheader("سجل الحركات الشخصية")
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد حركات مسجلة بعد في الحساب الشخصي.")
