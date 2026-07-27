import sqlite3
from datetime import datetime
import pandas as pd
from supabase import Client, create_client
import streamlit as st

# إعدادات الصفحة والهوية البصرية
st.set_page_config(
    page_title="النظام المالي للمسجد", page_icon="🕌", layout="wide"
)

# تصميم مخصص لتعديل اتجاه وتلوين الواجهة
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# الاتصال بـ Supabase
@st.cache_resource
def get_supabase_client() -> Client:
  url = st.secrets["SUPABASE_URL"]
  key = st.secrets["SUPABASE_KEY"]
  return create_client(url, key)


supabase = get_supabase_client()


# دوال جلب البيانات
def get_dollar_rate():
  try:
    res = (
        supabase.table("settings")
        .select("value")
        .eq("key", "dollar_rate")
        .execute()
    )
    if res.data:
      return float(res.data[0]["value"])
  except Exception:
    pass
  return 89500.0


dollar_rate = get_dollar_rate()


def get_funds():
  try:
    res = supabase.table("funds").select("name").execute()
    if res.data:
      return [r["name"] for r in res.data]
  except Exception:
    pass
  return [
      "المسجد العامة",
      "الزكاة",
      "الصدقات",
      "المشاريع",
      "ذمة وسلف الشيخ عبد الكريم",
  ]


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
    res = (
        supabase.table("transactions")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    if res.data:
      return pd.DataFrame(res.data)
  except Exception:
    pass
  return pd.DataFrame(
      columns=[
          "id",
          "date",
          "description",
          "type",
          "amount_usd",
          "amount_lbp",
          "total_usd",
          "fund",
          "account_type",
          "ref_name",
      ]
  )


def safe_rerun():
  for rerun_func in ["rerun", "experimental_rerun"]:
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
    return 0.0, 0.0, 0.0

  paid_out = 0.0
  received_back = 0.0

  for _, row in df.iterrows():
    is_sheikh_fund = row.get("fund") == "ذمة وسلف الشيخ عبد الكريم"
    is_sheikh_acc = row.get("account_type") == "حساب الشيخ عبد الكريم"
    is_mosque_fund = row.get("fund") == "المسجد العامة"

    t_type = row.get("type")
    t_usd = float(row.get("total_usd", 0.0) or 0.0)

    if t_type == "صرف" and (
        is_sheikh_fund or (is_sheikh_acc and not is_mosque_fund)
    ):
      paid_out += t_usd
    elif t_type == "صرف" and is_mosque_fund and (is_sheikh_acc or is_sheikh_fund):
      received_back += t_usd
    elif t_type == "قبض" and (is_sheikh_acc or is_sheikh_fund):
      received_back += t_usd

  net_status = paid_out - received_back
  return paid_out, received_back, net_status


# --- القائمة الجانبية ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<h2 style='text-align: center; color: #D4AF37; margin-top: 0px;'>🕌 مسجد"
    " الإحسان</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    "<p style='text-align: center; color: #004D40; font-weight: bold;'>مجدل"
    " عنجر</p>",
    unsafe_allow_html=True,
)
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
        "⚙️ الإعدادات",
    ],
    key="side_nav_v43",
)

