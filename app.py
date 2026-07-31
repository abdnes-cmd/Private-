from datetime import datetime
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="الصندوق الشخصي المطور", page_icon="💼", layout="wide"
)

FILE_PATH = "my_cash_box.csv"


def load_data():
  if os.path.exists(FILE_PATH):
    try:
      return pd.read_csv(FILE_PATH)
    except:
      return pd.DataFrame()
  return pd.DataFrame()


def save_data(df):
  df.to_csv(FILE_PATH, index=False)


df = load_data()

st.title("💼 إدارة الصندوق الشخصي (النسخة المطورة)")
st.markdown("---")

# --- زر رفع واستعادة الملفات البارز ---
st.info(
    "💡 استعد بياناتك القديمة فوراً برفع ملف الـ CSV أو Excel الخاص بك هنا:"
)
uploaded_file = st.file_uploader(
    "اختر الملف (CSV أو Excel)", type=["csv", "xlsx"]
)

if uploaded_file is not None:
  try:
    if uploaded_file.name.endswith(".csv"):
      imported_df = pd.read_csv(uploaded_file)
    else:
      imported_df = pd.read_excel(uploaded_file)

    if not imported_df.empty:
      df = pd.concat([df, imported_df], ignore_index=True)
      save_data(df)
      st.success(
          "🎉 تمت استعادة ودمج البيانات بنجاح تام! جاري تحديث الصفحة..."
      )
      st.rerun()
  except Exception as ex:
    st.error(f"خطأ في قراءة الملف: {ex}")

st.markdown("---")

# --- الإجماليات ---
st.subheader("📊 الملخص المالي")
if not df.empty and "amount_usd" in df.columns:
  df["amount_usd"] = pd.to_numeric(df["amount_usd"], errors="coerce").fillna(0)
  inc = df[df["type"] == "مدخول"]["amount_usd"].sum()
  exp = df[df["type"] == "مصروف"]["amount_usd"].sum()
  net = inc - exp
else:
  inc, exp, net = 0.0, 0.0, 0.0

c1, c2, c3 = st.columns(3)
c1.metric("إجمالي المداخيل ($)", f"${inc:,.2f}")
c2.metric("إجمالي المصاريف ($)", f"${exp:,.2f}")
c3.metric("الصافي ($)", f"${net:,.2f}")

st.markdown("---")

# --- إضافة معاملة ---
st.subheader("➕ إضافة معاملة جديدة")
with st.form("main_form", clear_on_submit=True):
  col1, col2, col3, col4 = st.columns(4)
  with col1:
    d = st.date_input("التاريخ", value=datetime.today())
    t = st.selectbox("النوع", ["مدخول", "مصروف"])
  with col2:
    cur = st.selectbox("العملة", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
    amt = st.number_input("المبلغ", min_value=0.0, step=1.0)
  with col3:
    rate = st.number_input("سعر الصرف", min_value=1.0, value=89500.0, step=100.0)
    cat = st.selectbox(
        "الفئة",
        ["راتب", "تجارة", "أكل وشرب", "فواتير", "مواصلات", "ترفيه", "متفرقات"],
    )
  with col4:
    desc = st.text_input("البيان")
    notes = st.text_input("ملاحظات")

  if st.form_submit_button("حفظ"):
    final_usd = amt / rate if "ليرة" in cur else amt
    new_row = {
        "date": str(d),
        "type": t,
        "amount_usd": round(final_usd, 2),
        "original_amount": amt,
        "currency": cur,
        "category": cat,
        "description": desc,
        "notes": notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.success("تم الحفظ بنجاح!")
    st.rerun()

st.markdown("---")

# --- الجدول ---
st.subheader("📋 السجل")
if not df.empty:
  st.dataframe(
      df.reset_index().rename(columns={"index": "ID"}).assign(ID=lambda x: x["ID"] + 1),
      use_container_width=True,
  )
else:
  st.info("لا توجد بيانات حالياً.")
