# قائمة الصناديق المعتمدة والمطابقة لصورتك الأصلية
DEFAULT_FUNDS = [
    "المسجد العامة",
    "الزكاة",
    "الصدقات",
    "المشاريع",
    "ذمة وسلف الشيخ عبد الكريم"
]

def initialize_funds(cursor, conn):
    """دالة لإنشاء الصناديق بالأسماء الصحيحة تلقائياً"""
    for fund_name in DEFAULT_FUNDS:
        cursor.execute(
            "INSERT OR IGNORE INTO funds (name) VALUES (?)",
            (fund_name,)
        )
    conn.commit()
