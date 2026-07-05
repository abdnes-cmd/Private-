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

# تم إصلاح القوس الزائد هنا تماماً ليعمل السكربت بنجاح
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                date TEXT, 
                description TEXT, 
                type TEXT, 
                amount_usd REAL,
                amount_lbp REAL,
                total_usd REAL, 
                fund TEXT, 
                account_type TEXT, 
                ref_name TEXT)''')

# التأكد من وجود سعر الصرف الصحيح في الإعدادات
c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '89500')")
for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# قراءة إعداد سعر الصرف الحالي من قاعدة البيانات بشكل مباشر وثابت
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
dollar_rate = float(c.fetchone()[0])

# --- القائمة الجانبية للتنقل ---
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>🕌 إدارة المسجد</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"])

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.لبنانية للدولار</p>", unsafe_allow_html=True)
    st.write("---")
    
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    if not df_trans.empty:
        total_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
        total_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 الرصيد الإجمالي الحالي ($)", f"${current_balance:,.2f}")
    col2.metric("🟢 إجمالي الإيرادات ($)", f"${total_in:,.2f}")
    col3.metric("🔴 إجمالي المصروفات ($)", f"${total_out:,.2f}")
    
    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية بالدولار")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        fund_balances.append({"الصندوق": f, "الرصيد الحالي بالدولار ($)": f"${f_in - f_out:,.2f}"})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية (يدعم الدولار واللبناني)")
    st.caption(f"💡 سعر الصرف المعتمد حالياً للتحويل: {dollar_rate:,.0f} ل.ل")
    
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    next_id = (max_id + 1) if max_id else 1
    
    st.info(f"رقم السند التلقائي القادم: {next_id}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now())
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])
    
    usd_amount = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=10.0, value=0.0, key="usd_input")
    lbp_amount = col2.number_input("المبلغ بالليرة اللبنانية (ل.ل)", min_value=0.0, step=100000.0, value=0.0, key="lbp_input")
    
    if dollar_rate > 0:
        converted_instant = lbp_amount / dollar_rate
    else:
        converted_instant = 0.0
        
    total_calculated_usd = usd_amount + converted_instant
    
    if lbp_amount > 0:
        st.warning(f"🔄 **تحويل فوري دقيق:** {lbp_amount:,.0f} ل.ل = **${converted_instant:,.2f}** | إجمالي السند بالكامل: **${total_calculated_usd:,.2f}**")
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list)
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        ref_name = st.selectbox("اختر الموظف", emp_list)
        
    description = st.text_area("البيان / تفاصيل القيد")
    
    if st.button("حفظ السند المالي"):
        if usd_amount == 0 and lbp_amount == 0:
            st.error("الرجاء إدخال قيمة في حقل الدولار أو اللبناني على الأقل.")
        elif not description:
            st.error("الرجاء إدخال بيان للعملية.")
        else:
            c.execute("""INSERT INTO transactions 
                         (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success(f"تم حفظ السند رقم {next_id} بنجاح! الإجمالي: ${total_calculated_usd:,.2f}")
            st.rerun()

    st.write("---")
    st.subheader("📋 القيود المسجلة مؤخراً")
    df_all = pd.read_sql_query("""SELECT id AS 'رقم السند', date AS 'التاريخ', description AS 'البيان', 
                                  type AS 'النوع', amount_usd AS 'دولار $', amount_lbp AS 'لبناني ل.ل', 
                                  total_usd AS 'الإجمالي ($)', fund AS 'الصندوق' 
                                  FROM transactions ORDER BY id DESC""", conn)
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)
    else:
        st.caption("لا توجد قيود مسجلة بعد.")

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق (بالدولار)")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        records.append({
            "اسم الصندوق": f,
            "إجمالي القبض ($)": f_in,
            "إجمالي الصرف ($)": f_out,
            "الرصيد الصافي ($)": f_in - f_out
        })
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم مع المسجد (بالدولار)")
    
    df_sheikh = pd.read_sql_query("""SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', 
                                     amount_usd AS 'دولار', amount_lbp AS 'لبناني', total_usd AS 'الإجمالي ($)' 
                                     FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'""", conn)
    
    sheikh_in = df_sheikh[df_sheikh['النوع'] == 'قبض']['الإجمالي ($)'].sum()
    sheikh_out = df_sheikh[df_sheikh['النوع'] == 'صرف']['الإجمالي ($)'].sum()
    
    final_status = sheikh_in - sheikh_out
    
    if final_status > 0:
        st.success(f"⚖️ ميزان الحساب: **المسجد مدين لك بمبلغ ${abs(final_status):,.2f}** (لك على المسجد)")
    elif final_status < 0:
        st.warning(f"⚖️ ميزان الحساب: **أنت مدين للمسجد بمبلغ ${abs(final_status):,.2f}** (عليك للمسجد)")
    else:
        st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً ($0.00)")
        
    st.write("---")
    st.dataframe(df_sheikh, use_container_width=True)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين (بالدولار)")
    
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
    
    emp_records = []
    for idx, row in df_emps.iterrows():
        emp_name = row['name']
        required = row['salary']
        paid = df_trans[(df_trans['ref_name'] == emp_name) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        emp_records.append({
            "اسم الموظف": emp_name,
            "الراتب المستحق ($)": required,
            "المدفوع إجمالاً ($)": paid,
            "المتبقي ($)": required - paid
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
        st.button("🖨️ طباعة")
    else:
        st.caption("لا توجد بيانات لتوليد التقارير.")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    
    new_rate = st.number_input("سعر صرف الدولار الحالي مقابل الليرة اللبنانية (مثال: 89500)", value=dollar_rate, step=500.0)
    if st.button("تحديث سعر الصرف"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success(f"تم تحديث السعر بنجاح إلى: {new_rate:,.0f} ل.ل")
        st.rerun()
        
    st.write("---")
    st.subheader("🚨 منطقة الخطر (إعادة تعيين قاعدة البيانات)")
    if st.button("🧹 تصفير وحذف جميع السندات المخربطة"):
        c.execute("DROP TABLE IF EXISTS transactions")
        conn.commit()
        st.success("تم مسح السندات القديمة بنجاح! يرجى إعادة تحديث الصفحة وبدء الإدخال.")
        st.rerun()
        
    st.write("---")
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
                ref_name TEXT)''')

