from sqlalchemy import create_engine, text
import time

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    start = time.time()
    # Let's count total reports first
    total_query = text('SELECT COUNT(*) FROM visual_distortion.visual_distortion_reports')
    total = conn.execute(total_query).scalar()
    
    # Let's count fake closures
    # A fake closure is any report in a group of (classification, lat, lng) beyond the first one.
    # So if a group has 3 reports, 2 of them are "fake closures".
    # Fake closures count = sum(count - 1) for groups having count > 1
    fake_query = text('''
        SELECT SUM(cnt - 1) FROM (
            SELECT 
                classification_name, 
                ROUND(longitude::numeric, 4) as lon, 
                ROUND(latitude::numeric, 4) as lat, 
                COUNT(*) as cnt
            FROM visual_distortion.visual_distortion_reports
            GROUP BY classification_name, ROUND(longitude::numeric, 4), ROUND(latitude::numeric, 4)
            HAVING COUNT(*) > 1
        ) as sub
    ''')
    fake_closures = conn.execute(fake_query).scalar() or 0
    end = time.time()
    
    print(f"Total reports: {total}")
    print(f"Fake closures: {fake_closures}")
    print(f"Percentage: {(fake_closures / total) * 100 if total else 0:.2f}%")
    print(f"Time taken: {end - start:.2f} seconds")