# --- 1. الصفحة الرئيسية ---
if page == "🏠 الرئيسية (لوحة التحكم)":
  st.markdown(
      "<h1 style='text-align: center;'>لوحة التحكم المالية (بالدولار)</h1>",
      unsafe_allow_html=True,
  )
  st.markdown(
      f"<p style='text-align: center; color: #C5A059;'>سعر الصرف المعتمد"
      f" حالياً: {dollar_rate:,.0f} ل.ل للدولار</p>",
      unsafe_allow_html=True,
  )
  st.write("---")

  df_trans = get_transactions_df()
  funds_list = get_funds()
  df_emps_db = get_employees_df()

  if not df_trans.empty:
    total_in = df_trans[
        (df_trans["fund"] != "الزكاة") & (df_trans["type"] == "قبض")
    ]["total_usd"].sum()
    total_out = df_trans[
        (df_trans["fund"] != "الزكاة") & (df_trans["type"] == "صرف")
    ]["total_usd"].sum()
  else:
    total_in, total_out = 0.0, 0.0
  current_balance = total_in - total_out

  col1, col2, col3 = st.columns(3)
  col1.metric(
      "💰 رصيد صندوق المسجد المدمج الحالي ($)", f"${current_balance:,.0f}"
  )
  col2.metric("🟢 إجمالي المقبوضات العامة (عدا الزكاة) ($)", f"${total_in:,.0f}")
  col3.metric("🔴 إجمالي المصروفات العامة (عدا الزكاة) ($)", f"${total_out:,.0f}")

  st.write("---")
  st.subheader("👥 ملخص رواتب وحسابات الموظفين والعاملين ($)")

  col_m, col_y = st.columns(2)
  selected_month = col_m.selectbox(
      "📅 عرض رواتب شهر:",
      range(1, 13),
      index=datetime.now().month - 1,
      key="sal_m_select",
  )
  selected_year = col_y.number_input(
      "السنة:", min_value=2020, value=datetime.now().year, key="sal_y_select"
  )

  emp_salaries_dict = (
      pd.Series(df_emps_db.salary.values, index=df_emps_db.name).to_dict()
      if not df_emps_db.empty
      else {}
  )

  if not df_trans.empty:
    df_trans["parsed_date"] = pd.to_datetime(df_trans["date"], errors="coerce")
    df_month_trans = df_trans[
        (df_trans["parsed_date"].dt.month == selected_month)
        & (df_trans["parsed_date"].dt.year == selected_year)
    ]
    distinct_ref_names = df_month_trans[
        (df_month_trans["account_type"] == "رواتب الموظفين")
        & (df_month_trans["ref_name"] != "")
    ]["ref_name"].unique().tolist()
  else:
    df_month_trans = pd.DataFrame()
    distinct_ref_names = []

  all_distinct_workers = list(
      set(list(emp_salaries_dict.keys()) + distinct_ref_names)
  )

  if not all_distinct_workers:
    st.info("💡 لا توجد بيانات موظفين مسجلة لهذا الشهر.")
  else:
    headers = [
        "اسم الموظف / العامل",
        f"راتب شهر ({selected_month}/{selected_year}) ($)",
        "إجمالي ما تم صرفه له هذا الشهر ($)",
        "المتبقي له عن الشهر ($)",
    ]
    rows = []
    for worker in all_distinct_workers:
      assigned_salary = emp_salaries_dict.get(worker, 0.0)
      amount_paid_this_month = (
          df_month_trans[
              (df_month_trans["account_type"] == "رواتب الموظفين")
              & (df_month_trans["ref_name"] == worker)
              & (df_month_trans["type"] == "صرف")
          ]["total_usd"].sum()
          if not df_month_trans.empty
          else 0.0
      )
      amount_remaining = assigned_salary - amount_paid_this_month
      display_name = (
          worker if worker in emp_salaries_dict else f"{worker} (اسم محذوف)"
      )
      rows.append([
          display_name,
          f"${assigned_salary:,.0f}",
          f"${amount_paid_this_month:,.0f}",
          f"${amount_remaining:,.0f}",
      ])
    render_custom_html_table(headers, rows)

  st.write("---")
  st.subheader("🚰 ملخص المصروفات التشغيلية والأخرى ($)")
  if df_trans.empty or df_trans[df_trans["type"] == "صرف"].empty:
    st.info("💡 لا توجد مصروفات مسجلة بعد.")
  else:
    df_ops = df_trans[
        (df_trans["type"] == "صرف")
        & (df_trans["account_type"] == "عام")
        & (df_trans["fund"] != "الزكاة")
    ]
    if df_ops.empty:
      st.info("💡 لا توجد مصروفات عامة مسجلة حتى الآن.")
    else:
      df_ops_grouped = (
          df_ops.groupby("description")["total_usd"].sum().reset_index()
      )
      headers = ["نوع المصروف / البيان", "إجمالي المبلغ المصروف ($)"]
      rows = [
          [row["description"], f"${row['total_usd']:,.0f}"]
          for _, row in df_ops_grouped.iterrows()
      ]
      render_custom_html_table(headers, rows)

  st.write("---")
  st.subheader("📌 أرصدة الصناديق الصافية والذمم المالية ($)")
  sh_paid, sh_rec, net_sheikh_status = calculate_sheikh_final_balance(df_trans)

  headers = ["الصندوق أو الحساب المالي", "الحالة المالية والاتزان ($)"]
  rows = []
  for f in funds_list:
    if f == "ذمة وسلف الشيخ عبد الكريم":
      if net_sheikh_status > 0:
        status_text = f"${net_sheikh_status:,.0f} (مستحق لك على المسجد)"
      elif net_sheikh_status < 0:
        status_text = f"${abs(net_sheikh_status):,.0f} (مطلب للمسجد - مدين)"
      else:
        status_text = "$0 (مسدد تماماً وجرى تصفيره)"
      rows.append(["👤 ذمة وسلف الشيخ عبد الكريم", status_text])
    else:
      f_in = (
          df_trans[(df_trans["fund"] == f) & (df_trans["type"] == "قبض")][
              "total_usd"
          ].sum()
          if not df_trans.empty
          else 0.0
      )
      f_out = (
          df_trans[(df_trans["fund"] == f) & (df_trans["type"] == "صرف")][
              "total_usd"
          ].sum()
          if not df_trans.empty
          else 0.0
      )
      rows.append([f, f"${(f_in - f_out):,.0f}"])
  render_custom_html_table(headers, rows)

