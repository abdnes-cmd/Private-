import streamlit as st
import pandas as pd
import sqlite3
import tempfile
import os
from datetime import datetime
from supabase import create_client, Client
import io
from openpyxl.styles import PatternFill, Alignment, Font
from openpyxl.utils import get_column_letter

# إعدادات الصفحة والهوية البصرية
st.set_page_config(page_title="النظام المالي لجامع الإحسان", page_icon="🕌", layout="wide")

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

# الاتصال بـ Supabase
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

# الأسماء المعتمدة والثابتة للمسجد
DEFAULT_FUNDS = [
    "صندوق الجمعة",
    "المسجد العامة",
    "الزكاة",
    "الصدقات",
    "المشاريع",
    "ذمة وسلف الشيخ عبد الكريم"
]

def get_dollar_rate():
    try:
        res = supabase.table("settings").select("value").eq("key", "dollar_rate").execute()
        if res.data:
            return float(res.data[0]["value"])
    except Exception:
        pass
    return 89500.0

dollar_rate = get_dollar_rate()

def get_funds():
    return DEFAULT_FUNDS

def get_employees_df():
    try:
        res = supabase.table("employees").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data)
            if 'name' in df.columns:
                df['name'] = df['name'].astype(str).str.replace('*', '', regex=False).str.strip()
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "name", "salary"])

def get_transactions_df():
    try:
        res = supabase.table("transactions").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "date", "description", "type", "amount_usd", "amount_lbp", "total_usd", "fund", "account_type", "ref_name"])

def get_personal_transactions_df():
    try:
        res = supabase.table("personal_transactions").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "date", "description", "type", "amount_usd", "amount_lbp", "total_usd", "category"])

def get_bus_students_df():
    try:
        res = supabase.table("bus_students").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "name", "monthly_fee"])

def get_bus_payments_df():
    try:
        res = supabase.table("bus_payments").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "student_name", "year_month", "amount_usd", "amount_lbp", "total_usd", "payment_date", "notes"])

def safe_rerun():
    for rerun_func in ['rerun', 'experimental_rerun']:
        if hasattr(st, rerun_func):
            getattr(st, rerun_func)()
            break

def parse_float_input(val_str):
    if not val_str or str(val_str).strip() == "":
        return 0.0
    try:
        cleaned = str(val_str).replace(',', '').strip()
        return float(cleaned)
    except ValueError:
        return 0.0

def render_custom_html_table(headers, rows):
    html = "<table class='custom-table'><thead><tr>"
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"
    for row in rows:
        html += "<tr>"
        for cell in row:
            display_cell = "" if cell is None or cell == 0 or cell == "$0" or cell == "0.0$" else cell
            html += f"<td>{display_cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

def calculate_sheikh_final_balance(df):
    if df.empty:
        return 0.0, 0.0, 0.0, "المسجد العامة"
    
    paid_out = 0.0
    received_back = 0.0
    last_fund = "المسجد العامة"
    
    for _, row in df.iterrows():
        is_sheikh_fund = row.get('fund') == 'ذمة وسلف الشيخ عبد الكريم'
        is_sheikh_acc = row.get('account_type') == 'حساب الشيخ عبد الكريم'
        is_mosque_fund = row.get('fund') == 'المسجد العامة'
        
        t_type = row.get('type')
        t_usd = float(row.get('total_usd', 0.0) or 0.0)
        curr_fund = row.get('fund')
        
        if t_type == 'صرف' and (is_sheikh_fund or is_sheikh_acc):
            paid_out += t_usd
            if curr_fund and curr_fund != "ذمة وسلف الشيخ عبد الكريم":
                last_fund = curr_fund
        elif t_type == 'صرف' and is_mosque_fund and (is_sheikh_acc or is_sheikh_fund):
            received_back += t_usd
        elif t_type == 'قبض' and (is_sheikh_acc or is_sheikh_fund):
            received_back += t_usd
            if curr_fund and curr_fund != "ذمة وسلف الشيخ عبد الكريم":
                last_fund = curr_fund
            
    net_status = paid_out - received_back
    return paid_out, received_back, net_status, last_fund

