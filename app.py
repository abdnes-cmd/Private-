import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import urllib.parse

# إعدادات الصفحة
st.set_page_config(
    page_title="برنامج إدارة مسجد بلال بن رباح",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ضبط الاتجاه إلى العربية (RTL) باستخدام CSS بسيط
st.markdown("""
    <style>
    body {
        direction: RTL;
        text-align: right;
    }
    div.stButton > button:first-child {
        background-color: #2e7d32;
        color: white;
    }
    .metric-card {
        background-color: #f1f8e9;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #2e7d32;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

# --- إعدادات الاتصال بـ Airtable ---
AIRTABLE_PAT = st.secrets.get("AIRTABLE_PAT", "ضع_رمز_الوصول_الخاص_بك_هنا").strip()
BASE_ID = st.secrets.get("BASE_ID", "ضع_معرف_القاعدة_هنا").strip()
TABLE_NAME = st.secrets.get("TABLE_NAME", "ضع_اسم_الجدول_هنا").strip()

# ترميز اسم الجدول بشكل آمن جداً للروابط
ENCODED_TABLE_NAME = urllib.parse.quote(TABLE_NAME)
URL = f"https://api.airtable.com/v0/{BASE_ID}/{ENCODED_TABLE_NAME}"

# تنظيف الترويسات وإجبار بايثون على التعامل معها كـ latin-1 متوافق بعد التشفير الآمن
# هذا يمنع خطأ latin-1 codec can't encode تماماً
auth_header = f"Bearer {AIRTABLE_PAT}".encode('utf-8').decode('latin-1')

HEADERS = {
    "Authorization": auth_header,
    "Content-Type": "application/json"
}

# --- دالات التعامل مع قاعدة البيانات ---
def fetch_data():
    """جلب كافة السجلات من Airtable"""
    try:
        response = requests.get(URL, headers=HEADERS)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                row = r["fields"]
                row["id"] = r["id"] # حفظ معرف السجل
                data.append(row)
            return pd.DataFrame(data)
        else:
            st.error(f"خطأ في الاتصال بـ Airtable: {response.status_code} - {response.text}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"حدث خطأ غير متوقع أثناء جلب البيانات: {e}")
        return pd.DataFrame()

def insert_data(description, trans_type, amount, date, category):
    """إدخال سجل جديد في Airtable"""
    payload = {
        "fields": {
            "البيان": description,
            "النوع": trans_type,
            "المبلغ": float(amount),
            "التاريخ": str(date),
            "الفئة": category
        }
    }
    try:
        # إرسال البيانات مشفرة يدوياً بصيغة utf-8 لتفادي مشاكل الحروف العربية في الجسم (Body)
        binary_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(URL, headers=HEADERS, data=binary_data)
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"فشل الإدخال: {response.text}")
            return False
    except Exception as e:
        st.error(f"خطأ أثناء الإرسال: {e}")
        return False

# --- واجهة المستخدم الرئيسية ---
st.title("🕌 نظام إدارة صندوق المسجد والواردات")
st.write("برنامج ذكي لإدارة الحسابات وتتبع التبرعات والمصروفات بشكل مباشر.")
st.markdown("---")

# 1. جلب البيانات أولاً
df = fetch_data()

# 2. تهيئة متغيرات الحسابات بقيم افتراضية لتفادي أي أخطاء
total_income_general = 0.0
total_expense_general = 0.0
balance_general = 0.0
zakat_balance = 0.0

# 3. حساب الإحصائيات إذا كانت البيانات متوفرة وليست فارغة
if not df.empty:
    for col in ["المبلغ", "النوع", "الفئة"]:
        if col not in df.columns:
            df[col] = 0 if col == "المبلغ" else ""
            
    df["المبلغ"] = pd.to_numeric(df["المبلغ"], errors='coerce').fillna(0)
    
    # تصفية البيانات لاستثناء "الزكاة" من الحسبة العامة للصندوق
    df_no_zakat = df[df["الفئة"] != "الزكاة"]
    
    # حساب المدخولات والمصروفات العامة (بدون الزكاة)
    total_income_general = df_no_zakat[df_no_zakat["النوع"] == "وارد"]["المبلغ"].sum()
    total_expense_general = df_no_zakat[df_no_zakat["النوع"] == "صادر"]["المبلغ"].sum()
    balance_general = total_income_general - total_expense_general
    
    # حساب صندوق الزكاة بشكل منفصل تماماً
    df_zakat = df[df["الفئة"] == "الزكاة"]
    zakat_income = df_zakat[df_zakat["النوع"] == "وارد"]["المبلغ"].sum()
    zakat_expense = df_zakat[df_zakat["النوع"] == "صادر"]["المبلغ"].sum()
    zakat_balance = zakat_income - zakat_expense

# --- عرض مؤشرات الأداء (Metrics) ---

st.markdown("### 📊 حالة الصناديق العامة (باستثناء الزكاة)")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #2e7d32;">
        <h4 style="margin:0; color:#2e7d32;">الواردات العامة (دون الزكاة)</h4>
        <h2 style="margin:10px 0 0 0;">${total_income_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #c62828; background-color: #ffebee;">
        <h4 style="margin:0; color:#c62828;">المصروفات العامة</h4>
        <h2 style="margin:10px 0 0 0;">${total_expense_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "#2e7d32" if balance_general >= 0 else "#c62828"
    bg = "#f1f8e9" if balance_general >= 0 else "#ffebee"
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: {color}; background-color: {bg};">
        <h4 style="margin:0; color:{color};">الرصيد العام المتوفر</h4>
        <h2 style="margin:10px 0 0 0;">${balance_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

st.markdown("### 🪙 صندوق الزكاة (مستقل شرعياً)")
col_z1, col_z2 = st.columns([1, 2])
with col_z1:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #f57c00; background-color: #fff3e0;">
        <h4 style="margin:0; color:#e65100;">رصيد صندوق الزكاة الحالي</h4>
        <h2 style="margin:10px 0 0 0;">${zakat_balance:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
with col_z2:
    st.info("💡 يتم عزل أموال الزكاة هنا بشكل تلقائي لضمان صرفها في مصارفها الشرعية الثمانية فقط وعدم خلطها بمصاريف المسجد التشغيلية.")

st.markdown("---")

# تقسيم الصفحة لإدخال البيانات وعرضها
tab1, tab2 = st.tabs(["➕ إضافة حركة مالية جديدة", "📊 جدول الحركات التفصيلي"])

with tab1:
    st.subheader("تسجيل عملية مالية جديدة")
    with st.form("add_transaction_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            description = st.text_input("البيان / الوصف (مثال: تبرع صلاة الجمعة، شراء مازوت)")
            amount = st.number_input("المبلغ ($)", min_value=0.0, step=10.0, format="%.2f")
            category = st.selectbox("الفئة", ["المسجد العامة", "الصدقات", "المشاريع", "الزكاة", "ذمة وسلف"])
        
        with col_f2:
            trans_type = st.radio("نوع الحركة المادية", ["وارد", "صادر"])
            date = st.date_input("التاريخ", value=datetime.today())
            
        submit_btn = st.form_submit_button("تسجيل وحفظ في السحاب 💾")
        
        if submit_btn:
            if not description:
                st.warning("الرجاء إدخال البيان للعملية.")
            elif amount <= 0:
                st.warning("يجب أن يكون المبلغ أكبر من صفر.")
            else:
                with st.spinner("جاري حفظ البيانات في Airtable..."):
                    success = insert_data(description, trans_type, amount, date, category)
                    if success:
                        st.success("تم تسجيل العملية بنجاح! سيتم تحديث البيانات تلقائياً.")
                        st.rerun()

with tab2:
    st.subheader("سجل العمليات المالية الأخير")
    if not df.empty:
        df_display = df.copy()
        if "التاريخ" in df_display.columns:
            df_display = df_display.sort_values(by="التاريخ", ascending=False)
            
        cols_order = ["التاريخ", "البيان", "النوع", "المبلغ", "الفئة"]
        cols_order = [c for c in cols_order if c in df_display.columns]
        
        st.dataframe(df_display[cols_order], use_container_width=True)
    else:
        st.info("لا توجد بيانات مسجلة حالياً أو لم يتم الاتصال بقاعدة البيانات.")
