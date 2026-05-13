import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    query = text('SELECT DISTINCT report_status FROM visual_distortion.visual_distortion_reports')
    statuses = conn.execute(query).fetchall()
    
    query_c = text('SELECT DISTINCT closing_status FROM visual_distortion.visual_distortion_reports')
    closing_statuses = conn.execute(query_c).fetchall()
    
    with open('statuses.json', 'w', encoding='utf-8') as f:
        json.dump({
            "report_status": [s[0] for s in statuses if s[0]],
            "closing_status": [c[0] for c in closing_statuses if c[0]]
        }, f, ensure_ascii=False, indent=2)
