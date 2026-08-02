import streamlit as st
import pandas as pd
import sqlite3
import tempfile
import os
from datetime import datetime
from supabase import create_client, Client

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
            return pd.DataFrame(res.data)
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

def safe_rerun():
    for rerun_func in ['rerun', 'experimental_rerun']:
        if hasattr(st, rerun_func):
            getattr(st, rerun_func)()
            break

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
        "💵 الصناديق",
        "👤 حساب الشيخ عبد الكريم",
        "👥 الرواتب",
        "📊 التقارير",
        "👤 حسابي الشخصي",
        "⚙️ الإعدادات"
    ],
    key="side_nav_v56"
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
    col1.metric("💰 رصيد صندوق المسجد المدمج الحالي ($)", f"${current_balance:,.0f}")
    col2.metric("🟢 إجمالي المقبوضات العامة (عدا الزكاة) ($)", f"${total_in:,.0f}")
    col3.metric("🔴 إجمالي المصروفات العامة (عدا الزكاة) ($)", f"${total_out:,.0f}")

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
            rows.append([display_name, f"${assigned_salary:,.0f}", f"${amount_paid_this_month:,.0f}", f"${amount_remaining:,.0f}"])
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
            rows = [[row['description'], f"${row['total_usd']:,.0f}"] for _, row in df_ops_grouped.iterrows()]
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
                status_text = "$0 (مسدد تماماً وجرى تصفيره)"
            rows.append(["👤 ذمة وسلف الشيخ عبد الكريم", status_text])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            rows.append([f, f"${(f_in - f_out):,.0f}"])
    render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
    st.title("📝 تسجيل القيود اليومية للمسجد")
    
    funds_list = get_funds()
    df_emps = get_employees_df()
    emp_list = df_emps["name"].tolist() if not df_emps.empty else []
    df_trans = get_transactions_df()
    
    max_id = df_trans["id"].max() if not df_trans.empty else 0
    st.info(f"رقم السند التلقائي القادم: {(max_id + 1) if pd.notnull(max_id) else 1}")

    with st.form("daily_form_v56", clear_on_submit=True):
        col1, col2 = st.columns(2)
        t_date = col1.date_input("التاريخ", datetime.now())
        t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"])

        usd_amount_raw = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0, value=0.0, placeholder="اكتب المبلغ بالدولار مباشرة...")
        lbp_amount_raw = col2.number_input("المبلغ بالليرة (ل.ل)", min_value=0.0, step=1000.0, value=0.0, placeholder="اكتب المبلغ بالليرة مباشرة...")

        usd_amount = usd_amount_raw if usd_amount_raw is not None else 0.0
        lbp_amount = lbp_amount_raw if lbp_amount_raw is not None else 0.0

        converted_instant = round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
        total_calculated_usd = round(usd_amount + converted_instant)

        if lbp_amount > 0:
            st.warning(f"📊 قيمة الليرة تعادل: {converted_instant:,.0f}$")

        fund = col1.selectbox("الصندوق المتأثر", funds_list)
        account_type = col2.selectbox("نوع الحساب", ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"])

        ref_name = ""
        if account_type == "رواتب الموظفين":
            if emp_list:
                ref_name = st.selectbox("اختر الموظف", emp_list)
            else:
                st.error("⚠️ لا يوجد موظفون مسجلون.")

        description = st.text_area("البيان / التفاصيل")

        submitted = st.form_submit_button("حفظ السند المالي للمسجد")
        
        if submitted:
            if total_calculated_usd == 0:
                st.error("الرجاء إدخال قيمة مالية.")
            elif not description:
                st.error("الرجاء إدخال البيان.")
            else:
                payload = {
                    "date": str(t_date),
                    "description": description,
                    "type": t_type,
                    "amount_usd": usd_amount,
                    "amount_lbp": lbp_amount,
                    "total_usd": total_calculated_usd,
                    "fund": fund,
                    "account_type": account_type,
                    "ref_name": ref_name
                }
                supabase.table("transactions").insert(payload).execute()
                st.success("تم حفظ السند المالي بنجاح في السحابة!")
                safe_rerun()

    st.write("---")
    st.subheader("📋 حذف السندات المسجلة")
    
    if df_trans.empty:
        st.info("💡 لا توجد قيود مسجلة بعد.")
    else:
        for idx, row in df_trans.head(15).iterrows():
            c1, c2, c3, c4 = st.columns([1, 2, 4, 1])
            c1.write(f"**🔢 سند:** {row['id']}")
            c2.write(f"**📅:** {row['date']}")

            usd_val = float(row['amount_usd']) if pd.notnull(row['amount_usd']) else 0.0
            lbp_val = float(row['amount_lbp']) if pd.notnull(row['amount_lbp']) else 0.0
            tot_val = float(row['total_usd']) if pd.notnull(row['total_usd']) else 0.0

            u_str = f"${usd_val:,.0f}" if usd_val > 0 else "-"
            l_str = f"{lbp_val:,.0f} ل.ل" if lbp_val > 0 else "-"

            desc_text = row['description']
            if row.get('ref_name'):
                desc_text += f" ({row['ref_name']})"

            details = f"【 {row['type']} 】  •  كاش: {u_str}  •  ليرة: {l_str}  •  الإجمالي: ${tot_val:,.0f}  •  {desc_text}"

            c3.write(details)
            if c4.button("🗑️ حذف", key=f"del_v56_{row['id']}"):
                supabase.table("transactions").delete().eq("id", row['id']).execute()
                st.success("تم الحذف!")
                safe_rerun()

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
    st.title("💵 إدارة وتفاصيل أرصدة الصناديق")
    df_trans = get_transactions_df()
    funds_list = get_funds()

    st.markdown("### 📊 الملخص العام للصناديق")
    headers = ["اسم الصندوق", "إجمالي المدفوع / ايداع ($)", "إجمالي المسترد / مصروف ($)", "الرصيد الصافي الحالي ($)"]
    rows = []
    for f in funds_list:
        if f == "ذمة وسلف الشيخ عبد الكريم":
            sh_paid, sh_rec, net_bal, last_f = calculate_sheikh_final_balance(df_trans)
            if net_bal > 0:
                if last_f == "الزكاة":
                    text_bal = f"${net_bal:,.0f} (مستحق عليك لصندوق الزكاة)"
                else:
                    text_bal = f"${net_bal:,.0f} (مستحق عليك للمسجد)"
            elif net_bal < 0:
                text_bal = f"${abs(net_bal):,.0f} (مستحق لك على الجهة المستلفة)"
            else:
                text_bal = "$0 (مصفّر)"
            rows.append([f, f"${sh_paid:,.0f}", f"${sh_rec:,.0f}", text_bal])
        else:
            f_in = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'قبض')]['total_usd'].sum() if not df_trans.empty else 0.0
            f_out = df_trans[(df_trans['fund'] == f) & (df_trans['type'] == 'صرف')]['total_usd'].sum() if not df_trans.empty else 0.0
            rows.append([f, f"${f_in:,.0f}", f"${f_out:,.0f}", f"${(f_in - f_out):,.0f}"])
    render_custom_html_table(headers, rows)

