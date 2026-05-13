from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    query = text('SELECT COUNT(*) FROM visual_distortion.visual_distortion_reports WHERE closing_date IS NULL')
    result = conn.execute(query).scalar()
    print(f"Number of blank (null) values in closing_date: {result}")

    query_total = text('SELECT COUNT(*) FROM visual_distortion.visual_distortion_reports')
    total = conn.execute(query_total).scalar()
    print(f"Total number of reports: {total}")
