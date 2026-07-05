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

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('mosque_finance.db', check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS funds (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
c.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, salary REAL)")
c.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, description TEXT, type TEXT, amount_usd REAL, amount_lbp REAL, total_usd REAL, fund TEXT, account_type TEXT, ref_name TEXT)")

c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '89500')")

for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# قراءة سعر الصرف الحالي
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
fetch_val = c.fetchone()
dollar_rate = float(fetch_val[0]) if fetch_val else 89500.0

# --- القائمة الجانبية للتنقل ---
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37;'>🕌 إدارة المسجد</h2>", unsafe_allow_html=True)
page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"], key="side_nav_panel_unique_v5")

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
    col1.metric("💰 الرصيد الإجمالي الحالي ($)", f"${current_balance:,.0f}")
    col2.metric("🟢 إجمالي الإيرادات ($)", f"${total_in:,.0f}")
    col3.metric("🔴 إجمالي المصروفات ($)", f"${total_out:,.0f}")
    
    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية بالدولار")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        fund_balances.append({"الصندوق": f, "الرصيد الحالي بالدولار ($)": f"${(f_in - f_out):,.0f}"})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    next_id = (max_id + 1) if max_id else 1
    
    st.info(f"رقم السند التلقائي القادم: {next_id}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now(), key="q_entry_date_v5")
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="q_entry_type_v5")
    
    usd_amount = col1.number_input("المبلغ بالدولار", min_value=0.0, step=1.0, value=0.0, key="q_usd_input_v5")
    lbp_amount = col2.number_input("المبلغ بالليرة اللبنانية", min_value=0.0, step=1000.0, value=0.0, key="q_lbp_input_v5")
    
    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)
    
    if lbp_amount > 0 or usd_amount > 0:
        st.warning(f"""
        📊 معاينة الحسبة الحالية (بدون فواصل):
        - قيمة اللبناني بالدولار: {converted_instant:,.0f} دولار
        - المبلغ الإضافي بالدولار: {usd_amount:,.0f} دولار
        - إجمالي السند بالكامل: {total_calculated_usd:,.0f} دولار
        """)
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list, key="q_entry_fund_v5")
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"], key="q_entry_account_type_v5")
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        if emp_list:
            ref_name = st.selectbox("اختر الموظف", emp_list, key="q_entry_employee_ref_v5")
        else:
            st.error("⚠️ لا يوجد موظفون مسجلون لتحديدهم. اذهب لصفحة الرواتب أولاً لإضافة الموظفين.")
        
    description = st.text_area("البيان / تفاصيل القيد", key="q_entry_description_v5")
    
    if st.button("حفظ السند المالي", key="q_entry_save_btn_v5"):
        if usd_amount == 0 and lbp_amount == 0:
            st.error("الرجاء إدخال قيمة في حقل الدولار أو اللبناني على الأقل.")
        elif account_type == "رواتب الموظفين" and not ref_name:
            st.error("الرجاء تحديد موظف مسجل أولاً أو إضافة موظفين في صفحة الرواتب.")
        elif not description:
            st.error("الرجاء إدخال بيان للعملية.")
        else:
            c.execute("""INSERT INTO transactions 
                         (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) 
                         VALUES (?,?,?,?,?,?,?,?,?)""",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success(f"تم حفظ السند بنجاح! الإجمالي: {total_calculated_usd:,.0f} دولار")
            st.rerun()

    st.write("---")
    st.subheader("📋 القيود المسجلة مؤخراً")
    df_all = pd.read_sql_query("""SELECT id AS 'رقم السند', date AS 'التاريخ', description AS 'البيان', 
                                  type AS 'النوع', CAST(amount_usd AS INT) AS 'دولار', CAST(amount_lbp AS INT) AS 'لبناني', 
                                  CAST(total_usd AS INT) AS 'الإجمالي ($)', fund AS 'الصندوق' 
                                  FROM transactions ORDER BY id DESC""", conn)
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
        records.append({
            "اسم الصندوق": f,
            "إجمالي القبض ($)": f"{f_in:,.0f}",
            "إجمالي الصرف ($)": f"{f_out:,.0f}",
            "الرصيد الصافي ($)": f"{(f_in - f_out):,.0f}"
        })
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم")
    
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'", conn)
    sheikh_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
    sheikh_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
    final_status = sheikh_in - sheikh_out
    
    if final_status > 0: 
        st.success(f"⚖️ ميزان الحساب: المسجد مدين لك بمبلغ {final_status:,.0f} دولار")
    elif final_status < 0: 
        st.warning(f"⚖️ ميزان الحساب: أنت مدين للمسجد بمبلغ {abs(final_status):,.0f} دولار")
    else: 
        st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً ($0)")
        
    df_sheikh = pd.read_sql_query("SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', CAST(amount_usd AS INT) AS 'دولار', CAST(amount_lbp AS INT) AS 'لبناني', CAST(total_usd AS INT) AS 'الإجمالي ($)' FROM transactions WHERE account_type='حساب الشيخ عبد الكريم' ORDER BY id DESC", conn)
    
    if df_sheikh.empty:
        st.info("💡 لا توجد عمليات مسجلة على هذا الحساب حتى الآن. عندما تقوم بإضافة قيد يومي وتختار نوع الحساب (حساب الشيخ عبد الكريم)، سيظهر هنا فوراً.")
    else:
        st.dataframe(df_sheikh, use_container_width=True)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين")
    
    st.subheader("📝 إضافة موظف جديد أو تعديل راتبه")
    col_name, col_sal, col_btn = st.columns([2, 1, 1])
    
    emp_name = col_name.text_input("اسم الموظف / العامل كاملاً", key="emp_reg_name_v5")
    emp_salary = col_sal.number_input("الراتب الشهري ($)", min_value=0, step=50, value=0, key="emp_reg_salary_v5")
    
    col_btn.markdown("<br>", unsafe_allow_html=True)
    if col_btn.button("حفظ البيانات", key="emp_reg_save_btn_v5"):
        if emp_name:
            c.execute("INSERT OR REPLACE INTO employees (name, salary) VALUES (?, ?)", (emp_name, emp_salary))
            conn.commit()
            st.success(f"تم حفظ الموظف {emp_name}!")
            st.rerun()
        else:
            st.error("يرجى كتابة الاسم.")

    st.write("---")
    st.subheader("📋 جدول الرواتب الحالي وإدارة الحذف")
    
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    
    if df_emps.empty:
        st.info("💡 لا يوجد موظفون مسجلون بعد. يرجى تعبئة الحقول أعلاه والضغط على (حفظ البيانات) لإضافة أول موظف.")
    else:
        df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
        
        for idx, row in df_emps.iterrows():
            paid = df_trans[(df_trans['ref_name'] == row['name']) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
            rem = row['salary'] - paid
            
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            c1.write(f"**👤 الموظف:** {row['name']}")
            c2.write(f"**المستحق:** ${row['salary']:,.0f}")
            c3.write(f"**المدفوع:** ${paid:,.0f}")
            c4.write(f"**المتبقي:** ${rem:,.0f}")
            
            # تم تعديل المفتاح هنا بإضافة idx ليكون فريداً بالكامل ويختفي الخطأ
            if c5.button("🗑️ حذف الموظف", key=f"del_btn_idx_{idx}"):
                c.execute("DELETE FROM employees WHERE name = ?", (row['name'],))
                conn.commit()
                st.success(f"تم حذف الموظف {row['name']} بنجاح!")
                st.rerun()
            st.write("---")

# --- 6. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة")
    rep_type = st.selectbox("نوع التقرير", ["يومي", "شهري", "سنوي"], key="rep_filter_type_v5")
    df_report = pd.read_sql_query("SELECT id, date, description, type, CAST(amount_usd AS INT) AS 'دولار', CAST(amount_lbp AS INT) AS 'لبناني', CAST(total_usd AS INT) AS 'الإجمالي ($)', fund FROM transactions", conn)
    if not df_report.empty:
        df_report['date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي": 
            df_filtered = df_report[df_report['date'].dt.date == st.date_input("اختر اليوم", datetime.now(), key="rep_date_picker_v5")]
        elif rep_type == "شهري": 
            df_filtered = df_report[df_report['date'].dt.month == st.slider("اختر الشهر", 1, 12, int(datetime.now().month), key="rep_month_slider_v5")]
        else: 
            df_filtered = df_report[df_report['date'].dt.year == st.number_input("اختر السنة", min_value=2020, max_value=2030, value=int(datetime.now().year), key="rep_year_input_v5")]
        st.write(df_filtered)
        st.button("🖨️ طباعة", key="rep_print_btn_v5")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    new_rate = st.number_input("سعر صرف الدولار الحالي مقابل الليرة اللبنانية (مثال: 89500)", value=dollar_rate, step=500.0, key="sys_setting_exchange_rate_input_final_v5")
    
    if st.button("تحديث سعر الصرف", key="sys_setting_update_rate_btn_v5"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success(f"تم تحديث السعر بنجاح إلى: {new_rate:,.0f} ل.ل")
        st.rerun()
        
    st.write("---")
    st.subheader("🚨 منطقة الخطر (إعادة تعيين قاعدة البيانات)")
    if st.button("🧹 تصفير وحذف جميع السندات المخربطة", key="sys_setting_clear_db_btn_v5"):
        c.execute("DROP TABLE IF EXISTS transactions")
        c.execute("UPDATE settings SET value='89500' WHERE key='dollar_rate'")
        conn.commit()
        st.success("تم تصفير قاعدة البيانات بنجاح وإعادة ضبط سعر الصرف إلى 89500.")
        st.rerun()
