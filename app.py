# افترض أن اسم العمود الذي يحدد نوع الحركة هو 'نوع' أو 'الحركة'، وعمود المبلغ هو 'المبلغ'
# قم بتعديل أسماء الأعمدة أدناه لتعطابق الأسماء الموجودة لديك في الملف

# حساب إجمالي المقبوضات (القبض)
total_in = df[df['نوع الحركة'] == 'قبض']['المبلغ'].sum()

# حساب إجمالي المصروفات (الصرف)
total_out = df[df['نوع الحركة'] == 'صرف']['المبلغ'].sum()

# حساب الصافي (المقبوضات - المصروفات)
net_balance = total_in - total_out

# عرض النتائج بشكل منظم في واجهة Streamlit
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="إجمالي المقبوضات", value=f"${total_in:,.2f}")

with col2:
    st.metric(label="إجمالي المصروفات", value=f"${total_out:,.2f}")

with col3:
    st.metric(label="الصافي في الصندوق", value=f"${net_balance:,.2f}")