# --- 4. حساب الشيخ ---
elif page == "👤 حساب الشيخ عبد الكريم":
    st.title("👤 كشف حساب الشيخ عبد الكريم التفصيلي")
    df_trans = get_transactions_df()

    if df_trans.empty:
        st.info("💡 لا توجد عمليات مالية مسجلة على حساب الشيخ حتى الآن.")
    else:
        df_sheikh = df_trans[(df_trans['account_type'] == 'حساب الشيخ عبد الكريم') | (df_trans['fund'] == 'ذمة وسلف الشيخ عبد الكريم')]
        sh_paid, sh_rec, status, last_f = calculate_sheikh_final_balance(df_trans)

        if status > 0:
            if last_f == "الزكاة":
                st.warning(f"⚖️ الميزان الحالي: أنت مدين بمبلغ {status:,.0f}$ (مستحق عليك لصندوق الزكاة)")
            else:
                st.warning(f"⚖️ الميزان الحالي: أنت مدين بمبلغ {status:,.0f}$ (مستحق عليك للمسجد)")
        elif status < 0:
            st.success(f"⚖️ الميزان الحالي: مدين لك بمبلغ {abs(status):,.0f}$ (مستحق لك)")
        else:
            st.info("⚖️ الميزان الحالي: الحساب متقاص تماماً ($0) تم تصفيره بنجاح!")

        st.write("---")
        headers = ["رقم السند", "التاريخ", "الحركة", "الصندوق", "البيان والتفاصيل", "كاش ($)", "ليرة (ل.ل)", "الإجمالي ($)"]
        rows = []
        for _, r in df_sheikh.iterrows():
            val_u = float(r['amount_usd']) if pd.notnull(r['amount_usd']) else 0.0
            val_l = float(r['amount_lbp']) if pd.notnull(r['amount_lbp']) else 0.0
            val_t = float(r['total_usd']) if pd.notnull(r['total_usd']) else 0.0

            u_str = f"${val_u:,.0f}" if val_u > 0 else "-"
            l_str = f"{val_l:,.0f} ل.ل" if val_l > 0 else "-"

            rows.append([r['id'], r['date'], r['type'], r['fund'], r['description'], u_str, l_str, f"${val_t:,.0f}"])
        render_custom_html_table(headers, rows)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
    st.title("👥 إدارة رواتب الموظفين والعاملين")
    st.subheader("📝 إضافة موظف جديد")
    col1, col2 = st.columns(2)
    emp_name = col1.text_input("اسم الموظف كاملاً", key="emp_n_v56")
    emp_salary_raw = col2.number_input("الراتب الشهري المحدد ($)", min_value=0, step=50, value=0.0, placeholder="مثال: 200...", key="emp_s_v56")
    emp_salary = emp_salary_raw if emp_salary_raw is not None else 0.0

    if st.button("حفظ الموظف الجديد", key="emp_save_v56"):
        if emp_name:
            supabase.table("employees").upsert({"name": emp_name, "salary": emp_salary}).execute()
            st.success(f"تم حفظ الموظف {emp_name} بنجاح!")
            safe_rerun()

    st.write("---")
    st.subheader("📋 قائمة الموظفين المسجلين")
    df_emp_list = get_employees_df()

    if df_emp_list.empty:
        st.info("💡 لا يوجد موظفون مسجلون حالياً.")
    else:
        for idx, e_row in df_emp_list.iterrows():
            ec1, ec2, ec3 = st.columns([3, 2, 1])
            ec1.write(f"👤 **{e_row['name']}**")
            ec2.write(f"💵 الراتب: **${e_row['salary']:,.0f}**")
            if ec3.button("🗑️ حذف", key=f"del_emp_{e_row['id']}"):
                supabase.table("employees").delete().eq("id", e_row['id']).execute()
                st.success("تم الحذف!")
                safe_rerun()

