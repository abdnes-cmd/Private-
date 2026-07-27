import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# 1. إعداد الصفحة والربط بـ Supabase
st.set_page_config(page_title="النظام المالي للمسجد", layout="wide")

@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

st.title("🕌 النظام المالي للمسجد والمركز الإسلامي")

# 2. دالة جلب البيانات المعالجة
def load_data():
    try:
        res = supabase.table("transactions").select("*").order("id", desc=True).execute()
        if res.data:
            return pd.DataFrame(res.data)
    except Exception:
        pass
    return pd.DataFrame()

# 3. إدخال الحركة المالية بتفاصيل المشاريع والزكوات
st.subheader("📝 إدخال سند جديد (قبض / صرف)")

col1, col2 = st.columns(2)

with col1:
    trans_type = st.radio("نوع الحركة", ["قبض (إيراد)", "صرف (مصروف)"], horizontal=True)
    
    fund = st.selectbox(
        "الصندوق / المشروع المستهدف", 
        [
            "صندوق المسجد العام", 
            "صندوق بناء المركز الإسلامي", 
            "مشروع المقبرة", 
            "صندوق الزكاة والصدقات", 
            "مشروع الطاقة الشمسية والكهرباء", 
            "ذمة وسلف الشيخ عبد الكريم",
            "صناديق ومشاريع أخرى"
        ]
    )
    
    account_type = st.selectbox(
        "تصنيف الحساب / البند", 
        [
            "تبرعات واشتراكات", 
            "زكاة أموال / زكاة فطرة", 
            "صدقات وكفارات", 
            "صيانة وتشغيل", 
            "رواتب ومكافآت", 
            "سلفة / استرداد سلفة", 
            "مشتريات ومعدات", 
            "مصاريف عامة"
        ]
    )
    
    date_val = st.date_input("تاريخ السند", datetime.now())

with col2:
    amount_usd = st.number_input("المبلغ بالدولار ($)", min_value=0.0, step=1.0)
    amount_lbp = st.number_input("المبلغ بالليرة اللبنانية (ل.ل)", min_value=0, step=50000)
    dollar_rate = st.number_input("سعر الصرف (ل.ل لكل $)", min_value=1, value=89500)
    
    ref_name = st.text_input("اسم المتبرع / المستفيد / الجهة (اختياري)")
    description = st.text_area("البيان / تفاصيل الملاحظات")

# حساب المبالغ الإجمالية
total_in_usd = amount_usd + (amount_lbp / dollar_rate if dollar_rate > 0 else 0)
st.info(f"💵 **إجمالي القيمة المعادلة بالدولار:** `${total_in_usd:,.2f}`")

if st.button("💾 حفظ السند في السحابة", type="primary", use_container_width=True):
    if total_in_usd <= 0:
        st.warning("يرجى إدخال مبلغ أكبر من الصفر قبل الحفظ.")
    else:
        payload = {
            "date": str(date_val),
            "description": description,
            "type": trans_type,
            "amount_usd": amount_usd,
            "amount_lbp": amount_lbp,
            "total_usd": total_in_usd,
            "fund": fund,
            "account_type": account_type,
            "ref_name": ref_name
        }
        try:
            supabase.table("transactions").insert(payload).execute()
            st.success("تم حفظ السند بنجاح في السحابة! 🎉")
        except Exception as e:
            st.error("حدث خطأ أثناء الحفظ، يرجى التحقق من الاتصال.")

st.divider()

# 4. عرض القيود المعتادة
st.subheader("📊 كشف القيود والحركات المسجلة")

df = load_data()
if not df.empty:
    # إعادة ترتيب وتسمية الأعمدة لتناسب الواجهة العربية
    cols_map = {
        "id": "رقم السند",
        "date": "التاريخ",
        "type": "النوع",
        "fund": "الصندوق/المشروع",
        "account_type": "التصنيف",
        "amount_usd": "المبلغ ($)",
        "amount_lbp": "المبلغ (ل.ل)",
        "total_usd": "الإجمالي ($)",
        "ref_name": "الاسم/الجهة",
        "description": "البيان"
    }
    
    # تصفية وتنسيق الأعمدة المتاحة
    df_display = df[[c for c in cols_map.keys() if c in df.columns]].rename(columns=cols_map)
    st.dataframe(df_display, use_container_width=True)
else:
    st.info("لا توجد قيود مسجلة حالياً في السحابة.")
