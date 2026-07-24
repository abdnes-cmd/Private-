import pandas as pd
import streamlit as st

st.set_page_config(page_title="إدارة مالية المسجد", layout="wide")

st.title("🕌 برنامج إدارة مالية المسجد والتقرير العام")

# --- القائمة الجانبية لإدخال البيانات ---
st.sidebar.header("📝 إدخال حركة جديدة")

date = st.sidebar.date_input("التاريخ")
description = st.sidebar.text_input("البيان (الوصف)", placeholder="مثال: مدخول جمعة، راتب الإمام...")
trans_type = st.sidebar.selectbox("نوع الحركة", ["وارد (مدخول)", "صادر (مصروفات/رواتب)"])
category = st.sidebar.selectbox(
    "التصنيف",
    ["صندوق الجمعة", "راتب الإمام", "راتب المؤذن", "مصروفات أخرى", "تبرعات عامة"],
)
exchange_rate = st.sidebar.number_input("سعر الصرف (ليرة/دولار)", value=89500, step=500)
amount_lbp = st.sidebar.number_input("المبلغ بالليرة اللبنانية", value=0, step=50000)

# حساب المبلغ بالدولار
amount_usd = amount_lbp / exchange_rate if exchange_rate > 0 else 0
st.sidebar.info(f"المبلغ بالدولار: ${amount_usd:,.2f}")

# تهيئة جدول البيانات في الجلسة
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(
        columns=[
            "التاريخ",
            "البيان",
            "التصنيف",
            "سعر الصرف",
            "الوارد (ليرة)",
            "الصادر (ليرة)",
            "الوارد ($)",
            "الصادر ($)",
        ]
    )

if st.sidebar.button("حفظ الحركة"):
    if description and amount_lbp > 0:
        in_lbp = amount_lbp if "وارد" in trans_type else 0
        out_lbp = amount_lbp if "صادر" in trans_type else 0
        in_usd = amount_usd if "وارد" in trans_type else 0
        out_usd = amount_usd if "صادر" in trans_type else 0

        new_row = {
            "التاريخ": date.strftime("%Y-%m-%d"),
            "البيان": description,
            "التصنيف": category,
            "سعر الصرف": exchange_rate,
            "الوارد (ليرة)": in_lbp,
            "الصادر (ليرة)": out_lbp,
            "الوارد ($)": in_usd,
            "الصادر ($)": out_usd,
        }

        st.session_state.transactions = pd.concat(
            [st.session_state.transactions, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        st.success("تم تسجيل الحركة بنجاح!")
    else:
        st.error("يرجى ملء البيان وتحديد المبلغ بشكل صحيح.")

# --- التقرير المالي العام ---
df = st.session_state.transactions

st.subheader("📊 التقرير المالي العام ($)")

total_in_usd = df["الوارد ($)"].sum() if not df.empty else 0.0
total_out_usd = df["الصادر ($)"].sum() if not df.empty else 0.0
balance_usd = total_in_usd - total_out_usd

col1, col2, col3 = st.columns(3)
col1.metric("إجمالي الواردات ($)", f"${total_in_usd:,.2f}")
col2.metric("إجمالي المصروفات ($)", f"${total_out_usd:,.2f}")
col3.metric(
    "صافي رصيد الصندوق ($)",
    f"${balance_usd:,.2f}",
    delta_color="normal" if balance_usd >= 0 else "inverse",
)

st.divider()

# --- جدول عرض الحركات ---
st.subheader("📋 سجل الحركة المالية التفصيلي (ليرة / دولار)")

if not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("لا توجد حركات تسجيل حتى الآن. استخدم القائمة الجانبية لإضافة بيانات.")
