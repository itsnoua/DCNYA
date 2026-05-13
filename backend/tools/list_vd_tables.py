import psycopg2
import os

try:
    conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
    cur = conn.cursor()
    
    # Check tables in visual_distortion schema
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'visual_distortion'")
    tables = cur.fetchall()
    print("Tables in visual_distortion schema:", tables)
    
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals(): conn.close()
