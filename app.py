# --- حساب الإحصائيات مع استثناء الزكاة ---
if not df.empty:
    # التأكد من تهيئة الأعمدة وتجنب القيم الفارغة
    for col in ["المبلغ", "النوع", "الفئة"]:
        if col not in df.columns:
            df[col] = 0 if col == "المبلغ" else ""
            
    df["المبلغ"] = pd.to_numeric(df["المبلغ"], errors='coerce').fillna(0)
    
    # 1. تصفية البيانات لاستثناء "الزكاة" من الحسبة العامة للصندوق
    df_no_zakat = df[df["الفئة"] != "الزكاة"]
    
    # 2. حساب المدخولات والمصروفات العامة (بدون الزكاة)
    total_income_general = df_no_zakat[df_no_zakat["النوع"] == "وارد"]["المبلغ"].sum()
    total_expense_general = df_no_zakat[df_no_zakat["النوع"] == "صادر"]["المبلغ"].sum()
    balance_general = total_income_general - total_expense_general
    
    # 3. حساب صندوق الزكاة بشكل منفصل تماماً
    df_zakat = df[df["الفئة"] == "الزكاة"]
    zakat_income = df_zakat[df_zakat["النوع"] == "وارد"]["المبلغ"].sum()
    zakat_expense = df_zakat[df_zakat["النوع"] == "صادر"]["المبلغ"].sum()
    zakat_balance = zakat_income - zakat_expense
else:
    total_income_general = 0.0
    total_expense_general = 0.0
    balance_general = 0.0
    zakat_balance = 0.0

# --- عرض مؤشرات الأداء (Metrics) في واجهة البرنامج ---

# الصف الأول: الصناديق العامة (بدون الزكاة)
st.markdown("### 📊 حالة الصناديق العامة (باستثناء الزكاة)")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #2e7d32;">
        <h4 style="margin:0; color:#2e7d32;">الواردات العامة (دون الزكاة)</h4>
        <h2 style="margin:10px 0 0 0;">${total_income_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #c62828; background-color: #ffebee;">
        <h4 style="margin:0; color:#c62828;">المصروفات العامة</h4>
        <h2 style="margin:10px 0 0 0;">${total_expense_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    color = "#2e7d32" if balance_general >= 0 else "#c62828"
    bg = "#f1f8e9" if balance_general >= 0 else "#ffebee"
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: {color}; background-color: {bg};">
        <h4 style="margin:0; color:{color};">الرصيد العام المتوفر</h4>
        <h2 style="margin:10px 0 0 0;">${balance_general:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# الصف الثاني: صندوق الزكاة المستقل
st.markdown("### 🪙 صندوق الزكاة (مستقل شرعياً)")
col_z1, col_z2 = st.columns([1, 2])
with col_z1:
    st.markdown(f"""
    <div class="metric-card" style="border-right-color: #f57c00; background-color: #fff3e0;">
        <h4 style="margin:0; color:#e65100;">رصيد صندوق الزكاة الحالي</h4>
        <h2 style="margin:10px 0 0 0;">${zakat_balance:,.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
with col_z2:
    st.info("💡 يتم عزل أموال الزكاة هنا بشكل تلقائي لضمان صرفها في مصارفها الشرعية الثمانية فقط وعدم خلطها بمصاريف المسجد التشغيلية.")
