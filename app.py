import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# 1. إعداد الصفحة والربط بـ Supabase
st.set_page_config(page_title="النظام المالي للمسجد", layout="wide")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("🕌 النظام المالي للمسجد")

# 2. جلب البيانات من السحابة
@st.cache_data(ttl=2)
def load_data():
    res = supabase.table("transactions").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

# 3. إدخال الحركة المالية
st.subheader("📝 إدخال حركة جديدة")

col1, col2 = st.columns(2)
with col1:
    trans_type = st.radio("نوع الحركة", ["قبض (إيراد)", "صرف (مصروف)"], horizontal=True)
    fund = st.selectbox("الصندوق", ["صندوق المسجد العام", "صندوق بناء المركز الإسلامي", "صندوق المقبرة", "الزكاة", "ذمة وسلف الشيخ عبد الكريم"])
    date_val = st.date_input("التاريخ", datetime.now())

with col2:
    amount_usd = st.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0)
    amount_lbp = st.number_input("المبلغ بالليرة (ل.ل)", min_value=0, step=50000)
    description = st.text_area("البيان / التفاصيل")

if st.button("💾 حفظ السند", type="primary"):
    payload = {
        "date": str(date_val),
        "description": description,
        "type": trans_type,
        "amount_usd": amount_usd,
        "amount_lbp": amount_lbp,
        "total_usd": amount_usd + (amount_lbp / 89500),
        "fund": fund
    }
    supabase.table("transactions").insert(payload).execute()
    st.success("تم الحفظ بنجاح! 🎉")
    st.cache_data.clear()

st.divider()

# 4. عرض القيود المسجلة
st.subheader("📊 القيود المسجلة")
df = load_data()
if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد قيود مسجلة بعد.")
