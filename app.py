import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import base64

st.set_page_config(page_title="صندوق المسجد", page_icon="🕌", layout="wide")

# إعدادات Airtable
ENCODED_KEY = "cGF0bmtsZ05WT0xlWjJ1RGYuNTk2NjgzMDM5NmRmOGUxOGNhNzkwYzVmYWU1NDlhZDdjOTk3Y2YxZDFjYWFjMDI2MTE1OTFkNDIzM2ZjNzYyYg=="
AIRTABLE_API_KEY = base64.b64decode(ENCODED_KEY).decode("utf-8")
BASE_ID = "app8p8z76mWPa3fET"
TABLE_NAME = "Table 1"
headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"

# دالة جلب البيانات
def fetch_data():
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            records = response.json().get("records", [])
            data = []
            for r in records:
                fields = r.get("fields", {})
                desc_val = fields.get("البيان", fields.get("Name", ""))
                data.append({
                    "ID": r.get("id"),
                    "التاريخ": fields.get("التاريخ", ""),
                    "النوع": fields.get("النوع", ""),
                    "المبلغ": fields.get("المبلغ", 0),
                    "البيان": desc_val
                })
            df = pd.DataFrame(data)
            if not df.empty:
                return df[["ID", "التاريخ", "النوع", "المبلغ", "البيان"]]
            return df
        return pd.DataFrame()
    except: 
        return pd.DataFrame()

# دالة حذف سجل معين
def delete_record(record_id):
    try:
        delete_url = f"{url}/{record_id}"
        res = requests.delete(delete_url, headers=headers)
        return res.status_code == 200
    except:
        return False

# --- واجهة التطبيق ---
st.title("🕌 صندوق المسجد والشؤون المالية")

df = fetch_data()

# 1. لوحة التحكم في الأعلى (احتساب الكسور بدقة)
if not df.empty:
    df['المبلغ'] = pd.to_numeric(df['المبلغ'], errors='coerce').fillna(0.0)
    income = df[df['النوع'] == 'المدخول']['المبلغ'].sum()
    expense = df[df['النوع'] == 'المصروف']['المبلغ'].sum()
    balance = income - expense
else:
    income, expense, balance = 0.0, 0.0, 0.0

col1, col2, col3 = st.columns(3)
col1.metric("🟢 إجمالي المقبوضات (المدخول)", f"{income:,.2f}")
col2.metric("🔴 إجمالي المدفوعات (المصروف)", f"{expense:,.2f}")
col3.metric("💰 الرصيد المتبقي في الصندوق", f"{balance:,.2f}")

st.markdown("---")

# 2. أزرار المعاملات والإدارة
tab1, tab2, tab3 = st.tabs(["➕ تسجيل معاملة جديدة", "🗑️ حذف معاملة من الصندوق", "⚙️ إدارة الصندوق"])

with tab1:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        amount = c1.number_input("المبلغ (يدعم الكسور)", min_value=0.01, step=0.01, format="%.2f")
        trans_type = c2.selectbox("نوع المعاملة", ["المصروف", "المدخول"])
        date = st.date_input("التاريخ", datetime.today())
        desc = st.text_input("البيان (تفاصيل المعاملة)")
        
        if st.form_submit_button("إضافة إلى الصندوق"):
            if desc:
                payload = {
                    "records": [{
                        "fields": {
                            "Name": desc,
                            "البيان": desc,
                            "النوع": trans_type,
                            "المبلغ": float(amount),
                            "التاريخ": date.strftime("%Y-%m-%d")
                        }
                    }]
                }
                requests.post(url, headers=headers, json=payload)
                st.success("تمت الإضافة بنجاح!")
                st.rerun()
            else:
                st.warning("الرجاء كتابة بيان المعاملة أولاً.")

with tab2:
    st.subheader("🗑️ حذف معاملة خاطئة")
    if not df.empty:
        options = []
        for idx, row in df.iterrows():
            options.append(f"{row['التاريخ']} | {row['النوع']} | {row['المبلغ']} | {row['البيان']}")
        
        selected_option = st.selectbox("اختر المعاملة المراد حذفها نهائياً:", options)
        
        selected_index = options.index(selected_option)
        selected_id = df.iloc[selected_index]["ID"]
        
        if st.button("حذف المعاملة المحددة", type="primary"):
            if delete_record(selected_id):
                st.success("تم حذف المعاملة وتحديث الصندوق!")
                st.rerun()
            else:
                st.error("حدث خطأ أثناء محاولة الحذف.")
    else:
        st.info("لا توجد معاملات مسجلة لحذفها.")

with tab3:
    if st.button("🔄 تحديث الصندوق"): 
        st.rerun()
    if st.button("🚨 تصفير صندوق المسجد بالكامل", type="primary"):
        if not df.empty:
            for r_id in df["ID"]: 
                requests.delete(f"{url}/{r_id}", headers=headers)
            st.rerun()

st.markdown("---")

# 3. عرض الجدول بالتفصيل
st.subheader("📊 دفتر قيود صندوق المسجد")
if not df.empty:
    display_df = df.drop(columns=["ID"])
    st.dataframe(display_df, use_container_width=True)
else:
    st.info("صندوق المسجد فارغ حالياً.")