# --- 2. القيود اليومية ---
elif page == "📝 القيود اليومية":
  st.title("📝 تسجيل القيود اليومية")

  funds_list = get_funds()
  df_emps = get_employees_df()
  emp_list = df_emps["name"].tolist() if not df_emps.empty else []
  df_trans = get_transactions_df()

  max_id = df_trans["id"].max() if not df_trans.empty else 0
  st.info(
      f"رقم السند التلقائي القادم: {(max_id + 1) if pd.notnull(max_id) else 1}"
  )

  col1, col2 = st.columns(2)
  t_date = col1.date_input("التاريخ", datetime.now(), key="q_date_v43")
  t_type = col2.selectbox("نوع العملية", ["قبض", "صرف"], key="q_type_v43")

  usd_amount_raw = col1.number_input(
      "المبلغ بالدولار ($)",
      min_value=0.0,
      step=1.0,
      value=None,
      placeholder="اكتب المبلغ بالدولار مباشرة...",
      key="q_usd_v43",
  )
  lbp_amount_raw = col2.number_input(
      "المبلغ بالليرة (ل.ل)",
      min_value=0.0,
      step=1000.0,
      value=None,
      placeholder="اكتب المبلغ بالليرة مباشرة...",
      key="q_lbp_v43",
  )

  usd_amount = usd_amount_raw if usd_amount_raw is not None else 0.0
  lbp_amount = lbp_amount_raw if lbp_amount_raw is not None else 0.0

  converted_instant = (
      round(lbp_amount / dollar_rate) if dollar_rate > 0 else 0
  )
  total_calculated_usd = round(usd_amount + converted_instant)

  if lbp_amount > 0:
    st.warning(f"📊 قيمة الليرة تعادل: {converted_instant:,.0f}$")

  fund = col1.selectbox("الصندوق المتأثر", funds_list, key="q_fund_v43")
  account_type = col2.selectbox(
      "نوع الحساب",
      ["عام", "حساب الشيخ عبد الكريم", "رواتب الموظفين"],
      key="q_acc_type_v43",
  )

  ref_name = ""
  if account_type == "رواتب الموظفين":
    if emp_list:
      ref_name = st.selectbox("اختر الموظف", emp_list, key="q_emp_v43")
    else:
      st.error("⚠️ لا يوجد موظفون مسجلون.")

  description = st.text_area("البيان / التفاصيل", key="q_desc_v43")

  if st.button("حفظ السند المالي", key="q_save_btn_v43"):
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
          "ref_name": ref_name,
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

      usd_val = (
          float(row["amount_usd"]) if pd.notnull(row["amount_usd"]) else 0.0
      )
      lbp_val = (
          float(row["amount_lbp"]) if pd.notnull(row["amount_lbp"]) else 0.0
      )
      tot_val = (
          float(row["total_usd"]) if pd.notnull(row["total_usd"]) else 0.0
      )

      u_str = f"${usd_val:,.0f}" if usd_val > 0 else "-"
      l_str = f"{lbp_val:,.0f} ل.ل" if lbp_val > 0 else "-"

      desc_text = row["description"]
      if row.get("ref_name"):
        desc_text += f" ({row['ref_name']})"

      details = f"【 {row['type']} 】  •  كاش: {u_str}  •  ليرة: {l_str}  •  الإجمالي: ${tot_val:,.0f}  •  {desc_text}"

      c3.write(details)
      if c4.button("🗑️ حذف", key=f"del_v43_{row['id']}"):
        supabase.table("transactions").delete().eq("id", row["id"]).execute()
        st.success("تم الحذف!")
        safe_rerun()

