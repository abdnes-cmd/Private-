import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# إعدادات الصفحة والهوية البصرية (الأخضر والذهبي)
st.set_page_config(page_title="النظام المالي للمسجد", page_icon="🕌", layout="wide")

# تصميم مخصص بالألوان المطلوبة
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    h1, h2, h3 { color: #004D40; font-family: 'Cairo', sans-serif; }
    .stButton>button { background-color: #004D40; color: #D4AF37; border-radius: 5px; }
    .stButton>button:hover { background-color: #D4AF37; color: #004D40; }
    .reportview-container .main .block-container{ padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# الاتصال بقاعدة البيانات وإنشاء الجداول إن لم تكن موجودة
conn = sqlite3.connect('mosque_finance.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS funds (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
c.execute('''CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, salary REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                date TEXT, 
                description TEXT, 
                type TEXT, 
                amount REAL, 
                fund TEXT, 
                account_type TEXT, 
                ref_name TEXT)''')

# إدخال بيانات افتراضية إذا كانت الجداول فارغة
c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '1.0')")
for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# --- القائمة الجانبية للتنقل ---
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>🕌 إدارة المسجد</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"])

# قراءة الإعدادات الحالية
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
dollar_rate = float(c.fetchone()[0])

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #C5A059;'>متابعة دقيقة لأرصدة وحسابات المسجد</p>", unsafe_allow_html=True)
    st.write("---")
    
    # حساب الإجماليات
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    if not df_trans.empty:
        total_in = df_trans[df_trans['type'] == 'قبض']['amount'].sum()
        total_out = df_trans[df_trans['type'] == 'صرف']['amount'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 الرصيد الإجمالي الحالي", f"{current_balance:,.2f}")
    col2.metric("🟢 إجمالي الإيرادات", f"{total_in:,.2f}")
    col3.metric("🔴 إجمالي المصروفات", f"{total_out:,.2f}")
    
    st.write("---")
    st.subheader("📌 أرصدة الصناديق الحالية")
    # عرض سريع للصناديق
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['amount'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['amount'].sum()
        fund_balances.append({"الصندوق": f, "الرصيد الحالي": f_in - f_out})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    
    # جلب الصناديق والموظفين للقوائم المنسدلة
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    
    # رقم السند التلقائي
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    next_id = (max_id + 1) if max_id else 1
    
    st.info(f"رقم السند التلقائي القادم: {next_id}")
    
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        t_date = col1.date_input("التاريخ", datetime.now())
        t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])
        
        amount = col1.number_input("المبلغ", min_value=0.0, step=50.0)
        fund = col2.selectbox("الصندوق المتأثر", funds_list)
        
        account_type = col1.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])
        
        ref_name = ""
        if account_type == "رواتب الموظفين":
            ref_name = col2.selectbox("اختر الموظف", emp_list)
            
        description = st.text_area("البيان / تفاصيل القيد")
        
        submit = st.form_submit_command("حفظ السند")
        if submit:
            if amount <= 0 or not description:
                st.error("الرجاء إدخال مبلغ صحيح وبيان للعملية.")
            else:
                c.execute("INSERT INTO transactions (date, description, type, amount, fund, account_type, ref_name) VALUES (?,?,?,?,?,?,?)",
                          (str(t_date), description, t_type, amount, fund, account_type, ref_name))
                conn.commit()
                st.success(f"تم حفظ السند رقم {next_id} بنجاح!")
                st.rerun()

    # عرض العمليات الأخيرة مع التلوين
    st.write("---")
    st.subheader("📋 القيود المسجلة مؤخراً")
    df_all = pd.read_sql_query("SELECT id AS 'رقم السند', date AS 'التاريخ', description AS 'البيان', type AS 'النوع', amount AS 'المبلغ', fund AS 'الصندوق' FROM transactions ORDER BY id DESC", conn)
    
    def color_type(val):
        color = '#e8f5e9' if val == 'قبض' else '#ffebee'
        return f'background-color: {color}'
    
    if not df_all.empty:
        st.dataframe(df_all.style.applymap(color_type, subset=['النوع']))
    else:
        st.caption("لا توجد قيود مسجلة بعد.")

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['amount'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['amount'].sum()
        records.append({
            "اسم الصندوق": f,
            "إجمالي القبض (+)": f_in,
            "إجمالي الصرف (-)": f_out,
            "الرصيد الحالي": f_in - f_out
        })
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم مع المسجد")
    
    df_sheikh = pd.read_sql_query("SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', amount AS 'المبلغ' FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'", conn)
    
    sheikh_in = df_sheikh[df_sheikh['النوع'] == 'قبض']['المبلغ'].sum() # ما قبضه المسجد من الشيخ (له)
    sheikh_out = df_sheikh[df_sheikh['النوع'] == 'صرف']['المبلغ'].sum() # ما صرفه المسجد للشيخ (عليه)
    
    final_status = sheikh_in - sheikh_out
    
    if final_status > 0:
        st.success(f"⚖️ ميزان الحساب: **المسجد مدين لك بمبلغ {abs(final_status):,.2f}** (لك على المسجد)")
    elif final_status < 0:
        st.warning(f"⚖️ ميزان الحساب: **أنت مدين للمسجد بمبلغ {abs(final_status):,.2f}** (عليك للمسجد)")
    else:
        st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً (0.00)")
        
    st.write("---")
    st.dataframe(df_sheikh)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين")
    
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
    
    emp_records = []
    for idx, row in df_emps.iterrows():
        emp_name = row['name']
        required = row['salary']
        paid = df_trans[(df_trans['ref_name'] == emp_name) & (df_trans['type'] == 'صرف')]['amount'].sum()
        emp_records.append({
            "اسم الموظف": emp_name,
            "الراتب المستحق": required,
            "المدفوع": paid,
            "المتبقي": required - paid
        })
        
    if emp_records:
        st.table(pd.DataFrame(emp_records))
    else:
        st.caption("لم يتم إضافة موظفين في صفحة الإعدادات بعد.")

# --- 6. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة")
    
    rep_type = st.selectbox("نوع التقرير", ["يومي", "شهري", "سنوي"])
    df_report = pd.read_sql_query("SELECT * FROM transactions", conn)
    
    if not df_report.empty:
        df_report['date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي":
            target_date = st.date_input("اختر اليوم", datetime.now())
            df_filtered = df_report[df_report['date'].dt.date == target_date]
        elif rep_type == "شهري":
            month = st.slider("اختر الشهر", 1, 12, int(datetime.now().month))
            df_filtered = df_report[df_report['date'].dt.month == month]
        else:
            year = st.number_input("اختر السنة", min_value=2020, max_value=2030, value=int(datetime.now().year))
            df_filtered = df_report[df_report['date'].dt.year == year]
            
        st.write(df_filtered)
        st.button("🖨️ طباعة (استخدم ميزة طباعة المتصفح لـ PDF)")
    else:
        st.caption("لا توجد بيانات لتوليد التقارير.")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    
    # 1. سعر الصرف
    new_rate = st.number_input("سعر صرف الدولار الحالي", value=dollar_rate, step=0.1)
    if st.button("تحديث سعر الصرف"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success("تم تحديث السعر!")
        
    st.write("---")
    # 2. إضافة صندوق
    st.subheader("➕ إضافة صندوق جديد")
    new_fund = st.text_input("اسم الصندوق الجديد")
    if st.button("حفظ الصندوق"):
        if new_fund:
            try:
                c.execute("INSERT INTO funds (name) VALUES (?)", (new_fund,))
                conn.commit()
                st.success(f"تمت إضافة صندوق {new_fund}")
                st.rerun()
            except:
                st.error("الصندوق موجود مسبقاً")
                
    st.write("---")
    # 3. إضافة موظف
    st.subheader("➕ إضافة موظف جديد")
    col1, col2 = st.columns(2)
    emp_name = col1.text_input("اسم الموظف")
    emp_salary = col2.number_index = col2.number_input("الراتب الشهري", min_value=0.0)
    if st.button("حفظ الموظف"):
        if emp_name:
            c.execute("INSERT INTO employees (name, salary) VALUES (?,?)", (emp_name, emp_salary))
            conn.commit()
            st.success(f"تمت إضافة الموظف {emp_name}")
            st.rerun()
