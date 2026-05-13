import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/aseer_compliance')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'visual_distortion'")
    tables = cur.fetchall()
    print("Tables:", tables)
    
    # Check if we have a municipalities table
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'municipalities'")
    muns = cur.fetchall()
    print("Municipalities tables:", muns)
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals(): conn.close()