# --- 3. الصناديق ---
elif page == "💵 الصناديق":
  st.title("💵 إدارة وتفاصيل أرصدة الصناديق")
  df_trans = get_transactions_df()
  funds_list = get_funds()

  st.markdown("### 📊 الملخص العام للصناديق")
  headers = [
      "اسم الصندوق",
      "إجمالي المدفوع من جيب الشيخ / ايداع ($)",
      "إجمالي المسترد للشيخ / مصروف ($)",
      "الرصيد الصافي الحالي ($)",
  ]
  rows = []
  for f in funds_list:
    if f == "ذمة وسلف الشيخ عبد الكريم":
      sh_paid, sh_rec, net_bal = calculate_sheikh_final_balance(df_trans)
      if net_bal > 0:
        text_bal = f"${net_bal:,.0f} (مستحق لك)"
      elif net_bal < 0:
        text_bal = f"${abs(net_bal):,.0f} (مطلوب منك)"
      else:
        text_bal = "$0 (مصفّر)"
      rows.append([f, f"${sh_paid:,.0f}", f"${sh_rec:,.0f}", text_bal])
    else:
      f_in = (
          df_trans[(df_trans["fund"] == f) & (df_trans["type"] == "قبض")][
              "total_usd"
          ].sum()
          if not df_trans.empty
          else 0.0
      )
      f_out = (
          df_trans[(df_trans["fund"] == f) & (df_trans["type"] == "صرف")][
              "total_usd"
          ].sum()
          if not df_trans.empty
          else 0.0
      )
      rows.append([f, f"${f_in:,.0f}", f"${f_out:,.0f}", f"${(f_in - f_out):,.0f}"])
  render_custom_html_table(headers, rows)

# --- 4. حساب الشيخ ---
elif page == "👤 حساب الشيخ عبد الكريم":
  st.title("👤 كشف حساب الشيخ عبد الكريم التفصيلي")
  df_trans = get_transactions_df()

  if df_trans.empty:
    st.info("💡 لا توجد عمليات مالية مسجلة على حساب الشيخ حتى الآن.")
  else:
    df_sheikh = df_trans[
        (df_trans["account_type"] == "حساب الشيخ عبد الكريم")
        | (df_trans["fund"] == "ذمة وسلف الشيخ عبد الكريم")
    ]
    sh_paid, sh_rec, status = calculate_sheikh_final_balance(df_trans)

    if status > 0:
      st.success(
          f"⚖️ الميزان الحالي: المسجد مدين لك بمبلغ {status:,.0f}$ (مستحق لك على"
          " المسجد)"
      )
    elif status < 0:
      st.warning(
          f"⚖️ الميزان الحالي: أنت مدين للمسجد بمبلغ {abs(status):,.0f}$ (مطلوب"
          " سداده للمسجد)"
      )
    else:
      st.info("⚖️ الميزان الحالي: الحساب متقاص تماماً ($0) تم تصفيره بنجاح!")

    st.write("---")
    headers = [
        "رقم السند",
        "التاريخ",
        "الحركة",
        "الصندوق",
        "البيان والتفاصيل",
        "كاش ($)",
        "ليرة (ل.ل)",
        "الإجمالي ($)",
    ]
    rows = []
    for _, r in df_sheikh.iterrows():
      val_u = float(r["amount_usd"]) if pd.notnull(r["amount_usd"]) else 0.0
      val_l = float(r["amount_lbp"]) if pd.notnull(r["amount_lbp"]) else 0.0
      val_t = float(r["total_usd"]) if pd.notnull(r["total_usd"]) else 0.0

      u_str = f"${val_u:,.0f}" if val_u > 0 else "-"
      l_str = f"{val_l:,.0f} ل.ل" if val_l > 0 else "-"

      rows.append([
          r["id"],
          r["date"],
          r["type"],
          r["fund"],
          r["description"],
          u_str,
          l_str,
          f"${val_t:,.0f}",
      ])
    render_custom_html_table(headers, rows)

