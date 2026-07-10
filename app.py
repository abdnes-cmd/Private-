import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# إعدادات الصفحة والهوية البصرية (الأخضر والذهبي)
st.set_page_config(page_title="النظام المالي للمسجد", page_icon="🕌", layout="wide")

# تصميم مخصص بالألوان المطلوبة وتعديل اتجاه وتلوين الواجهة
st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    h1, h2, h3, h4 { color: #004D40; font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { background-color: #004D40; color: #D4AF37; border-radius: 5px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #D4AF37; color: #004D40; }
    
    /* تنسيق جداول الـ HTML المخصصة لضمان عدم انهيار التطبيق */
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
    /* تلوين أعمدة الترويسة بشكل تبادلي (أخضر ثم ذهبي) */
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
    /* تلوين أسطر الجدول بشكل تبادلي (أخضر فاتح ثم أصفر فاتح) */
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

page = st.sidebar.radio("انتقل إلى:", ["🏠 الرئيسية (لوحة التحكم)", "📝 القيود اليومية", "💵 الصناديق", "👤 حساب الشيخ عبد الكريم", "👥 الرواتب", "📊 التقارير", "⚙️ الإعدادات"], key="side_navigation_v22")

# دالة مساعدة لإنشاء جداول HTML مستقرة لمنع انهيار السيرفر
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
    
    # 📋 الجدول 1: ملخص الرواتب للموظفين
    st.subheader("👥 ملخص رواتب وحسابات الموظفين والعاملين ($)")
    df_emps_db = pd.read_sql_query("SELECT name, salary FROM employees", conn)
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
    
    # 📊 الجدول 2: ملخص المصروفات التشغيلية
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
    
    # 📌 الجدول 3: أرصدة الصناديق والذمم
    st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
    df_funds = pd.read_sql_query("SELECT name FROM funds", conn)
    sheikh_personal_in = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
    sheikh_personal_out = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0

    headers = ["الصندوق أو الحساب المالي", "الحالة المالية والاتزان ($)"]
    rows = []
    for f in df_funds['name']:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            net_sheikh_status = sheikh_personal_in - sheikh_personal_out
            status_text = f"${net_sheikh_status:,.0f} (مستحق لك - دائن)" if net_sheikh_status > 0 else (f"${abs(net_sheikh_status):,.0f} (مطلوب منك - مدين)" if net_sheikh_status < 0 else "$0 (مسدد تماماً)")
            rows.append(["👤 ذمة وسلف الشيخ عبد الكريم", status_text])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            rows.append([f, f"${(f_in - f_out):,.0f}"])
    render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية")
    funds_list = [r[0] for r in c.execute("SELECT name FROM funds").fetchall()]
    emp_list = [r[0] for r in c.execute("SELECT name FROM employees").fetchall()]
    c.execute("SELECT MAX(id) FROM transactions")
    max_id = c.fetchone()[0]
    st.info(f"رقم السند التلقائي القادم: {(max_id + 1) if max_id else 1}")
    
    col1, col2 = st.columns(2)
    t_date = col1.date_input("التاريخ", datetime.now(), key="q_date_v22")
    t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="q_type_v22")
    usd_amount = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0, key="q_usd_v22")
    lbp_amount = col2.number_input("المبلغ بالليرة (ل.ل)", min_value=0.0, step=1000.0, key="q_lbp_v22")
    
    converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
    total_calculated_usd = round(usd_amount + converted_instant)
    
    if lbp_amount > 0:
        st.warning(f"📊 قيمة الليرة تعادل: {converted_instant:,.0f}$")
        
    fund = col1.selectbox("الصندوق المتأثر", funds_list, key="q_fund_v22")
    account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"], key="q_acc_type_v22")
    
    ref_name = ""
    if account_type == "رواتب الموظفين":
        if emp_list: ref_name = st.selectbox("اختر الموظف", emp_list, key="q_emp_v22")
        else: st.error("⚠️ لا يوجد موظفون مسجلون.")
        
    description = st.text_area("البيان / التفاصيل", key="q_desc_v22")
    
    if st.button("حفظ السند المالي", key="q_save_btn_v22"):
        if total_calculated_usd == 0: st.error("الرجاء إدخال قيمة مالية.")
        elif not description: st.error("الرجاء إدخال البيان.")
        else:
            c.execute("INSERT INTO transactions (date, description, type, amount_usd, amount_lbp, total_usd, fund, account_type, ref_name) VALUES (?,?,?,?,?,?,?,?,?)",
                      (str(t_date), description, t_type, usd_amount, lbp_amount,
