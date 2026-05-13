import psycopg2
conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'compliance' AND table_name = 'buildings'")
columns = cur.fetchall()
print(columns)
conn.close()