# --- القائمة الجانبية ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>🕌 جامع الإحسان</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #004D40; font-weight: bold;'>مجدل عنجر</p>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "انتقل إلى:",
    [
        "🏠 الرئيسية (لوحة التحكم)",
        "📝 القيود اليومية",
        "💵 الصناديق وصندوق الجمعة",
        "👤 حساب الشيخ عبد الكريم",
        "👥 الرواتب",
        "🚌 باص المدرسة",
        "📊 التقارير",
        "👤 حسابي الشخصي",
        "⚙️ الإعدادات"
    ],
    key="side_nav_v70"
)

# زر إضافة لرفع رصيد الشيخ أحمد إلى 200$
st.sidebar.markdown("---")
if st.sidebar.button("رفع رصيد الشيخ أحمد إلى 200$"):
    try:
        payload = {
            "date": str(datetime.now().date()),
            "description": "رفع رصيد الشيخ أحمد من 150 إلى 200 دولار (تسوية تلقائية)",
            "type": "قبض",
            "amount_usd": 50.0,
            "amount_lbp": 0.0,
            "total_usd": 50.0,
            "fund": "ذمة وسلف الشيخ عبد الكريم",
            "account_type": "حساب الشيخ عبد الكريم",
            "ref_name": ""
        }
        supabase.table("transactions").insert(payload).execute()
        st.sidebar.success("تم رفع رصيد الشيخ أحمد إلى 200$ بنجاح!")
        safe_rerun()
    except Exception as e:
        st.sidebar.error(f"حدث خطأ: {e}")

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
    st.markdown("<h1 style='text-align: center;'>النظام المالي لجامع الإحسان</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد حالياً: {dollar_rate:,.0f} ل.ل للدولار</p>", unsafe_allow_html=True)
    st.write("---")

    df_trans = get_transactions_df()
    funds_list = get_funds()
    df_emps_db = get_employees_df()

    if not df_trans.empty:
        total_in = df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'قبض')]['total_usd'].sum()
        total_out = df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'صرف')]['total_usd'].sum()
    else:
        total_in, total_out = 0.0, 0.0
    current_balance = total_in - total_out

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 رصيد صندوق المسجد المدمج الحالي ($)", f"${current_balance:,.0f}" if current_balance != 0 else "-")
    col2.metric("🟢 إجمالي المقبوضات العامة (عدا الزكاة) ($)", f"${total_in:,.0f}" if total_in != 0 else "-")
    col3.metric("🔴 إجمالي المصروفات العامة (عدا الزكاة) ($)", f"${total_out:,.0f}" if total_out != 0 else "-")

    st.write("---")
    st.subheader("👥 ملخص رواتب وحسابات الموظفين والعاملين ($)")

    col_m, col_y = st.columns(2)
    selected_month = col_m.selectbox("📅 عرض رواتب شهر:", range(1, 13), index=datetime.now().month - 1, key="sal_m_select")
    selected_year = col_y.number_input("السنة:", min_value=2020, value=datetime.now().year, key="sal_y_select")

    emp_salaries_dict = pd.Series(df_emps_db.salary.values, index=df_emps_db.name).to_dict() if not df_emps_db.empty else {}

    if not df_trans.empty:
        df_trans['parsed_date'] = pd.to_datetime(df_trans['date'], errors='coerce')
        df_month_trans = df_trans[(df_trans['parsed_date'].dt.month == selected_month) & (df_trans['parsed_date'].dt.year == selected_year)]
        distinct_ref_names = df_month_trans[(df_month_trans['account_type'] == 'رواتب الموظفين') & (df_month_trans['ref_name'] != '')]['ref_name'].unique().tolist()
    else:
        df_month_trans = pd.DataFrame()
        distinct_ref_names = []

    all_distinct_workers = list(set(list(emp_salaries_dict.keys()) + distinct_ref_names))

    if not all_distinct_workers:
        st.info("💡 لا توجد بيانات موظفين مسجلة لهذا الشهر.")
    else:
        headers = ["اسم الموظف / العامل", f"راتب شهر ({selected_month}/{selected_year}) ($)", "إجمالي ما تم صرفه له هذا الشهر ($)", "المتبقي له عن الشهر ($)"]
        rows = []
        for worker in all_distinct_workers:
            assigned_salary = emp_salaries_dict.get(worker, 0.0)
            amount_paid_this_month = df_month_trans[(df_month_trans['account_type'] == 'رواتب الموظفين') & (df_month_trans['ref_name'] == worker) & (df_month_trans['type'] == 'صرف')]['total_usd'].sum() if not df_month_trans.empty else 0.0
            amount_remaining = assigned_salary - amount_paid_this_month
            display_name = worker if worker in emp_salaries_dict else f"{worker} (اسم محذوف)"
            
            s_sal = f"${assigned_salary:,.0f}" if assigned_salary > 0 else "-"
            s_paid = f"${amount_paid_this_month:,.0f}" if amount_paid_this_month > 0 else "-"
            s_rem = f"${amount_remaining:,.0f}" if amount_remaining != 0 else "-"
            
            rows.append([display_name, s_sal, s_paid, s_rem])
        render_custom_html_table(headers, rows)

    st.write("---")
    st.subheader("🚰 ملخص المصروفات التشغيلية والأخرى ($)")
    if df_trans.empty or df_trans[df_trans['type'] == 'صرف'].empty:
        st.info("💡 لا توجد مصروفات مسجلة بعد.")
    else:
        df_ops = df_trans[(df_trans['type'] == 'صرف') & (df_trans['account_type'] == 'عام') & (df_trans['fund'] != 'الزكاة')]
        if df_ops.empty:
            st.info("💡 لا توجد مصروفات عامة مسجلة حتى الآن.")
        else:
            df_ops_grouped = df_ops.groupby('description')['total_usd'].sum().reset_index()
            headers = ["نوع المصروف / البيان", "إجمالي المبلغ المصروف ($)"]
            rows = [[row['description'], f"${row['total_usd']:,.0f}" if row['total_usd'] > 0 else "-"] for _, row in df_ops_grouped.iterrows()]
            render_custom_html_table(headers, rows)

    st.write("---")
    st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
    sh_paid, sh_rec, net_sheikh_status, last_fund_name = calculate_sheikh_final_balance(df_trans)

    headers = ["الصندوق أو الحساب المالي", "الحالة المالية والاتزان ($)"]
    rows = []
    for f in funds_list:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            if net_sheikh_status > 0:
                if last_fund_name == "الزكاة":
                    status_text = f"${net_sheikh_status:,.0f} (مستحق عليك لصندوق الزكاة)"
                else:
                    status_text = f"${net_sheikh_status:,.0f} (مستحق عليك للمسجد)"
            elif net_sheikh_status < 0:
                status_text = f"${abs(net_sheikh_status):,.0f} (مستحق لك على الجهة المستلفة)"
            else:
                status_text = "-"
            rows.append(["👤 ذمة وسلف الشيخ عبد الكريم", status_text])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            net_f = f_in - f_out
            rows.append([f, f"${f_in:,.0f}" if f_in > 0 else "-", f"${f_out:,.0f}" if f_out > 0 else "-", f"${net_f:,.0f}" if net_f != 0 else "-"])
    render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل وتعديل القيود اليومية للمسجد")
    
    funds_list = get_funds()
    df_emps = get_employees_df()
    emp_list = df_emps["name"].dropna().tolist() if not df_emps.empty else []
    df_trans = get_transactions_df()
    
    tab_add, tab_edit = st.tabs(["➕ إضافة سند جديد", "✏️ تعديل سند سابق"])
    
    with tab_add:
        max_id = df_trans["id"].max() if not df_trans.empty else 0
        st.info(f"رقم السند التلقائي القادم: {(max_id + 1) if pd.notnull(max_id) else 1}")

        t_type = st.selectbox("نوع العملية", ["صرف", "قبض"], key="add_t_type")

        if t_type == "صرف":
            account_options = ["عام", "رواتب الموظفين", "حساب الشيخ عبد الكريم"]
        else:
            account_options = ["عام", "حساب الشيخ عبد الكريم"]
