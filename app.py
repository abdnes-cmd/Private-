import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# إعدادات الصفحة والهوية البصرية (الأخضر والذهبي)
st.set_page_config(page_title="النظام المالي للمسجد", page_icon="🕌", layout="wide")
if "initialized" not in st.session_state:
    st.session_state["initialized"] = True

# تصميم مخصص لتعديل اتجاه وتلوين الواجهة
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    h1, h2, h3, h4 { color: #004D40; font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { background-color: #004D40; color: #D4AF37; border-radius: 5px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #D4AF37; color: #004D40; }
    
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        direction: rtl;
        text-align: right;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .custom-table th {
        padding: 12px;
        font-size: 16px;
        border: 1px solid #00332a;
    }
    .custom-table th:nth-child(odd) {
        background-color: #004D40 !important;
        color: #D4AF37 !important;
    }
    .custom-table th:nth-child(even) {
        background-color: #C5A059 !important;
        color: #FFFFFF !important;
    }
    .custom-table td {
        padding: 12px;
        border: 1px solid #e0e0e0;
        font-size: 15px;
    }
    .custom-table td:nth-child(odd) {
        background-color: #e8f5e9 !important;
        color: #004D40 !important;
        font-weight: bold;
    }
    .custom-table td:nth-child(even) {
        background-color: #fefde8 !important;
        color: #b45309 !important;
    }
    </style>
""", unsafe_allow_html=True)

db_file_path = 'mosque_finance.db'

# دالة آمنة للاتصال بقاعدة البيانات
def get_db_connection():
    return sqlite3.connect(db_file_path, check_same_thread=False)

# إنشاء الجداول الأساسية عند البدء لمرة واحدة
try:
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS funds (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, salary REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, description TEXT, type TEXT, amount_usd REAL, amount_lbp REAL, total_usd REAL, fund TEXT, account_type TEXT, ref_name TEXT)")

    c.execute("INSERT OR IGNORE INTO settings VALUES ('dollar_rate', '89500')")
    for fund_name in ["المسجد العامة", "الزكاة", "الصدقات", "المشاريع", "ذمة وسلف الشيخ عبد الكريم"]:
        c.execute("INSERT OR IGNORE INTO funds (name) VALUES (?)", (fund_name,))
    conn.commit()

    c.execute("SELECT value FROM settings WHERE key='dollar_rate'")
    fetch_val = c.fetchone()
    dollar_rate = float(fetch_val[0]) if fetch_val else 89500.0
    conn.close()
except Exception as e:
    dollar_rate = 89500.0

# دالة لإعادة تحديث الصفحة
def safe_rerun():
    for rerun_func in ["rerun", "experimental_rerun"]:
        if hasattr(st, rerun_func):
            getattr(st, rerun_func)()
            break

# --- القائمة الجانبية للنظام ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)

image_path = "1002387706.jpg"
if os.path.exists(image_path):
    try:
        st.sidebar.image(image_path)
    except Exception:
        try:
            st.sidebar.image(image_path, use_container_width=True)
        except Exception:
            pass

st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>🕌 مسجد الإحسان</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #004D40; font-weight: bold;'>مجدل عنجر</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"], key="side_nav_v36")

def render_custom_html_table(headers, rows):
    html = "<table class='custom-table'><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            html += f"<td>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)


# --- دالة حساب ذمة الشيخ المحدثة والمصححة تماماً لمعالجة الاسترداد ---
def calculate_sheikh_final_balance(df):
    if df.empty:
        return 0.0, 0.0, 0.0
    
    paid_out = 0.0      # ما دفعه الشيخ من جيبه (أو سلفه للمسجد)
    received_back = 0.0 # ما استرده الشيخ من المسجد (تسديد ذمة)
    
    for _, row in df.iterrows():
        is_sheikh_fund = (row['fund'] == "ذمة وسلف الشيخ عبد الكريم")
        is_sheikh_acc = (row['account_type'] == "حساب الشيخ عبد الكريم")
        is_mosque_fund = (row['fund'] == "المسجد العامة")
        
        # 1. إذا خرج المال (صرف) من صندوق الشيخ، أو صُرف لحساب الشيخ وكان الصندوق المتأثر ليس المسجد العام
        if row['type'] == 'صرف' and (is_sheikh_fund or (is_sheikh_acc and not is_mosque_fund)):
            paid_out += row['total_usd']
        
        # 2. إذا تم صرف مبلغ من صندوق المسجد العام وكان مخصصاً لحساب الشيخ أو صندوق الشيخ (هذا هو الاسترداد والتسديد)
        elif row['type'] == 'صرف' and is_mosque_fund and (is_sheikh_acc or is_sheikh_fund):
            received_back += row['total_usd']
            
        # 3. إذا دخل مال (قبض) إلى حساب الشيخ أو صندوق الشيخ
        elif row['type'] == 'قبض' and (is_sheikh_acc or is_sheikh_fund):
            received_back += row['total_usd']
            
    net_status = paid_out - received_back
    return paid_out, received_back, net_status


# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.ل للدولار</p>", unsafe_allow_html=True)
    st.write("---")
    
    conn = get_db_connection()
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    df_emps_db = pd.read_sql_query("SELECT name, salary FROM employees", conn)
    conn.close()
    
    if not df_trans.empty:
        total_in = df_trans[(df_trans['fund'] == 'المسجد العامة') & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        total_out = df_trans[(df_trans['fund'] == 'المسجد العامة') & (df_trans['type'] == 'صرف')]['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 رصيد صندوق المسجد العام الحالي ($)", f"${current_balance:,.0f}")
    col2.metric("🟢 إجمالي مقبوضات المسجد العامة ($)", f"${total_in:,.0f}")
    col3.metric("🔴 إجمالي مصروفات المسجد العامة ($)", f"${total_out:,.0f}")
    
    st.write("---")
    st.subheader("👥 ملخص رواتب وحسابات الموظفين والعاملين ($)")
    emp_salaries_dict = pd.Series(df_emps_db.salary.values, index=df_emps_db.name).to_dict() if not df_emps_db.empty else {}
    
    distinct_ref_names = []
    if not df_trans.empty:
        distinct_ref_names = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] != '')]['ref_name'].unique().tolist()
    all_distinct_workers = list(set(list(emp_salaries_dict.keys()) + distinct_ref_names))
    
    if not all_distinct_workers:
        st.info("💡 لا توجد بيانات موظفين مسجلة حتى الآن.")
    else:
        headers = ["اسم الموظف / العامل", "الراتب المستحق ($)", "إجمالي ما تم صرفه ($)", "المتبقي له في الذمة ($)"]
        rows = []
        for worker in all_distinct_workers:
            assigned_salary = emp_salaries_dict.get(worker, 0.0)
            amount_paid = df_trans[(df_trans['account_type'] == 'رواتب الموظفين') & (df_trans['ref_name'] == worker) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            amount_remaining = assigned_salary - amount_paid
            display_name = worker if worker in emp_salaries_dict else f"{worker} (اسم محذوف)"
            rows.append([display_name, f"${assigned_salary:,.0f}", f"${amount_paid:,.0f}", f"${amount_remaining:,.0f}"])
        render_custom_html_table(headers, rows)
        
    st.write("---")
    st.subheader("🚰 ملخص المصروفات التشغيلية والأخرى ($)")
    if df_trans.empty or df_trans[df_trans['type'] == 'صرف'].empty:
        st.info("💡 لا توجد مصروفات مسجلة بعد.")
    else:
        df_ops = df_trans[(df_trans['type'] == 'صرف') & (df_trans['account_type'] == 'عام')]
        if df_ops.empty:
            st.info("💡 لا توجد مصروفات عامة مسجلة حتى الآن.")
        else:
            df_ops_grouped = df_ops.groupby('description')['total_usd'].sum().reset_index()
            headers = ["نوع المصروف / البيان", "إجمالي المبلغ المصروف ($)"]
            rows = [[row['description'], f"${row['total_usd']:,.0f}"] for _, row in df_ops_grouped.iterrows()]
            render_custom_html_table(headers, rows)

    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
    
    sh_paid, sh_rec, net_sheikh_status = calculate_sheikh_final_balance(df_trans)

    headers = ["الصندوق أو الحساب المالي", "الحالة المالية والاتزان ($)"]
    rows = []
    for f in df_funds['name']:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            if net_sheikh_status > 0:
                status_text = f"${net_sheikh_status:,.0f} (مستحق لك على المسجد)"
            elif net_sheikh_status < 0:
                status_text = f"${abs(net_sheikh_status):,.0f} (مطلب للمسجد - مدين)"
            else:
                status_text = "$0 (مسدد تماماً وجرى تصفيره)"
            rows.append(["👤 ذمة وسلف الشيخ عبد الكريم", status_text])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            rows.append([f, f"${(f_in - f_out):,.0f}"])
    render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    conn = get_db_connection()
    c = conn.cursor()
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    conn.close()
    
    st.info(f"رقم السند التلقائي القادم: {(max_id + 1) if max_id else 1}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now(), key="q_date_v36")
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="q_type_v36")
    
    usd_amount_raw = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0, value=None, placeholder="اكتب المبلغ بالدولار مباشرة...", key="q_usd_v36")
    lbp_amount_raw = col2.number_input("المبلغ بالليرة (ل.ل)", min_value=0.0, step=1000.0, value=None, placeholder="اكتب المبلغ بالليرة مباشرة...", key="q_lbp_v36")
    
    usd_amount = usd_amount_raw if usd_amount_raw is not None else 0.0
    lbp_amount = lbp_amount_raw if lbp_amount_raw is not None else 0.0
    
    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)
    
    if lbp_amount > 0:
        st.warning(f"📊 قيمة الليرة تعادل: {converted_instant:,.0f}$")
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list, key="q_fund_v36")
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"], key="q_acc_type_v36")
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        if emp_list: ref_name = st.selectbox("اختر الموظف", emp_list, key="q_emp_v36")
        else: st.error("⚠️ لا يوجد موظفون مسجلون.")
        
    description = st.text_area("البيان / التفاصيل", key="q_desc_v36")
    
    if st.button("حفظ السند المالي", key="q_save_btn_v36"):
        if total_calculated_usd == 0: st.error("الرجاء إدخال قيمة مالية.")
        elif not description: st.error("الرجاء إدخال البيان.")
        else:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT INTO transactions (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) VALUES (?,?,?,?,?,?,?,?,?)", (str(t_date), description, t_type, usd_amount, lbp_amount, total_calculated_usd, fund, account_type, ref_name))
            conn.commit()
            conn.close()
            st.success("تم حفظ السند المالي بنجاح!")
            safe_rerun()
            
    st.write("---")
    st.subheader("📋 حذف السندات المسجلة")
    conn = get_db_connection()
    df_raw = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC LIMIT 15", conn)
    conn.close()
    
    if df_raw.empty:
        st.info("💡 لا توجد قيود مسجلة بعد.")
    else:
        for idx, row in df_raw.iterrows():
            c1, c2, c3, c4 = st.columns([1, 2, 4, 1])
            c1.write(f"**🔢 سند:** {row['id']}")
            c2.write(f"**📅:** {row['date']}")
            details = f"【 {row['type']} 】 بمبلغ **{row['total_usd']:,.0f}$** | {row['description']}"
            if row['ref_name']: details += f" ({row['ref_name']})"
            c3.write(details)
            if c4.button("🗑️ حذف", key=f"del_v36_{row['id']}"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("DELETE FROM transactions WHERE id = ?", (row['id'],))
                conn.commit()
                conn.close()
                st.success("تم الحذف!")
                safe_rerun()

elif page == "💵 الصناديق":
    st.title("💵 إدارة وتفاصيل أرصدة الصناديق")
    conn = get_db_connection()
    df_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    conn.close()
    
    st.markdown("### 📊 الملخص العام للصناديق")
    headers = ["اسم الصندوق", "إجمالي المدفوع من جيب الشيخ / ايداع ($)", "إجمالي المسترد للشيخ / مصروف ($)", "الرصيد الصافي الحالي ($)"]
    rows = []
    for f in df_funds['name']:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            sh_paid, sh_rec, net_bal = calculate_sheikh_final_balance(df_trans)
            if net_bal > 0: text_bal = f"${net_bal:,.0f} (مستحق لك)"
            elif net_bal < 0: text_bal = f"${abs(net_bal):,.0f} (مطلوب منك)"
            else: text_bal = "$0 (مصفّر)"
            rows.append([f, f"${sh_paid:,.0f}", f"${sh_rec:,.0f}", text_bal])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            rows.append([f, f"${f_in:,.0f}", f"${f_out:,.0f}", f"${(f_in - f_out):,.0f}"])
    render_custom_html_table(headers, rows)

elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم التفصيلي")
    conn = get_db_connection()
    df_trans = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    conn.close()
    
    if df_trans.empty:
        st.info("💡 لا توجد عمليات مالية مسجلة على حساب الشيخ حتى الآن.")
    else:
        df_sheikh = df_trans[
            (df_trans['account_type'] == 'حساب الشيخ عبد الكريم') | 
            (df_trans['fund'] == 'ذمة وسلف الشيخ عبد الكريم')
        ]
        
        sh_paid, sh_rec, status = calculate_sheikh_final_balance(df_trans)
        
        if status > 0: st.success(f"⚖️ الميزان الحالي: المسجد مدين لك بمبلغ {status:,.0f}$ (مستحق لك على المسجد)")
        elif status < 0: st.warning(f"⚖️ الميزان الحالي: أنت مدين للمسجد بمبلغ {abs(status):,.0f}$ (مطلوب سداده للمسجد)")
        else: st.info("⚖️ الميزان الحالي: الحساب متقاص تماماً ($0) تم تصفيره بنجاح!")
        
        st.write("---")
        headers = ["رقم السند", "التاريخ", "الحركة المكتوبة", "الصندوق المستعمل", "البيان والطلب", "الإجمالي ($)"]
        rows = []
        for _, r in df_sheikh.iterrows():
            rows.append([r['id'], r['date'], r['type'], r['fund'], r['description'], f"${r['total_usd']:,.0f}"])
        render_custom_html_table(headers, rows)

elif page == "👥 الرواتب":
    st.title("👥 إدارة رواتب الموظفين والعاملين")
    st.subheader("📝 إضافة موظف جديد")
    col1, col2 = st.columns(2)
    emp_name = col1.text_input("اسم الموظف كاملاً", key="emp_n_v36")
    
    emp_salary_raw = col2.number_input("الراتب الشهري المحدد ($)", min_value=0, step=50, value=None, placeholder="مثال: 200...", key="emp_s_v36")
    emp_salary = emp_salary_raw if emp_salary_raw is not None else 0.0
    
    if st.button("حفظ الموظف الجديد", key="emp_save_v36"):
        if emp_name:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO employees (name, salary) VALUES (?, ?)", (emp_name, emp_salary))
            conn.commit()
            conn.close()
            st.success(f"تم حفظ الموظف {emp_name} بنجاح!")
            safe_rerun()

elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة")
    rep_type = st.selectbox("نوع التقرير المراد عرضه", ["يومي", "شهري", "سنوي"], key="rep_t_v36")
    conn = get_db_connection()
    df_report = pd.read_sql_query("SELECT * FROM transactions ORDER BY id DESC", conn)
    conn.close()
    
    if df_report.empty:
        st.info("💡 قاعدة البيانات فارغة تماماً ولا توجد قيود.")
    else:
        df_report['parsed_date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي":
            sel_date = st.date_input("اختر اليوم", datetime.now(), key="rep_d_v36")
            df_filtered = df_report[df_report['parsed_date'].dt.date == sel_date]
        elif rep_type == "شهري":
            sel_month = st.slider("اختر الشهر", 1, 12, int(datetime.now().month), key="rep_m_v36")
            df_filtered = df_report[df_report['parsed_date'].dt.month == sel_month]
        else:
            sel_year = st.number_input("حدد السنة", min_value=2020, value=int(datetime.now().year), key="rep_y_v36")
            df_filtered = df_report[df_report['parsed_date'].dt.year == sel_year]
            
        if df_filtered.empty:
            st.warning("⚠️ لا توجد معاملات مالية مسجلة لهذه الفترة.")
        else:
            headers = ["رقم السند", "التاريخ", "الحركة", "البيان والتفاصيل", "الصندوق", "الصافي ($)"]
            rows = []
            for _, r in df_filtered.iterrows():
                desc = r['description']
                if r['account_type'] == 'رواتب الموظفين': desc = f"راتب: {r['ref_name']} ({desc})"
                elif r['account_type'] == 'حساب الشيخ عبد الكريم': desc = f"حساب الشيخ: {desc}"
                rows.append([r['id'], r['date'], r['type'], desc, r['fund'], f"${r['total_usd']:,.0f}"])
            render_custom_html_table(headers, rows)

elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة وخيارات الأمان")
    
    new_rate = st.number_input("تحديث سعر صرف الدولار مقابل الليرة اللبنانية", value=dollar_rate, step=500.0, key="set_r_v36")
    if st.button("تحديث سعر الصرف الآن", key="set_save_r_v36"):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("UPDATE settings SET value=? WHERE key='dollar_rate'", (str(new_rate),))
        conn.commit()
        conn.close()
        st.success("تم تحديث سعر الصرف بنجاح!")
        safe_rerun()
        
    st.write("---")
    st.subheader("💾 استرجاع الحسابات المحفوظة والنسخ الاحتياطي")
    
    uploaded_file = st.file_uploader("📤 اختر ملف المحفوظات (Backup) من هاتفك لاستعادة الحسابات فوراً", type=["db"], key="restore_uploader_v36")
    if uploaded_file is not None:
        if st.button("⚙️ اضغط هنا لتأكيد استعادة البيانات الآن", key="confirm_restore_btn_v36"):
            try:
                db_data = uploaded_file.getbuffer()
                with open(db_file_path, "wb") as f:
                    f.write(db_data)
                st.success("✅ تم استعادة كافة الحسابات القديمة بنجاح تام!")
                st.balloons()
                safe_rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء الاستعادة: {e}")
                
    st.write("---")
    if os.path.exists(db_file_path):
        with open(db_file_path, "rb") as f:
            db_bytes = f.read()
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        st.download_button(
            label="📥 تحميل نسخة احتياطية جديدة (Backup)",
            data=db_bytes,
            file_name=f"mosque_finance_backup_{current_date_str}.db",
            mime="application/octet-stream",
            key="backup_btn_v36"
        )

    st.write("---")
    st.subheader("⚠️ منطقة خطر: تصفير العمليات والقيود")
    confirm_reset = st.checkbox("أوافق على حذف وتصفير جميع السندات والعمليات الحسابية نهائياً من البرنامج", key="confirm_reset_v36")
    if st.button("🔴 تصفير كافة العمليات الحسابية الآن", key="reset_btn_v36"):
        if confirm_reset:
            try:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("DELETE FROM transactions")
                conn.commit()
                conn.close()
                st.success("✅ تم تصفير كافة العمليات بنجاح والبدء من جديد!")
                st.balloons()
                safe_rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء التصفير: {e}")
        else:
            st.error("⚠️ يرجى تحديد مربع الموافقة أولاً لتأكيد رغبتك بالتصفير.")
