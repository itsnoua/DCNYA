import psycopg2
try:
    conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print("Public tables:", cur.fetchall())
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals(): conn.close()