# --- 5. الرواتب ---
elif page == "👥 الرواتب":
  st.title("👥 إدارة رواتب الموظفين والعاملين")
  st.subheader("📝 إضافة موظف جديد")
  col1, col2 = st.columns(2)
  emp_name = col1.text_input("اسم الموظف كاملاً", key="emp_n_v43")
  emp_salary_raw = col2.number_input(
      "الراتب الشهري المحدد ($)",
      min_value=0,
      step=50,
      value=None,
      placeholder="مثال: 200...",
      key="emp_s_v43",
  )
  emp_salary = emp_salary_raw if emp_salary_raw is not None else 0.0

  if st.button("حفظ الموظف الجديد", key="emp_save_v43"):
    if emp_name:
      supabase.table("employees").upsert(
          {"name": emp_name, "salary": emp_salary}
      ).execute()
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
        supabase.table("employees").delete().eq("id", e_row["id"]).execute()
        st.success("تم الحذف!")
        safe_rerun()

# --- 6. التقارير ---
elif page == "📊 التقارير":
  st.title("📊 التقارير المالية والطباعة")
  rep_type = st.selectbox(
      "نوع التقرير المراد عرضه", ["يومي", "شهري", "سنوي"], key="rep_t_v43"
  )
  df_report = get_transactions_df()

  if df_report.empty:
    st.info("💡 قاعدة البيانات فارغة تماماً ولا توجد قيود.")
  else:
    df_report["parsed_date"] = pd.to_datetime(df_report["date"])
    if rep_type == "يومي":
      sel_date = st.date_input("اختر اليوم", datetime.now(), key="rep_d_v43")
      df_filtered = df_report[df_report["parsed_date"].dt.date == sel_date]
    elif rep_type == "شهري":
      sel_month = st.slider(
          "اختر الشهر", 1, 12, int(datetime.now().month), key="rep_m_v43"
      )
      df_filtered = df_report[df_report["parsed_date"].dt.month == sel_month]
    else:
      sel_year = st.number_input(
          "حدد السنة",
          min_value=2020,
          value=int(datetime.now().year),
          key="rep_y_v43",
      )
      df_filtered = df_report[df_report["parsed_date"].dt.year == sel_year]

    if df_filtered.empty:
      st.warning("⚠️ لا توجد معاملات مالية مسجلة لهذه الفترة.")
    else:
      headers = [
          "رقم السند",
          "التاريخ",
          "الحركة",
          "البيان والتفاصيل",
          "الصندوق",
          "المبلغ كاش ($)",
          "المبلغ بالليرة (ل.ل)",
          "الإجمالي الموحد ($)",
      ]
      rows = []

      for _, r in df_filtered.iterrows():
        desc = r["description"]
        if r.get("account_type") == "رواتب الموظفين":
          desc = f"راتب: {r.get('ref_name', '')} ({desc})"
        elif r.get("account_type") == "حساب الشيخ عبد الكريم":
          desc = f"حساب الشيخ: {desc}"

        val_usd = float(r["amount_usd"]) if pd.notnull(r["amount_usd"]) else 0.0
        val_lbp = float(r["amount_lbp"]) if pd.notnull(r["amount_lbp"]) else 0.0
        val_total = (
            float(r["total_usd"]) if pd.notnull(r["total_usd"]) else 0.0
        )

        usd_cash_str = f"${val_usd:,.0f}" if val_usd > 0 else "-"
        lbp_str = f"{val_lbp:,.0f} ل.ل" if val_lbp > 0 else "-"
        total_usd_str = f"${val_total:,.0f}"

        rows.append([
            r["id"],
            r["date"],
            r["type"],
            desc,
            r["fund"],
            usd_cash_str,
            lbp_str,
            total_usd_str,
        ])

      render_custom_html_table(headers, rows)

      st.write("---")
      sum_usd_cash = df_filtered["amount_usd"].sum()
      sum_lbp = df_filtered["amount_lbp"].sum()
      sum_total_final = df_filtered["total_usd"].sum()

      mc1, mc2, mc3 = st.columns(3)
      mc1.metric("مجموع الكاش ($)", f"${sum_usd_cash:,.0f}")
      mc2.metric("مجموع الليرة (ل.ل)", f"{sum_lbp:,.0f} ل.ل")
      mc3.metric("الإجمالي الشامل ($)", f"${sum_total_final:,.0f}")

      df_export = df_filtered.drop(columns=["parsed_date"])
      csv_data = df_export.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="📥 تحميل التقرير المعروض (CSV / Excel)",
          data=csv_data,
          file_name=f"mosque_report_{rep_type}_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          key="export_csv_v43",
      )

