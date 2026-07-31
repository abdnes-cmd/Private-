from datetime import datetime
import os
import pandas as pd
import streamlit as st

# إعداد الصفحة
st.set_page_config(
    page_title="الصندوق الشخصي", page_icon="💰", layout="wide"
)

DATA_FILE = "personal_box_data.csv"


def load_data():
  if os.path.exists(DATA_FILE):
    try:
      df = pd.read_csv(DATA_FILE)
      required_columns = [
          "date",
          "type",
          "amount_usd",
          "original_amount",
          "currency",
          "category",
          "description",
          "notes",
      ]
      for col in required_columns:
        if col not in df.columns:
          return pd.DataFrame(columns=required_columns)
      return df
    except:
      return pd.DataFrame(
          columns=[
              "date",
              "type",
              "amount_usd",
              "original_amount",
              "currency",
              "category",
              "description",
              "notes",
          ]
      )
  else:
    return pd.DataFrame(
        columns=[
            "date",
            "type",
            "amount_usd",
            "original_amount",
            "currency",
            "category",
            "description",
            "notes",
        ]
    )


def save_data(df):
  df.to_csv(DATA_FILE, index=False)


df = load_data()

# عنوان التطبيق
st.title("💰 إدارة الصندوق الشخصي")
st.markdown("---")

# --- ميزة رفع ملف سابق لاستعادة البيانات ---
with st.expander("📁 استعادة البيانات (رفع ملف CSV أو Excel سابق)"):
  uploaded_file = st.file_uploader(
      "اختر ملف البيانات القديم", type=["csv", "xlsx"]
  )
  if uploaded_file is not None:
    try:
      if uploaded_file.name.endswith(".csv"):
        uploaded_df = pd.read_csv(uploaded_file)
      else:
        uploaded_df = pd.read_excel(uploaded_file)

      # التأكد من دمج البيانات بشكل سليم
      required_columns = [
          "date",
          "type",
          "amount_usd",
          "original_amount",
          "currency",
          "category",
          "description",
          "notes",
      ]
      # إذا كانت الأعمدة متوافقة
      if all(col in uploaded_df.columns for col in required_columns):
        df = pd.concat([df, uploaded_df], ignore_index=True).drop_duplicates()
        save_data(df)
        st.success("✅ تم استعادة ودمج البيانات بنجاح!")
        st.rerun()
      else:
        st.error(
            "❌ الأعمدة في الملف المرفوع غير متطابقة مع هيكل التطبيق."
        )
    except Exception as e:
      st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")

st.markdown("---")

# --- 1. حالة الصندوق والإجماليات في الأعلى ---
st.subheader("📊 حالة الصندوق والإجماليات")

if not df.empty:
  total_income = df[df["type"] == "مدخول"]["amount_usd"].sum()
  total_expense = df[df["type"] == "مصروف"]["amount_usd"].sum()
  net_balance = total_income - total_expense
else:
  total_income = 0.0
  total_expense = 0.0
  net_balance = 0.0

col1, col2, col3 = st.columns(3)
col1.metric("إجمالي المداخيل ($)", f"${total_income:,.2f}")
col2.metric("إجمالي المصاريف ($)", f"${total_expense:,.2f}")
col3.metric("الصافي الحالي ($)", f"${net_balance:,.2f}")

st.markdown("---")

# --- 2. إضافة معاملة جديدة ---
st.subheader("➕ إضافة معاملة جديدة")

with st.form("transaction_form", clear_on_submit=True):
  c1, c2, c3, c4 = st.columns(4)

  with c1:
    t_date = st.date_input("التاريخ", value=datetime.today())
    t_type = st.selectbox("النوع", ["مدخول", "مصروف"])

  with c2:
    currency = st.selectbox("عملة الدفع", ["دولار ($)", "ليرة لبنانية (ل.ل)"])
    t_amount = st.number_input("المبلغ المدفوع", min_value=0.0, step=1.0)

  with c3:
    exchange_rate = st.number_input(
        "سعر الصرف (ليرة/$)", min_value=1.0, value=89500.0, step=100.0
    )
    t_category = st.selectbox(
        "الفئة",
        [
            "راتب",
            "تجارة",
            "أكل وشرب",
            "فواتير",
            "مواصلات",
            "ترفيه",
            "متفرقات",
        ],
    )

  with c4:
    t_description = st.text_input("البيان / الوصف")
    t_notes = st.text_input("ملاحظات")

  submit_button = st.form_submit_button(label="حفظ المعاملة")

  if submit_button:
    if "ليرة" in currency:
      amount_usd = t_amount / exchange_rate if exchange_rate > 0 else 0
    else:
      amount_usd = t_amount

    new_row = {
        "date": str(t_date),
        "type": t_type,
        "amount_usd": round(amount_usd, 2),
        "original_amount": t_amount,
        "currency": currency,
        "category": t_category,
        "description": t_description,
        "notes": t_notes,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)
    st.success(f"✅ تم الحفظ! (المبلغ بالدولار: ${amount_usd:,.2f})")
    st.rerun()

st.markdown("---")

# --- 3. سجل المعاملات وخيارات الحذف ---
st.subheader("📋 جدول تنظيم المعاملات")

if not df.empty:
  display_df = df.reset_index().rename(columns={"index": "ID"})
  display_df["ID"] = display_df["ID"] + 1
  st.dataframe(display_df, use_container_width=True)

  st.markdown("### 🗑️ حذف معاملة")
  d_col1, d_col2 = st.columns([2, 1])
  with d_col1:
    delete_id = st.number_input(
        "أدخل رقم (ID) المعاملة المراد حذفها",
        min_value=1,
        max_value=len(df),
        step=1,
    )
  with d_col2:
    st.write("")
    st.write("")
    if st.button("حذف المعاملة"):
      df = df.drop(index=delete_id - 1).reset_index(drop=True)
      save_data(df)
      st.success(f"تم حذف المعاملة رقم {delete_id} بنجاح!")
      st.rerun()
else:
  st.info("ℹ️ لا توجد معاملات مسجلة حتى الآن.")
