import psycopg2
try:
    conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
    cur = conn.cursor()
    
    # 1. Check schemas
    cur.execute("SELECT schema_name FROM information_schema.schemata")
    print("Schemas:", cur.fetchall())
    
    # 2. Check tables in compliance schema (where municipality boundaries usually live)
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'compliance'")
    print("Compliance tables:", cur.fetchall())
    
    # 3. Check if there's a municipalities table with geometry
    cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name = 'municipalities'")
    print("Municipalities columns:", cur.fetchall())
    
except Exception as e:
    print("Error:", e)
finally:
    if 'conn' in locals(): conn.close()