# --- 6. التقارير ---
elif page == "📊 التقارير":
    st.title("📊 التقارير المالية والطباعة للمسجد")
    rep_type = st.selectbox("نوع التقرير المراد عرضه", ["يومي", "شهري", "سنوي"], key="rep_t_v56")
    df_report = get_transactions_df()

    if df_report.empty:
        st.info("💡 قاعدة البيانات فارغة تماماً ولا توجد قيود.")
    else:
        df_report['parsed_date'] = pd.to_datetime(df_report['date'])
        if rep_type == "يومي":
            sel_date = st.date_input("اختر اليوم", datetime.now(), key="rep_d_v56")
            df_filtered = df_report[df_report['parsed_date'].dt.date == sel_date]
        elif rep_type == "شهري":
            sel_month = st.slider("اختر الشهر", 1, 12, int(datetime.now().month), key="rep_m_v56")
            df_filtered = df_report[df_report['parsed_date'].dt.month == sel_month]
        else:
            sel_year = st.number_input("حدد السنة", min_value=2020, value=int(datetime.now().year), key="rep_y_v56")
            df_filtered = df_report[df_report['parsed_date'].dt.year == sel_year]

        if df_filtered.empty:
            st.warning("⚠️ لا توجد معاملات مالية مسجلة لهذه الفترة.")
        else:
            headers = ["رقم السند", "التاريخ", "الحركة", "البيان والتفاصيل", "الصندوق", "المبلغ كاش ($)", "المبلغ بالليرة (ل.ل)", "الإجمالي الموحد ($)"]
            rows = []

            for _, r in df_filtered.iterrows():
                desc = r['description']
                if r.get('account_type') == 'رواتب الموظفين':
                    desc = f"راتب: {r.get('ref_name', '')} ({desc})"
                elif r.get('account_type') == 'حساب الشيخ عبد الكريم':
                    desc = f"حساب الشيخ: {desc}"

                val_usd = float(r['amount_usd']) if pd.notnull(r['amount_usd']) else 0.0
                val_lbp = float(r['amount_lbp']) if pd.notnull(r['amount_lbp']) else 0.0
                val_total = float(r['total_usd']) if pd.notnull(r['total_usd']) else 0.0

                usd_cash_str = f"${val_usd:,.0f}" if val_usd > 0 else "-"
                lbp_str = f"{val_lbp:,.0f} ل.ل" if val_lbp > 0 else "-"
                total_usd_str = f"${val_total:,.0f}"

                rows.append([r['id'], r['date'], r['type'], desc, r['fund'], usd_cash_str, lbp_str, total_usd_str])

            render_custom_html_table(headers, rows)

            st.write("---")
            df_filtered_non_zakat = df_filtered[df_filtered['fund'] != 'الزكاة']
            total_in_rep = df_filtered_non_zakat[df_filtered_non_zakat['type'] == 'قبض']['total_usd'].sum()
            total_out_rep = df_filtered_non_zakat[df_filtered_non_zakat['type'] == 'صرف']['total_usd'].sum()
            net_rep = total_in_rep - total_out_rep

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("🟢 إجمالي المقبوضات (عدا الزكاة)", f"${total_in_rep:,.0f}")
            mc2.metric("🔴 إجمالي المصروفات (عدا الزكاة)", f"${total_out_rep:,.0f}")
            mc3.metric("💰 الصافي للفترة", f"${net_rep:,.0f}")

            df_export = df_filtered.drop(columns=['parsed_date'])
            csv_data = df_export.to_csv(index=False).encode('utf-8-sig')

            st.download_button(
                label="📥 تحميل التقرير المعروض (CSV / Excel)",
                data=csv_data,
                file_name=f"mosque_report_{rep_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="export_csv_v56"
            )

