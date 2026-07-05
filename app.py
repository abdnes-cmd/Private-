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
        background-color: #004D40 !important;
        color: #D4AF37 !important;
        text-align: right !important;
        padding: 10px !important;
        font-size: 16px !important;
    }
    div[data-testid="stTable"] td {
        text-align: right !important;
        padding: 10px !important;
        border-bottom: 1px solid #e0e0e0;
    }
    /* تلوين أسطر الجدول بالتناوب */
    div[data-testid="stTable"] tr:nth-child(even) {
        background-color: #f2f7f4 !important;
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
# التحقق من وجود ملف شعار المسجد وعرضه
image_path = "1002387706.jpg"
if os.path.exists(image_path):
    st.sidebar.image(image_path, use_container_width=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>🕌 مسجد الإحسان</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #004D40; font-weight: bold;'>مجدل عنجر</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"], key="side_nav_panel_unique_v15")

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
    
    # 📋 الجدول 1: ملخص الرواتب للموظفين والعاملين
    st.subheader("👥 ملخص رواتب وحسابات الموظفين والعاملين ($)")
    
    df_emps_db = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    emp_salaries_dict = pd.Series(df_emps_db.salary.values, index=df_emps_db.name).to_dict() if not df_emps_db.empty else {}
    
    distinct_ref_names = []
    if not df_trans.empty:
        distinct_ref_names = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] != '')]['ref_name'].unique().tolist()
    
    all_distinct_workers = list(set(list(emp_salaries_dict.keys()) + distinct_ref_names))
    
    if not all_distinct_workers:
        st.info("💡 لا توجد بيانات موظفين أو عمليات رواتب مسجلة حتى الآن.")
    else:
        worker_report_data = []
        for worker in all_distinct_workers:
            assigned_salary = emp_salaries_dict.get(worker, 0.0)
            
            if not df_trans.empty:
                amount_paid = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] == worker) & (df_trans['type'] == 'صرف')]['total_usd'].sum()
            else:
                amount_paid = 0.0
                
            amount_remaining = assigned_salary - amount_paid
            display_name = worker if worker in emp_salaries_dict else f"{worker} (اسم محذوف من الرواتب)"
            
            worker_report_data.append({
                "اسم الموظف / العامل": display_name,
                "الراتب المستحق ($)": f"${assigned_salary:,.0f}",
                "إجمالي ما تم صرفه له ($)": f"${amount_paid:,.0f}",
                "المتبقي له في الذمة ($)": f"${amount_remaining:,.0f}"
            })
        st.table(pd.DataFrame(worker_report_data))
        
    st.write("---")
    
    # 📊 الجدول 2: ملخص المصروفات التشغيلية الأخرى
    st.subheader("🚰 ملخص المصروفات التشغيلية والأخرى ($)")
    if df_trans.empty:
        st.info("💡 لا توجد مصروفات مسجلة بعد.")
    else:
        df_ops = df_trans[(df_trans['type'] == 'صرف') & (df_trans['account_type'] == 'عام')]
        if df_ops.empty:
            st.info("💡 لا توجد مصروفات عامة أو تشغيلية مسجلة حتى الآن.")
        else:
            df_ops_grouped = df_ops.groupby('description')['total_usd'].sum().reset_index()
            df_ops_grouped.columns = ['نوع المصروف / البيان', 'إجمالي المبلغ المصروف ($)']
            df_ops_grouped['إجمالي المبلغ المصروف ($)'] = df_ops_grouped['إجمالي المبلغ المصروف ($)'].apply(lambda x: f"${x:,.0f}")
            st.table(df_ops_grouped)

    st.write("---")
    
    # 📌 الجدول 3: أرصدة الصناديق والتمييز الدقيق بين الدائن والمدين للشيخ
    st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    
    raw_balances = {}
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
        raw_balances[f] = f_in - f_out

    automatic_deficit_covered_by_sheikh = 0.0
    if raw_balances.get("المسجد العامة", 0.0) < 0:
        automatic_deficit_covered_by_sheikh = abs(raw_balances["المسجد العامة"])

    sheikh_personal_in = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
    sheikh_personal_out = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0

    fund_balances = []
    for f in df_funds['name']:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            net_sheikh_status = automatic_deficit_covered_by_sheikh + sheikh_personal_in - sheikh_personal_out
            
            if net_sheikh_status > 0:
                status_text = f"${net_sheikh_status:,.0f} (مستحق لك على المسجد - دائن)"
            elif net_sheikh_status < 0:
                status_text = f"${abs(net_sheikh_status):,.0f} (مطلوب منك للمسجد - مدين)"
            else:
                status_text = "$0 (متقاص ومسدد تماماً)"
                
            fund_balances.append({
                "الصندوق أو الحساب": "👤 ذمة وسلف الشيخ عبد الكريم (الصافي الإجمالي)",
                "الحالة المالية والاتزان ($)": status_text
            })
            
            if automatic_deficit_covered_by_sheikh > 0:
                fund_balances.append({"الصندوق أو الحساب": "   ↳ 🟢 عجز في الصندوق العام قمت أنت بتغطيته تلقائياً", "الحالة المالية والاتزان ($)": f"+${automatic_deficit_covered_by_sheikh:,.0f}"})
            if sheikh_personal_out > 0:
                fund_balances.append({"الصندوق أو الحساب": "   ↳ 🔴 مبالغ شخصية استدنتها أنت من صندوق المسجد", "الحالة المالية والاتزان ($)": f"-${sheikh_personal_out:,.0f}"})
            if sheikh_personal_in > 0:
                fund_balances.append({"الصندوق أو الحساب": "   ↳ 🟢 مبالغ شخصية قمت بإعادتها أو تبرعت بها مباشرة", "الحالة المالية والاتزان ($)": f"+${sheikh_personal_in:,.0f}"})
        
        elif f == "المسجد العامة":
            current_bal = 0.0 if automatic_deficit_covered_by_sheikh > 0 else raw_balances.get(f, 0.0)
            note = " (تم تصفير العجز تلقائياً بواسطة الشيخ)" if automatic_deficit_covered_by_sheikh > 0 else ""
            fund_balances.append({
                "الصندوق أو الحساب": f + note,
                "الحالة المالية والاتزان ($)": f"${current_bal:,.0f}"
            })
        else:
            current_bal = raw_balances.get(f, 0.0)
            fund_balances.append({
                "الصندوق أو الحساب": f,
                "الحالة المالية والاتزان ($)": f"${current_bal:,.0f}"
            })
        
    st.table(pd.DataFrame(fund_balances))

