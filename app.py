elif page == "📊 التقارير":
  st.title("📊 التقارير المالية والطباعة")
  rep_type = st.selectbox(
      "نوع التقرير المراد عرضه", ["يومي", "شهري", "سنوي"], key="rep_t_v39"
  )
  conn = get_db_connection()
  df_report = pd.read_sql_query(
      "SELECT * FROM transactions ORDER BY id DESC", conn
  )
  conn.close()

  if df_report.empty:
    st.info("💡 قاعدة البيانات فارغة تماماً ولا توجد قيود.")
  else:
    df_report["parsed_date"] = pd.to_datetime(df_report["date"])
    if rep_type == "يومي":
      sel_date = st.date_input("اختر اليوم", datetime.now(), key="rep_d_v39")
      df_filtered = df_report[df_report["parsed_date"].dt.date == sel_date]
    elif rep_type == "شهري":
      sel_month = st.slider(
          "اختر الشهر", 1, 12, int(datetime.now().month), key="rep_m_v39"
      )
      df_filtered = df_report[df_report["parsed_date"].dt.month == sel_month]
    else:
      sel_year = st.number_input(
          "حدد السنة",
          min_value=2020,
          value=int(datetime.now().year),
          key="rep_y_v39",
      )
      df_filtered = df_report[df_report["parsed_date"].dt.year == sel_year]

    if df_filtered.empty:
      st.warning("⚠️ لا توجد معاملات مالية مسجلة لهذه الفترة.")
    else:
      # --- رؤوس الجدول التفصيلي ---
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

        usd_cash_str = (
            f"${r['amount_usd']:,.0f}" if r["amount_usd"] > 0 else "-"
        )
        lbp_str = (
            f"{r['amount_lbp']:,.0f} ل.ل" if r["amount_lbp"] > 0 else "-"
        )
        total_usd_str = f"${r['total_usd']:,.0f}"

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

      # عرض الجدول بالحقول المنفصلة
      render_custom_html_table(headers, rows)

      # --- عرض ملخص مجموع الفترة ---
      st.write("---")
      sum_usd_cash = df_filtered["amount_usd"].sum()
      sum_lbp = df_filtered["amount_lbp"].sum()
      sum_total_final = df_filtered["total_usd"].sum()

      mc1, mc2, mc3 = st.columns(3)
      mc1.metric("مجموع المقبوض/المصروف كاش ($)", f"${sum_usd_cash:,.0f}")
      mc2.metric("مجموع المقبوض/المصروف (ل.ل)", f"{sum_lbp:,.0f} ل.ل")
      mc3.metric(
          "الإجمالي الموحد الشامل ($)",
          f"${sum_total_final:,.0f}",
          help="يشمل كاش الدولار + الليرة بعد تحويلها على سعر الصرف",
      )

      # --- تصدير إلى CSV دون خطأ مكتبة Excel ---
      df_export = df_filtered.drop(columns=["parsed_date"])
      csv_data = df_export.to_csv(index=False).encode("utf-8-sig")

      st.download_button(
          label="📥 تحميل التقرير المعروض (CSV / Excel)",
          data=csv_data,
          file_name=f"mosque_report_{rep_type}_{datetime.now().strftime('%Y%m%d')}.csv",
          mime="text/csv",
          key="export_csv_v39",
      )
