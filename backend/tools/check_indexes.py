import psycopg2
conn = psycopg2.connect('postgresql://gis_user:gis_secure_password@localhost:5432/gis_db')
cur = conn.cursor()
cur.execute("SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'compliance' AND tablename = 'buildings'")
indexes = cur.fetchall()
for idx in indexes:
    print(idx)
conn.close()