# --- 7. حسابي الشخصي ---
elif page == "👤 حسابي الشخصي":
    st.title("👤 حسابي الشخصي (مداخيل ومصاريف خاصة)")
    st.markdown("هذا القسم خاص بك وحدك لإدارة مدخولك ومصاريفك الشخصية بعيداً عن حسابات المسجد.")
    st.write("---")

    df_personal = get_personal_transactions_df()

    if not df_personal.empty:
        p_in = df_personal[df_personal['type'] == 'قبض (مدخول)']['total_usd'].sum()
        p_out = df_personal[df_personal['type'] == 'صرف (مصروف)']['total_usd'].sum()
    else:
        p_in, p_out = 0.0, 0.0
    p_balance = p_in - p_out

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("💰 صافي رصيدك الشخصي الحالي ($)", f"${p_balance:,.0f}")
    pc2.metric("🟢 إجمالي المداخيل الشخصية ($)", f"${p_in:,.0f}")
    pc3.metric("🔴 إجمالي المصاريف الشخصية ($)", f"${p_out:,.0f}")

    st.write("---")
    st.subheader("➕ إضافة حركة شخصية جديدة")

    with st.form("personal_form_v56", clear_on_submit=True):
        col1, col2 = st.columns(2)
        p_date = col1.date_input("تاريخ الحركة", datetime.now())
        p_type = col2.selectbox("نوع الحركة", ["قبض (مدخول)", "صرف (مصروف)"])

        p_usd_raw = col1.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0, value=0.0, placeholder="اكتب المبلغ بالدولار...")
        p_lbp_raw = col2.number_input("المبلغ بالليرة (ل.ل)", min_value=0.0, step=1000.0, value=0.0, placeholder="اكتب المبلغ بالليرة...")

        p_usd = p_usd_raw if p_usd_raw is not None else 0.0
        p_lbp = p_lbp_raw if p_lbp_raw is not None else 0.0

        p_conv = round(p_lbp / dollar_rate) if dollar_rate > 0 else 0
        p_total = round(p_usd + p_conv)

        if p_lbp > 0:
            st.warning(f"📊 قيمة الليرة تعادل: {p_conv:,.0f}$ (الإجمالي: ${p_total:,.0f})")

        p_category = st.text_input("التصنيف (مثال: راتب شخصي، أجار منزل، طعام...)")
        p_desc = st.text_area("البيان والتفاصيل الشخصية")

        p_submitted = st.form_submit_button("حفظ الحركة الشخصية")
        
        if p_submitted:
            if p_total == 0:
                st.error("الرجاء إدخال مبلغ صحيح.")
            elif not p_desc:
                st.error("الرجاء إدخال البيان.")
            else:
                payload = {
                    "date": str(p_date),
                    "description": p_desc,
                    "type": p_type,
                    "amount_usd": p_usd,
                    "amount_lbp": p_lbp,
                    "total_usd": p_total,
                    "category": p_category if p_category else "عام"
                }
                supabase.table("personal_transactions").insert(payload).execute()
                st.success("تم حفظ الحركة الشخصية بنجاح!")
                safe_rerun()

    st.write("---")
    st.subheader("📋 سجل الحركات الشخصية السابقة وعمليات الحذف")

    if df_personal.empty:
        st.info("💡 لا توجد حركات شخصية مسجلة بعد.")
    else:
        # عرض جدول ملون ومنسق للحركات الشخصية
        headers = ["رقم السند", "التاريخ", "نوع الحركة", "التصنيف", "البيان والتفاصيل", "المبلغ الإجمالي ($)"]
        rows = []
        for _, row in df_personal.iterrows():
            r_id = row.get('id', '')
            r_date = row.get('date', '')
            r_type = row.get('type', '')
            r_cat = row.get('category', 'عام')
            r_desc = row.get('description', '')
            r_tot = float(row.get('total_usd', 0.0))
            rows.append([f"#سند {r_id}", r_date, r_type, r_cat, r_desc, f"${r_tot:,.0f}"])
        
        render_custom_html_table(headers, rows)

        # قسم منظم لحذف السندات برقم السند لتجنب تكرار أزرار الحذف الفوضوية
        st.markdown("#### 🗑️ حذف حركة شخصية محددة")
        del_col1, del_col2 = st.columns([2, 1])
        personal_ids = df_personal['id'].tolist()
        selected_id_to_delete = del_col1.selectbox("اختر رقم السند المطلوب حذفه:", personal_ids, key="sel_del_pers_id")
        
        if del_col2.button("حذف السند المختار", key="btn_del_pers_action"):
            try:
                supabase.table("personal_transactions").delete().eq("id", selected_id_to_delete).execute()
                st.success(f"تم حذف السند رقم {selected_id_to_delete} بنجاح!")
                safe_rerun()
            except Exception as e:
                st.error(f"خطأ في الحذف: {e}")

