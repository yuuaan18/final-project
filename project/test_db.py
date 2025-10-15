import mysql.connector
from mysql.connector import Error

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # put your password if any
        database="techstore_pos"
    )
    if conn.is_connected():
        print("✅ Connected successfully to MySQL")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        print("Tables:", cursor.fetchall())
        conn.close()
    else:
        print("❌ Connection object exists but not connected")
except Error as e:
    print("❌ Database connection error:", e)
