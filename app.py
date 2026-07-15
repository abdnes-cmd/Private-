import streamlit as st

# 1. إعدادات الصفحة الأساسية كأول أمر برمجي على الإطلاق
st.set_page_config(
    page_title="برنامج المسجد", 
    layout="wide"
)

# 2. تهيئة وتثبيت متغيرات الجلسة (Session State) فوراً لمنع خطأ SessionInfo
if "initialized" not in st.session_state:
    st.session_state["initialized"] = True

# 3. استيراد باقي المكتبات اللازمة للبرنامج بأمان
import pandas as pd
import sqlite3
from datetime import datetime
import os

# 4. تطبيق الهوية البصرية وتنسيق الواجهة (الأخضر والذهبي)
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
        border-radius: 5px;
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

# 5. عنوان البرنامج الرئيسي في الواجهة
st.title("🕌 برنامج المسجد لإدارة الأنشطة والدروس")
st.write("مرحباً بك يا شيخنا الفاضل في نظام إدارة شؤون المسجد.")

# --- هنا يبدأ ربط قاعدة البيانات والعمليات البرمجية الخاصة بك ---
# (يمكنك إضافة بقية الأزرار والجداول هنا)
