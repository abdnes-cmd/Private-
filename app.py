# --- تجهيز الصفوف للجدول مع حماية القيم الصفرية والنصية ---
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
  if r["account_type"] == "رواتب الموظفين":
    desc = f"راتب: {r['ref_name']} ({desc})"
  elif r["account_type"] == "حساب الشيخ عبد الكريم":
    desc = f"حساب الشيخ: {desc}"

  # --- معالجة المبلغ كاش بالدولار ---
  try:
    val_usd = float(r["amount_usd"]) if pd.notnull(r["amount_usd"]) else 0.0
  except (ValueError, TypeError):
    val_usd = 0.0

  usd_cash_str = f"${val_usd:,.0f}" if val_usd > 0 else "-"

  # --- معالجة المبلغ بالليرة اللبنانية ---
  try:
    val_lbp = float(r["amount_lbp"]) if pd.notnull(r["amount_lbp"]) else 0.0
  except (ValueError, TypeError):
    val_lbp = 0.0

  lbp_str = f"{val_lbp:,.0f} ل.ل" if val_lbp > 0 else "-"

  # --- معالجة الإجمالي الموحد ($) ---
  try:
    val_total = float(r["total_usd"]) if pd.notnull(r["total_usd"]) else 0.0
  except (ValueError, TypeError):
    val_total = 0.0

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
