import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client

# إعدادات الصفحة والهوية البصرية للحساب الشخصي
st.set_page_config(page_title="الحساب الشخصي", page_icon="👤", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #fcf9f5; }
    h1, h2, h3, h4 { color: #5c4033; font-family: 'Cairo', sans-serif; text-align: right; direction: rtl; }
    .stButton>button { background-color: #5c4033; color: #ffffff; border-radius: 5px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #8b5a2b; color: #ffffff; }
    
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
        background-color: #5c4033 !important;
        color: #ffffff !important;
        border: 1px solid #4a3328;
    }
    .custom-table td {
        padding: 12px;
        border: 1px solid #e0e0e0;
        font-size: 15px;
        background-color: #fffdf9 !important;
        color: #333333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# الاتصال بـ Supabase (خاص بالحساب الشخصي)
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

def get_personal_transactions():
    try:
        res = supabase.table("personal_transactions").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "date", "description", "type", "amount", "category"])

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

st.title("👤 نظام إدارة الحساب الشخصي (على السحابة)")
st.write("---")

df_trans = get_personal_transactions()

# حساب الإجماليات
if not df_trans.empty:
    total_income = df_trans[df_trans['type'] == 'قبض']['amount'].sum()
    total_expense = df_trans[df_trans['type'] == 'صرف']['amount'].sum()
    net_balance = total_income - total_expense
else:
    total_income = 0.0
    total_expense = 0.0
    net_balance = 0.0

# عرض المؤشرات المالية
col1, col2, col3 = st.columns(3)
col1.metric("🟢 إجمالي الإيرادات ($)", f"${total_income:,.2f}")
col2.metric("🔴 إجمالي المصروفات ($)", f"${total_expense:,.2f}")
col3.metric("💰 الرصيد الحالي ($)", f"${net_balance:,.2f}")

st.write("---")

# لوحة التحكم الجانبية للإدخال
st.sidebar.markdown("<h2 style='text-align: center; color: #5c4033;'>⚙️ لوحة التحكم الشخصية</h2>", unsafe_allow_html=True)

with st.sidebar.form("personal_form", clear_on_submit=True):
    t_date = st.date_input("التاريخ", datetime.now())
    t_type = st.selectbox("نوع الحركة", ["قبض", "صرف"])
    category = st.selectbox("التصنيف", ["دخل شخصي", "مصروفات معيشية", "فواتير", "تسوية رصيد سابق", "أخرى"])
    amount = st.number_input("المبلغ ($)", min_value=0.0, step=1.0)
    description = st.text_area("البيان / التفاصيل")
    
    submit_button = st.form_submit_button("حفظ الحركة المالية")
    
    if submit_button:
        if amount <= 0:
            st.sidebar.error("الرجاء إدخال مبلغ صحيح.")
        elif not description:
            st.sidebar.error("الرجاء إدخال البيان.")
        else:
            payload = {
                "date": str(t_date),
                "description": description,
                "type": t_type,
                "amount": amount,
                "category": category
            }
            supabase.table("personal_transactions").insert(payload).execute()
            st.sidebar.success("تم الحفظ بنجاح في السحابة!")
            safe_rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📌 رفع رصيد حساب الشيخ أحمد")
if st.sidebar.button("رفع الرصيد إلى 200$ (إضافة تسوية 50$)"):
    try:
        payload = {
            "date": str(datetime.now().date()),
            "description": "رفع رصيد الشيخ أحمد من 150 إلى 200 دولار (تسوية تلقائية)",
            "type": "قبض",
            "amount": 50.0,
            "category": "تسوية رصيد سابق"
        }
        supabase.table("personal_transactions").insert(payload).execute()
        st.sidebar.success("تم رفع الرصيد بمقدار 50$ وأصبح الإجمالي 200$ مع الحفاظ على السجل القديم!")
        safe_rerun()
    except Exception as e:
        st.sidebar.error(f"حدث خطأ: {e}")

# عرض سجل الحركات
st.subheader("📋 سجل الحركات والحسابات الشخصية")
if not df_trans.empty:
    headers = ["رقم الحركة", "التاريخ", "النوع", "التصنيف", "البيان", "المبلغ ($)"]
    rows = []
    for _, r in df_trans.iterrows():
        rows.append([r['id'], r['date'], r['type'], r['category'], r['description'], f"${float(r['amount']):,.2f}"])
    render_custom_html_table(headers, rows)
    
    st.write("---")
    st.subheader("🗑️ حذف الحركات الخاطئة")
    for idx, row in df_trans.head(10).iterrows():
        c1, c2, c3 = st.columns([1, 4, 1])
        c1.write(f"حركة #{row['id']}")
        c2.write(f"{row['description']} (${row['amount']})")
        if c3.button("🗑️ حذف", key=f"del_p_{row['id']}"):
            supabase.table("personal_transactions").delete().eq("id", row['id']).execute()
            st.success("تم الحذف بنجاح!")
            safe_rerun()
else:
    st.info("💡 لا توجد حركات مسجلة بعد في الحساب الشخصي.")
