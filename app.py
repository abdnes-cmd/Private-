import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# إعدادات الصفحة والهوية البصرية (الأخضر والذهبي)
st.set_page_config(page_title="النظام المالي للمسجد", page_icon="🕌", layout="wide")

# تصميم مخصص بالألوان المطلوبة وتعديل اتجاه وتلوين الجداول
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    h1, h2, h3 { color: #004D40; font-family: 'Cairo', sans-serif; text-align: right; }
    .stButton>button { background-color: #004D40; color: #D4AF37; border-radius: 5px; }
    .stButton>button:hover { background-color: #D4AF37; color: #004D40; }
    .reportview-container .main .block-container{ padding-top: 2rem; }
    
    /* تنسيق وعكس اتجاه الجداول من اليمين إلى اليسار وتلوينها */
    div[data-testid="stTable"] table {
        direction: rtl !important;
        text-align: right !important;
        width: 100%;
        border-collapse: collapse;
    }
    div[data-testid="stTable"] th {
        text-align: right !important;
        padding: 12px !important;
        font-size: 16px !important;
        border: 1px solid #00332a;
    }
    div[data-testid="stTable"] td {
        text-align: right !important;
        padding: 12px !important;
        border: 1px solid #e0e0e0;
        font-size: 15px !important;
    }
    
    /* تلوين أعمدة الترويسة بشكل تبادلي */
    div[data-testid="stTable"] th:nth-child(odd) {
        background-color: #004D40 !important;
        color: #D4AF37 !important;
    }
    div[data-testid="stTable"] th:nth-child(even) {
        background-color: #C5A059 !important;
        color: #FFFFFF !important;
    }
    
    /* تلوين أسطر الجدول بشكل تبادلي */
    div[data-testid="stTable"] td:nth-child(odd) {
        background-color: #e8f5e9 !important;
        color: #004D40 !important;
        font-weight: bold;
    }
    div[data-testid="stTable"] td:nth-child(even) {
        background-color: #fefde8 !important;
        color: #b45309 !important;
    }
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

# إضافة الصناديق الأساسية والصندوق المخصص للشيخ
for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع", "ذمة وسلف الشيخ عبد الكريم"]:
    c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
conn.commit()

# قراءة سعر الصرف الحالي
c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
fetch_val = c.fetchone()
dollar_rate = float(fetch_val[0]) if fetch_val else 89500.0

# --- القائمة الجانبية للتنقل وإدراج الشعار ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
image_path = "1002387706.jpg"
if os.path.exists(image_path):
    st.sidebar.image(image_path, use_container_width=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>🕌 مسجد الإحسان</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #004D40; font-weight: bold;'>مجدل عنجر</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"], key="side_nav_v21")

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.ل للدولار</p>", unsafe_allow_html=True)
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
    
    # 📋 الجدول 1: ملخص الرواتب
    st.subheader("👥 ملخص رواتب الموظفين والعاملين ($)")
    df_emps_db = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    emp_salaries_dict = pd.Series(df_emps_db.salary.values, index=df_emps_db.name).to_dict() if not df_emps_db.empty else {}
    
    distinct_ref_names = []
    if not df_trans.empty:
        distinct_ref_names = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] != '')]['ref_name'].unique().tolist()
    all_distinct_workers = list(set(list(emp_salaries_dict.keys()) + distinct_ref_names))
    
    if not all_distinct_workers:
        st.info("💡 لا توجد بيانات موظفين مسجلة.")
    else:
        worker_report_data = []
        for worker in all_distinct_workers:
            assigned_salary = emp_salaries_dict.get(worker, 0.0)
            amount_paid = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] == worker) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            amount_remaining = assigned_salary - amount_paid
            display_name = worker if worker in emp_salaries_dict else f"{worker} (اسم محذوف)"
            worker_report_data.append({
                "اسم الموظف": display_name,
                "الراتب المستحق ($)": f"${assigned_salary:,.0f}",
                "إجمالي ما تم صرفه له ($)": f"${amount_paid:,.0f}",
                "المتبقي له في الذمة ($)": f"${amount_remaining:,.0f}"
            })
        st.table(pd.DataFrame(worker_report_data))
        
    st.write("---")
    
    # 📌 الجدول 2: أرصدة الصناديق
    st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    sheikh_personal_in = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
    sheikh_personal_out = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0

    fund_balances = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
        current_bal = f_in - f_out

        if f == "ذمة وسلف الشيخ عبد الكريم":
            net_sheikh_status = sheikh_personal_in - sheikh_personal_out
            status_text = f"${net_sheikh_status:,.0f} (دائن)" if net_sheikh_status > 0 else (f"${abs(net_sheikh_status):,.0f} (مدين)" if net_sheikh_status < 0 else "$0")
            fund_balances.append({"الصندوق": "👤 ذمة الشيخ", "الحالة": status_text})
        else:
            fund_balances.append({"الصندوق": f, "الحالة": f"${current_bal:,.0f}"})
    st.table(pd.DataFrame(fund_balances))

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    st.info(f"رقم السند التلقائي القادم: {(max_id + 1) if max_id else 1}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now())
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])
    usd_amount = col1.number_input("المبلغ ($)", min_value=0.0, step=1.0)
    lbp_amount = col2.number_input("المبلغ (ل.ل)", min_value=0.0, step=1000.0)
    
    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)
    
    if lbp_amount > 0:
        st.warning(f"📊 قيمة المبلغ بالليرة تعادل: {converted_instant:,.0f}$")
        
    fund = col1.selectbox("الصندوق", funds_list)
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        if emp_list: ref_name = st.selectbox("اختر الموظف", emp_list)
        else: st.error("⚠️ لا يوجد موظفون.")
        
    description = st.text_area("البيان")
    
    if st.button("حفظ السند"):
        if total_calculated_usd == 0: st.error("أدخل مبلغاً.")
        elif not description: st.error("أدخل بياناً.")
        else:
            c.execute("INSERT INTO transactions (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) VALUES (?,?,?,?,?,?,?,?,?)",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success("تم الحفظ!")
            st.rerun()

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة وتفاصيل أرصدة الصناديق")
    st.markdown("### 🔍 تفاصيل المصروفات")
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE type='صرف'", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    if df_trans.empty:
        st.info("💡 لا توجد مصروفات.")
    else:
        for f in df_funds['name']:
            st.markdown(f"#### 📦 صندوق: {f}")
            df_f_spend = df_trans[df_trans['fund'] == f]
            if df_f_spend.empty:
                st.write("*لا مصروفات.*")
                continue
            detailed_rows = []
            for _, row in df_f_spend.iterrows():
                label = row['description']
                if row['account_type'] == 'رواتب الموظفين' and row['ref_name']: label = f"راتب ({row['ref_name']}) - {label}"
                detailed_rows.append({"التاريخ": row['date'], "البيان": label, "المبلغ ($)": f"${row['total_usd']:,.0f}"})
            st.table(pd.DataFrame(detailed_rows))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 حساب الشيخ عبد الكريم")
    df_trans = pd.read_sql_query("SELECT id, date, description, type, amount_usd, amount_lbp, total_usd FROM transactions WHERE account_type='حساب الشيخ عبد الكريم' ORDER BY id DESC", conn)
    
    if df_trans.empty:
        st.info("💡 لا حركات مسجلة.")
    else:
        sheikh_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum()
        sheikh_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum()
        status = sheikh_in - sheikh_out
        st.success(f"⚖️ الميزان الحالي: {'لكم' if status > 0 else 'عليكم'} {abs(status):,.0f}$")
        
        df_display = pd.DataFrame()
        df_display['التاريخ'] = df_trans['date']
        df_display['الحركة'] = df_trans['type']
        df_display['البيان'] = df_trans['description']
        df_display['الإجمالي ($)'] = df_trans['total_usd'].apply(lambda x: f"${x:,.0f}")
        st.table(df_display)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 الرواتب")
    st.subheader("📝 إضافة موظف")
    col1, col2 = st.columns(2)
    emp_name = col1.text_input("الاسم")
    emp_salary = col2.number_input("الراتب ($)", min_value=0)
    
    if st.button("حفظ الموظف"):
        if emp_name:
            c.execute("INSERT OR REPLACE INTO employees (name, salary) VALUES (?, ?)", (emp_name, emp_salary))
            conn.commit()
            st.success("تم الحفظ!")
            st.rerun()
            
    st.write("---")
    st.subheader("📋 الموظفون")
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    if not df_emps.empty:
        st.table(df_emps)

# --- 6. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية")
    rep_type = st.selectbox("النوع", ["يومي", "شهري", "سنوي"])
    df_report = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    
    if not df_report.empty:
        df_report['parsed_date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي":
            sel_date = st.date_input("اليوم", datetime.now())
            df_filtered = df_report[df_report['parsed_date'].dt.date == sel_date]
        elif rep_type == "شهري":
            sel_month = st.slider("الشهر", 1, 12, int(datetime.now().month))
            df_filtered = df_report[df_report['parsed_date'].dt.month == sel_month]
        else:
            sel_year = st.number_input("السنة", min_value=2020, value=int(datetime.now().year))
            df_filtered = df_report[df_report['parsed_date'].dt.year == sel_year]
            
        if not df_filtered.empty:
            df_display = pd.DataFrame()
            df_display['التاريخ'] = df_filtered['date']
            df_display['الحركة'] = df_filtered['type']
            df_display['البيان'] = df_filtered['description']
            df_display['الصندوق'] = df_filtered['fund']
            df_display['الإجمالي ($)'] = df_filtered['total_usd'].apply(lambda x: f"${x:,.0f}")
            st.table(df_display)
            st.button("🖨️ طباعة")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات")
    new_rate = st.number_input("سعر صرف الدولار (ل.ل)", value=dollar_rate)
    if st.button("تحديث السعر"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success("تم التحديث!")
        st.rerun()