# --- 8. الإعدادات ---
elif page == "⚙️ الإعدادات":
    st.title("⚙️ الإعدادات العامة وخيارات الاستيراد")

    new_rate = st.number_input("تحديث سعر صرف الدولار مقابل الليرة اللبنانية", value=dollar_rate, step=500.0, key="set_r_v56")
    if st.button("تحديث سعر الصرف الآن", key="set_save_r_v56"):
        supabase.table("settings").upsert({"key": "dollar_rate", "value": str(new_rate)}).execute()
        st.success("تم تحديث سعر الصرف بنجاح!")
        safe_rerun()

    st.write("---")
    st.subheader("📥 استيراد قيود المسجد من ملف (.db أو Excel / CSV)")
    
    uploaded_file = st.file_uploader("اختر ملف البيانات القديم للمسجد", key="import_file_v56")
    if uploaded_file is not None:
        if st.button("🚀 بدء رفع واستيراد القيود للسحابة", key="start_import_btn_v56"):
            try:
                imported_count = 0
                file_name_lower = uploaded_file.name.lower()
                
                if file_name_lower.endswith('.db') or file_name_lower.endswith('.sqlite'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    conn = sqlite3.connect(tmp_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    df_import = pd.DataFrame()
                    for table in tables:
                        t_name = table[0]
                        temp_df = pd.read_sql(f"SELECT * FROM {t_name}", conn)
                        if 'date' in temp_df.columns or 'description' in temp_df.columns or 'type' in temp_df.columns:
                            df_import = temp_df
                            break
                    if df_import.empty and tables:
                        df_import = pd.read_sql(f"SELECT * FROM {tables[0][0]}", conn)
                    conn.close()
                    os.unlink(tmp_path)
                elif 'csv' in file_name_lower or uploaded_file.type == 'text/csv':
                    df_import = pd.read_csv(uploaded_file)
                else:
                    df_import = pd.read_excel(uploaded_file)
                
                for _, row in df_import.iterrows():
                    r_date = str(row.get('date', row.get('التاريخ', datetime.now().date())))
                    r_desc = str(row.get('description', row.get('البيان والتفاصيل', 'قيد استيراد')))
                    r_type = str(row.get('type', row.get('الحركة', 'قبض')))
                    r_fund = str(row.get('fund', row.get('الصندوق', 'المسجد العامة')))
                    
                    r_usd = float(row.get('amount_usd', row.get('usd', 0.0)) or 0.0)
                    r_lbp = float(row.get('amount_lbp', row.get('lbp', 0.0)) or 0.0)
                    r_tot = float(row.get('total_usd', row.get('total', r_usd)) or r_usd)
                    
                    payload = {
                        "date": r_date[:10] if len(r_date) >= 10 else str(datetime.now().date()),
                        "description": r_desc,
                        "type": r_type if r_type in ['قبض', 'صرف'] else 'قبض',
                        "amount_usd": r_usd,
                        "amount_lbp": r_lbp,
                        "total_usd": r_tot,
                        "fund": r_fund if r_fund in DEFAULT_FUNDS else 'المسجد العامة',
                        "account_type": str(row.get('account_type', 'عام')),
                        "ref_name": str(row.get('ref_name', ''))
                    }
                    supabase.table("transactions").insert(payload).execute()
                    imported_count += 1
                
                st.success(f"✅ تم استيراد عدد {imported_count} قيد بنجاح إلى سحابة Supabase!")
                st.balloons()
                safe_rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء رفع الملف: {e}")

    st.write("---")
    st.subheader("⚠️ منطقة خطر: تصفير العمليات والقيود للمسجد")
    confirm_reset = st.checkbox("أوافق على حذف وتصفير جميع السندات والعمليات الحسابية للمسجد نهائياً", key="confirm_reset_v56")
    if st.button("🔴 تصفير كافة عمليات المسجد الآن", key="reset_btn_v56"):
        if confirm_reset:
            try:
                supabase.table("transactions").delete().neq("id", -1).execute()
                st.success("✅ تم تصفير كافة عمليات المسجد بنجاح!")
                st.balloons()
                safe_rerun()
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
        else:
            st.error("⚠️ يرجى تحديد مربع الموافقة أولاً.")