# --- بقية الصفحات والعمليات لضمان استقرار البيانات ---
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
    t_date = col1.date_input("التاريخ", datetime.now(), key="q_entry_date_v15")
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="q_entry_type_v15")
    usd_amount = col1.number_input("المبلغ بالدولار", min_value=0.0, step=1.0, value=0.0, key="q_usd_input_v15")
    lbp_amount = col2.number_input("المبلغ بالليرة اللبنانية", min_value=0.0, step=1000.0, value=0.0, key="q_lbp_input_v15")
    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)
    if lbp_amount > 0 or usd_amount > 0:
        st.warning(f"📊 معاينة الحسبة: قيمة اللبناني: {converted_instant:,.0f}$ | الإضافي: {usd_amount:,.0f}$ | الإجمالي: {total_calculated_usd:,.0f}$")
    fund = col1.selectbox("الصندوق المتأثر", funds_list, key="q_entry_fund_v15")
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"], key="q_entry_account_type_v15")
    ref_name = ""
    if account_type == "رواتب الموظفين":
        if emp_list: ref_name = st.selectbox("اختر الموظف", emp_list, key="q_entry_employee_ref_v15")
        else: st.error("⚠️ لا يوجد موظفون مسجلون.")
    description = st.text_area("البيان / تفاصيل القيد", key="q_entry_description_v15")
    if st.button("حفظ السند المالي", key="q_entry_save_btn_v15"):
        if usd_amount == 0 and lbp_amount == 0: st.error("الرجاء إدخال قيمة.")
        elif account_type == "رواتب الموظفين" and not ref_name: st.error("الرجاء تحديد موظف.")
        elif not description: st.error("الرجاء إدخال بيان.")
        else:
            c.execute("INSERT INTO transactions (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) VALUES (?,?,?,?,?,?,?,?,?)",
                      (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            st.success(f"تم حفظ السند بنجاح! الإجمالي: {total_calculated_usd:,.0f} دولار")
            st.rerun()
    st.write("---")
    st.subheader("📋 إدارة وحذف السندات المسجلة")
    df_raw = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    if df_raw.empty: st.info("💡 لا توجد قيود مسجلة بعد.")
    else:
        for idx, row in df_raw.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1, 2, 1, 3, 1])
            c1.write(f"**🔢 سند رقم:** {row['id']}")
            c2.write(f"**📅 التاريخ:** {row['date']}")
            c3.write(f"**نوع الحساب:** {row['account_type']}")
            details = f"【 {row['type']} 】 بمبلغ **{row['total_usd']:,.0f}$** | البيان: {row['description']}"
            if row['ref_name']: details += f" ({row['ref_name']})"
            c4.write(details)
            if c5.button("🗑️ حذف السند", key=f"del_trans_id_{row['id']}"):
                c.execute("DELETE FROM transactions WHERE id = ?", (row['id'],))
                conn.commit()
                st.success(f"تم حذف السند المالي رقم {row['id']} بنجاح!")
                st.rerun()
            st.write("---")

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة أرصدة الصناديق")
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    records = []
    for f in df_funds['name']:
        f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0
        f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0
        records.append({"اسم الصندوق": f, "إجمالي القبض ($)": f"{f_in:,.0f}", "إجمالي الصرف ($)": f"{f_out:,.0f}", "الرصيد الصافي ($)": f"{(f_in - f_out):,.0f}"})
    st.table(pd.DataFrame(records))