# --- 7. الإعدادات ---
elif page == "⚙️ الإعدادات":
  st.title("⚙️ الإعدادات العامة وخيارات الأمان")

  new_rate = st.number_input(
      "تحديث سعر صرف الدولار مقابل الليرة اللبنانية",
      value=dollar_rate,
      step=500.0,
      key="set_r_v43",
  )
  if st.button("تحديث سعر الصرف الآن", key="set_save_r_v43"):
    supabase.table("settings").upsert(
        {"key": "dollar_rate", "value": str(new_rate)}
    ).execute()
    st.success("تم تحديث سعر الصرف بنجاح!")
    safe_rerun()

  st.write("---")
  st.subheader("🚀 نقل البيانات القديمة إلى السحابة (Supabase)")
  st.info(
      "قم برفع ملف الـ .db الذي حملته في الخطوة الأولية لنقل جميع البيانات"
      " للسحابة بنقرة زر واحدة:"
  )

  db_upload = st.file_uploader(
      "اختر ملف المحفوظات (.db) لنقله للسحابة", type=["db"], key="migrate_db"
  )
  if db_upload is not None:
    if st.button("⚡ نقل البيانات الآن إلى السحابة"):
      try:
        # حفظ الملف مؤقتاً لقراءته
        with open("temp_migrate.db", "wb") as f:
          f.write(db_upload.getbuffer())

        conn = sqlite3.connect("temp_migrate.db")

        # 1. نقل القيود
        df_mig_trans = pd.read_sql_query("SELECT * FROM transactions", conn)
        trans_records = df_mig_trans.drop(columns=["id"], errors="ignore").to_dict(
            orient="records"
        )
        if trans_records:
          supabase.table("transactions").insert(trans_records).execute()

        # 2. نقل الموظفين
        try:
          df_mig_emp = pd.read_sql_query("SELECT * FROM employees", conn)
          emp_records = df_mig_emp.drop(
              columns=["id"], errors="ignore"
          ).to_dict(orient="records")
          if emp_records:
            supabase.table("employees").upsert(emp_records).execute()
        except Exception:
          pass

        conn.close()
        st.success("🎉 تم رفع ونقل جميع حساباتك وسنداتك إلى السحابة بنجاح!")
        st.balloons()
        safe_rerun()
      except Exception as e:
        st.error(f"حدث خطأ أثناء النقل: {e}")

  st.write("---")
  st.subheader("⚠️ منطقة خطر: تصفير العمليات والقيود")
  confirm_reset = st.checkbox(
      "أوافق على حذف وتصفير جميع السندات والعمليات الحسابية نهائياً من"
      " السحابة",
      key="confirm_reset_v43",
  )
  if st.button("🔴 تصفير كافة العمليات الحسابية الآن", key="reset_btn_v43"):
    if confirm_reset:
      try:
        supabase.table("transactions").delete().neq("id", -1).execute()
        st.success("✅ تم تصفير كافة العمليات بنجاح والبدء من جديد!")
        st.balloons()
        safe_rerun()
      except Exception as e:
        st.error(f"حدث خطأ أثناء التصفير: {e}")
    else:
      st.error("⚠️ يرجى تحديد مربع الموافقة أولاً لتأكيد رغبتك بالتصفير.")
