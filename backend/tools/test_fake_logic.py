import time
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    start = time.time()
    
    query_total = text("SELECT COUNT(*) FROM visual_distortion.visual_distortion_reports")
    total = conn.execute(query_total).scalar() or 0

    query_fake = text('''
        SELECT SUM(cnt - 1) FROM (
            SELECT classification_name, longitude, latitude, 
                   COUNT(*) as cnt,
                   SUM(CASE WHEN report_status = 'مغلق' THEN 1 ELSE 0 END) as manual_closed_cnt
            FROM visual_distortion.visual_distortion_reports
            GROUP BY classification_name, longitude, latitude
            HAVING COUNT(*) > 1 AND SUM(CASE WHEN report_status = 'مغلق' THEN 1 ELSE 0 END) > 0
        ) as sub
    ''')
    fake_closures = conn.execute(query_fake).scalar() or 0
    end = time.time()
    
    print(f"Total reports: {total}")
    print(f"Fake closures (Only manual closed): {fake_closures}")
    print(f"Percentage: {(fake_closures / total) * 100 if total else 0:.2f}%")
    print(f"Time taken: {end - start:.2f} seconds")