# --- 4. حساب الشيخ عبد الكريم ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم")
    df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='حساب الشيخ عبد الكريم'", conn)
    sheikh_in = df_trans[df_trans['type'] == 'قبض']['total_usd'].sum() if not df_trans.empty else 0
    sheikh_out = df_trans[df_trans['type'] == 'صرف']['total_usd'].sum() if not df_trans.empty else 0
    final_status = sheikh_in - sheikh_out
    if final_status > 0: st.success(f"⚖️ ميزان الحساب: المسجد مدين لك بمبلغ {final_status:,.0f} دولار")
    elif final_status < 0: st.warning(f"⚖️ ميزان الحساب: أنت مدين للمسجد بمبلغ {abs(final_status):,.0f} دولار")
    else: st.info("⚖️ ميزان الحساب: الحساب متقاص تماماً ($0)")
    df_sheikh = pd.read_sql_query("SELECT date AS 'التاريخ', description AS 'البيان', type AS 'النوع', CAST(amount_usd AS INT) AS 'دولار', CAST(amount_lbp AS INT) AS 'لبناني', CAST(total_usd AS INT) AS 'الإجمالي ($)' FROM transactions WHERE account_type='حساب الشيخ عبد الكريم' ORDER BY id DESC", conn)
    if df_sheikh.empty: st.info("💡 لا توجد عمليات مسجلة على هذا الحساب حتى الآن.")
    else: 
        st.dataframe(df_sheikh, use_container_width=True)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 رواتب الموظفين والعاملين")
    st.subheader("📝 إضافة موظف جديد أو تعديل راتبه")
    col_name, col_sal, col_btn = st.columns([2, 1, 1])
    emp_name = col_name.text_input("اسم الموظف / العامل كاملاً", key="emp_reg_name_v15")
    emp_salary = col_sal.number_input("الراتب الشهري ($)", min_value=0, step=50, value=0, key="emp_reg_salary_v15")
    col_btn.markdown("<br>", unsafe_allow_html=True)
    if col_btn.button("حفظ البيانات", key="emp_reg_save_btn_v15"):
        if emp_name:
            c.execute("INSERT OR REPLACE INTO employees (name, salary) VALUES (?, ?)", (emp_name, emp_salary))
            conn.commit()
            st.success(f"تم حفظ الموظف {emp_name}!")
            st.rerun()
        else: st.error("يرجى كتابة الاسم.")
    st.write("---")
    st.subheader("📋 جدول الإدارة العامة للموظفين النشطين")
    df_emps = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    if df_emps.empty: st.info("💡 لا يوجد موظفون نشطون مسجلون بعد.")
    else:
        df_trans = pd.read_sql_query("SELECT * FROM transactions WHERE account_type='رواتب الموظفين'", conn)
        for idx, row in df_emps.iterrows():
            paid = df_trans[(df_trans['ref_name'] == row['name']) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0
            rem = row['salary'] - paid
            c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
            c1.write(f"**👤 الموظف:** {row['name']}")
            c2.write(f"**المستحق:** ${row['salary']:,.0f}")
            c3.write(f"**المدفوع:** ${paid:,.0f}")
            c4.write(f"**المتبقي:** ${rem:,.0f}")
            if c5.button("🗑️ حذف من القائمة", key=f"del_btn_idx_{idx}"):
                c.execute("DELETE FROM employees WHERE name = ?", (row['name'],))
                conn.commit()
                st.success(f"تم الحذف بنجاح!")
                st.rerun()
            st.write("---")

# --- 6. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة")
    rep_type = st.selectbox("نوع التقرير", ["يومي", "شهري", "سنوي"], key="rep_filter_type_v15")
    df_report = pd.read_sql_query("SELECT id, date, description, type, CAST(amount_usd AS INT) AS 'دولار', CAST(amount_lbp AS INT) AS 'لبناني', CAST(total_usd AS INT) AS 'الإجمالي ($)', fund FROM transactions", conn)
    if not df_report.empty:
        df_report['date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي": df_filtered = df_report[df_report['date'].dt.date == st.date_input("اختر اليوم", datetime.now(), key="rep_date_picker_v15")]
        elif rep_type == "شهري": df_filtered = df_report[df_report['date'].dt.month == st.slider("اختر الشهر", 1, 12, int(datetime.now().month), key="rep_month_slider_v15")]
        else: df_filtered = df_report[df_report['date'].dt.year == st.number_input("اختر السنة", min_value=2020, max_value=2030, value=int(datetime.now().year), key="rep_year_input_v15")]
        st.write(df_filtered)
        st.button("🖨️ طباعة", key="rep_print_btn_v15")

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة للنظام")
    new_rate = st.number_input("سعر صرف الدولار الحالي مقابل الليرة اللبنانية (مثال: 89500)", value=dollar_rate, step=500.0, key="sys_setting_exchange_rate_input_final_v15")
    if st.button("تحديث سعر الصرف", key="sys_setting_update_rate_btn_v15"):
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        st.success(f"تم تحديث السعر بنجاح إلى: {new_rate:,.0f} ل.ل")
        st.rerun()
    st.write("---")
    st.subheader("🚨 منطقة الخطر (إعادة تعيين قاعدة البيانات)")
    if st.button("🧹 تصفير وحذف جميع السندات المخربطة", key="sys_setting_clear_db_btn_v15"):
        c.execute("DROP TABLE IF EXISTS transactions")
        c.execute("UPDATE settings SET value='89500' WHERE key='dollar_rate'")
        conn.commit()
        st.success("تم تصفير قاعدة البيانات بنجاح.")
        st.rerun()
