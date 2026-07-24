# في صفحة الرئيسية (لوحة التحكم):

# حساب المبالغ بالليرة والدولار
total_in_usd = (
    df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'قبض')][
        'total_usd'
    ].sum()
    if not df_trans.empty
    else 0.0
)
total_in_lbp = (
    df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'قبض')][
        'amount_lbp'
    ].sum()
    if not df_trans.empty
    else 0.0
)

total_out_usd = (
    df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'صرف')][
        'total_usd'
    ].sum()
    if not df_trans.empty
    else 0.0
)
total_out_lbp = (
    df_trans[(df_trans['fund'] != 'الزكاة') & (df_trans['type'] == 'صرف')][
        'amount_lbp'
    ].sum()
    if not df_trans.empty
    else 0.0
)

current_balance_usd = total_in_usd - total_out_usd
current_balance_lbp = total_in_lbp - total_out_lbp

# عرض البطاقات بـ العملتين
col1, col2, col3 = st.columns(3)
col1.metric(
    "💰 الرصيد المدمج الحالي",
    f"${current_balance_usd:,.0f}",
    f"{current_balance_lbp:,.0f} ل.ل",
)
col2.metric(
    "🟢 إجمالي المقبوضات (عدا الزكاة)",
    f"${total_in_usd:,.0f}",
    f"{total_in_lbp:,.0f} ل.ل",
)
col3.metric(
    "🔴 إجمالي المصروفات (عدا الزكاة)",
    f"${total_out_usd:,.0f}",
    f"{total_out_lbp:,.0f} ل.ل",
)
