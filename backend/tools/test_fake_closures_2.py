from sqlalchemy import create_engine, text
import time

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    start = time.time()
    
    # Check with exact coordinates
    fake_query = text('''
        SELECT SUM(cnt - 1) FROM (
            SELECT 
                classification_name, 
                longitude, 
                latitude, 
                COUNT(*) as cnt
            FROM visual_distortion.visual_distortion_reports
            GROUP BY classification_name, longitude, latitude
            HAVING COUNT(*) > 1
        ) as sub
    ''')
    fake_closures = conn.execute(fake_query).scalar() or 0
    end = time.time()
    
    print(f"Fake closures (exact coords): {fake_closures}")
    print(f"Time taken: {end - start:.2f} seconds")
