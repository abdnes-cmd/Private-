            st.write("---")
            # فصل إجمالي المقبوضات عن إجمالي المصروفات محاسبياً
            total_in_rep = df_filtered[df_filtered['type'] == 'قبض']['total_usd'].sum()
            total_out_rep = df_filtered[df_filtered['type'] == 'صرف']['total_usd'].sum()
            net_rep = total_in_rep - total_out_rep
            
            sum_lbp = df_filtered['amount_lbp'].sum()

            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("🟢 إجمالي المقبوضات", f"${total_in_rep:,.0f}")
            mc2.metric("🔴 إجمالي المصروفات", f"${total_out_rep:,.0f}")
            mc3.metric("💰 الصافي للفترة", f"${net_rep:,.0f}")
            mc4.metric("💵 مجموع الليرة", f"{sum_lbp:,.0f} ل.ل")
