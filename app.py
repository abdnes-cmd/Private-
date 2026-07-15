import streamlit as st

# 1. إعدادات الصفحة كأول أمر برمجي على الإطلاق لمنع تعارض الجلسة
st.set_page_config(
    page_title="برنامج المسجد", 
    layout="wide"
)

# 2. تهيئة وتثبيت متغيرات الجلسة (Session State) فوراً
if "initialized" not in st.session_state:
    st.session_state["initialized"] = True

# 3. الآن نستورد باقي المكتبات بأمان تام دون أي تعارض
import pandas as pd
import sqlite3
from datetime import datetime
import os

# 4. تصميم مخصص لتعديل اتجاه وتلوين الواجهة (الستايل الخاص بك)
st.markdown("""
<style>
    .main { 
        background-color: #f9fbf9; 
    }
    h1, h2, h3, h4 { 
        color: #004D40; 
    }
    .stButton>button { 
        background-color: #004D40; 
        color: white; 
    }
    .stButton>button:hover { 
        background-color: #00796B; 
        color: white; 
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        direction: rtl;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# هنا يكمل باقي كود برنامجك (السطر 22 وما بعده) كما هو دون أي تغيير
# --------------------------------------------------