# التأكد من وجود سعر الصرف الصحيح في الإعدادات
c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '89500')")
for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# قراءة إعداد سعر الصرف الحالي من قاعدة البيانات بشكل مباشر وثابت
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
dollar_rate = float(c.fetchone()[0])

# --- القائمة الجانبية للتنقل ---
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>🕌 إدارة المسجد</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"])

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.لبنانية للدولار</p>", unsafe_allow_html=True)
    st.write("---")
    
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    if not df_trans.empty:
        total_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
        total_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 الرصيد الإجمالي الحالي ($)", f"${current_balance:,.2f}")
    col2.metric("🟢 إجمالي الإيرادات ($)", f"${total_in:,.2f}")
    col3.metric("🔴 إجمالي المصروفات ($)", f"${total_out:,.2f}")
    
    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية بالدولار")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        fund_balances.append({"الصندوق": f, "الرصيد الحالي بالدولار ($)": f"${f_in - f_out:,.2f}"})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية (تصحيح المعاينة الحسابية الفورية) ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية (يدعم الدولار واللبناني)")
    st.caption(f"💡 سعر الصرف المعتمد حالياً للتحويل: {dollar_rate:,.0f} ل.ل")
    
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    next_id = (max_id + 1) if max_id else 1
    
    st.info(f"رقم السند التلقائي القادم: {next_id}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now())
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])
    
    usd_amount = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=10.0, value=0.0, key="usd_input")
    lbp_amount = col2.number_input("المبلغ بالليرة اللبنانية (ل.ل)", min_value=0.0, step=100000.0, value=0.0, key="lbp_input")
    
    # حساب قيمة اللبناني بالدولار بناءً على السعر الفعلي المكتوب (89500 مثلاً)
    if dollar_rate > 0:
        converted_instant = lbp_amount / dollar_rate
    else:
        converted_instant = 0.0
        
    total_calculated_usd = usd_amount + converted_instant
    
    # عرض المعاينة بشكل منسق وواضح وصحيح 100%
    if lbp_amount > 0:
        st.warning(f"🔄 **تحويل فوري دقيق:** {lbp_amount:,.0f} ل.ل = **${converted_instant:,.2f}** | إجمالي السند بالكامل: **${total_calculated_usd:,.2f}**")
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list)
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        ref_name = st.selectbox("اختر الموظف", emp_list)
        
    description = st.text_area("البيان / تفاصيل القيد")
    
    if st.button("حفظ السند المالي"):
        if usd_amount == 0 and lbp_amount == 0:
            st.error("الرجاء إدخال قيمة في حقل الدولار أو اللبناني على الأقل.")
        elif not description:
            st.error("الرجاء إدخال بيان للعملية.")
        else:
            c.execute("""INSERT INTO transactions 
                         (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success(f"تم حفظ السند رقم {next_id} بنجاح! الإجمالي: ${total_calculated_usd:,.2f}")
            st.rerun()

    st.write("---")
    st.subheader("📋 القيود المسجلة مؤخراً")
    df_all = pd.read_sql_query("""SELECT id AS 'رقم السند', date AS 'التاريخ', description AS 'البيان', 
                                  type AS 'النوع', amount_usd AS 'دولار $', amount_lbp AS 'لبناني ل.ل', 
                                  total_usd AS 'الإجمالي ($)', fund AS 'الصندوق' 
                                  FROM transactions ORDER BY id DESC""", conn)
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)
    else:
        st.caption("لا توجد قيود مسجلة بعد.")

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق (بالدولار)")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        records.append({
            "اسم الصندوق": f,
            "إجمالي القبض ($)": f_in,
            "إجمالي الصرف ($)": f_out,
            "الرصيد الصافي ($)": f_in - f_out
        })
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم مع المسجد (بالدولار)")
    
    df_sheikh = pd.read_sql_query("""SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', 
                                     amount_usd AS 'دولار', amount_lbp AS 'لبناني', total_usd AS 'الإجمالي ($)' 
                                     FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'""", conn)
    
    sheikh_in = df_sheikh[df_sheikh['النوع'] == 'قبض']['الإجمالي ($)'].sum()
    sheikh_out = df_sheikh[df_sheikh['النوع'] == 'صرف']['الإجمالي ($)'].sum()
    
    final_status = sheikh_in - sheikh_out
    
    if final_status > 0:
        st.success(f"⚖️ ميزان الحساب: **المسجد مدين لك بمبلغ ${abs(final_status):,.2f}** (لك على المسجد)")
    elif final_status < 0:
        st.warning(f"⚖️ ميزان الحساب: **أنت مدين للمسجد بمبلغ ${abs(final_status):,.2f}** (عليك للمسجد)")
    else:
        st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً ($0.00)")
        
    st.write("---")
    st.dataframe(df_sheikh, use_container_width=True)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين (بالدولار)")
    
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
    
    emp_records = []
    for idx, row in df_emps.iterrows():
        emp_name = row['name']
        required = row['salary']
        paid = df_trans[(df_trans['ref_name'] == emp_name) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        emp_records.append({
            "اسم الموظف": emp_name,
            "الراتب المستحق ($)": required,
            "المدفوع إجمالاً ($)": paid,
            "المتبقي ($)": required - paid
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
        st.button("🖨️ طباعة")
    else:
        st.caption("لا توجد بيانات لتوليد التقارير.")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    
    new_rate = st.number_input("سعر صرف الدولار الحالي مقابل الليرة اللبنانية (مثال: 89500)", value=dollar_rate, step=500.0)
    if st.button("تحديث سعر الصرف"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success(f"تم تحديث السعر بنجاح إلى: {new_rate:,.0f} ل.ل")
        st.rerun()
        
    st.write("---")
    st.subheader("🚨 منطقة الخطر (إعادة تعيين قاعدة البيانات)")
    if st.button("🧹 تصفير وحذف جميع السندات المخربطة"):
        c.execute("DROP TABLE IF EXISTS transactions")
        conn.commit()
        st.success("تم مسح السندات القديمة بنجاح! يرجى إعادة تحديث الصفحة وبدء الإدخال.")
        st.rerun()
        
    st.write("---")
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
                fund TEXT, 
                account_type TEXT, 
                ref_name TEXT)''')

# إدخال البيانات الافتراضية للأسعار والصناديق
c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '89500')")
for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# --- القائمة الجانبية للتنقل ---
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>🕌 إدارة المسجد</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"])

# قراءة إعداد سعر الصرف الحالي
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
dollar_rate = float(c.fetchone()[0])

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.لبنانية للدولار</p>", unsafe_allow_html=True)
    st.write("---")
    
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    if not df_trans.empty:
        total_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
        total_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 الرصيد الإجمالي الحالي ($)", f"${current_balance:,.2f}")
    col2.metric("🟢 إجمالي الإيرادات ($)", f"${total_in:,.2f}")
    col3.metric("🔴 إجمالي المصروفات ($)", f"${total_out:,.2f}")
    
    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية بالدولار")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        fund_balances.append({"الصندوق": f, "الرصيد الحالي بالدولار ($)": f"${f_in - f_out:,.2f}"})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية (المعاينة اللحظية والتحويل الدقيق) ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية (يدعم الدولار واللبناني)")
    st.caption(f"💡 سعر الصرف المعتمد حالياً للتحويل: {dollar_rate:,.0f} ل.ل")
    
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    next_id = (max_id + 1) if max_id else 1
    
    st.info(f"رقم السند التلقائي القادم: {next_id}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now())
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])
    
    usd_amount = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=10.0, value=0.0)
    lbp_amount = col2.number_input("المبلغ بالليرة اللبنانية (ل.ل)", min_value=0.0, step=100000.0, value=0.0)
    
    # حساب قيمة اللبناني بالدولار بدقة وعرضها فورياً
    converted_instant = lbp_amount / dollar_rate if dollar_rate > 0 else 0
    total_calculated_usd = usd_amount + converted_instant
    
    if lbp_amount > 0:
        st.warning(f"🔄 **تحويل فوري دقيق:** {lbp_amount:,.0f} ل.ل تساوي حالياً: **${converted_instant:,.2f}** | إجمالي السند بالكامل: **${total_calculated_usd:,.2f}**")
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list)
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        ref_name = st.selectbox("اختر الموظف", emp_list)
        
    description = st.text_area("البيان / تفاصيل القيد")
    
    if st.button("حفظ السند المالي"):
        if usd_amount == 0 and lbp_amount == 0:
            st.error("الرجاء إدخال قيمة في حقل الدولار أو اللبناني على الأقل.")
        elif not description:
            st.error("الرجاء إدخال بيان للعملية.")
        else:
            c.execute("""INSERT INTO transactions 
                         (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success(f"تم حفظ السند رقم {next_id} بنجاح! الإجمالي الصحيح: ${total_calculated_usd:,.2f}")
            st.rerun()

    st.write("---")
    st.subheader("📋 القيود المسجلة مؤخراً")
    df_all = pd.read_sql_query("""SELECT id AS 'رقم السند', date AS 'التاريخ', description AS 'البيان', 
                                  type AS 'النوع', amount_usd AS 'دولار $', amount_lbp AS 'لبناني ل.ل', 
                                  total_usd AS 'الإجمالي ($)', fund AS 'الصندوق' 
                                  FROM transactions ORDER BY id DESC""", conn)
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)
    else:
        st.caption("لا توجد قيود مسجلة بعد.")

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق (بالدولار)")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        records.append({
            "اسم الصندوق": f,
            "إجمالي القبض ($)": f_in,
            "إجمالي الصرف ($)": f_out,
            "الرصيد الصافي ($)": f_in - f_out
        })
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم مع المسجد (بالدولار)")
    
    df_sheikh = pd.read_sql_query("""SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', 
                                     amount_usd AS 'دولار', amount_lbp AS 'لبناني', total_usd AS 'الإجمالي ($)' 
                                     FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'""", conn)
    
    sheikh_in = df_sheikh[df_sheikh['النوع'] == 'قبض']['الإجمالي ($)'].sum()
    sheikh_out = df_sheikh[df_sheikh['النوع'] == 'صرف']['الإجمالي ($)'].sum()
    
    final_status = sheikh_in - sheikh_out
    
    if final_status > 0:
        st.success(f"⚖️ ميزان الحساب: **المسجد مدين لك بمبلغ ${abs(final_status):,.2f}** (لك على المسجد)")
    elif final_status < 0:
        st.warning(f"⚖️ ميزان الحساب: **أنت مدين للمسجد بمبلغ ${abs(final_status):,.2f}** (عليك للمسجد)")
    else:
        st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً ($0.00)")
        
    st.write("---")
    st.dataframe(df_sheikh, use_container_width=True)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين (بالدولار)")
    
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
    
    emp_records = []
    for idx, row in df_emps.iterrows():
        emp_name = row['name']
        required = row['salary']
        paid = df_trans[(df_trans['ref_name'] == emp_name) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        emp_records.append({
            "اسم الموظف": emp_name,
            "الراتب المستحق ($)": required,
            "المدفوع إجمالاً ($)": paid,
            "المتبقي ($)": required - paid
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
        st.button("🖨️ طباعة")
    else:
        st.caption("لا توجد بيانات لتوليد التقارير.")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    
    new_rate = st.number_input("سعر صرف الدولار الحالي مقابل الليرة اللبنانية (مثال: 89500)", value=dollar_rate, step=500.0)
    if st.button("تحديث سعر الصرف"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success(f"تم تحديث السعر بنجاح إلى: {new_rate:,.0f} ل.ل")
        st.rerun()
        
    st.write("---")
    st.subheader("🚨 منطقة الخطر (إعادة تعيين قاعدة البيانات)")
    st.caption("استخدم هذا الزر لحذف السندات القديمة المتداخلة والمخربطة وبدء الحسابات من الصفر بناءً على الأسعار الجديدة.")
    if st.button("🧹 تصفير وحذف جميع السندات المخربطة"):
        c.execute("DROP TABLE IF EXISTS transactions")
        conn.commit()
        st.success("تم مسح السندات القديمة بنجاح! يرجى إعادة تحديث الصفحة والبدء بالإدخال الصحيح.")
        st.rerun()
        
    st.write("---")
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
    st.subheader("➕ إضافة موظف جديد")
    col1, col2 = st.columns(2)
    emp_name = col1.text_input("اسم الموظف")
    emp_salary = col2.number_input("الراتب الشهري الافتراضي ($)", min_value=0.0)
    if st.button("حفظ الموظف"):
        if emp_name:
            c.execute("INSERT INTO employees (name, salary) VALUES (?,?)", (emp_name, emp_salary))
            conn.commit()
            st.success(f"تمت إضافة الموظف {emp_name}")
            st.rerun()
