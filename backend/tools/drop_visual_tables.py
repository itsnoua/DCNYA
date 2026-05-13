import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine

def drop_tables():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS visual_distortion_reports CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS visual_violations CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS violation_types CASCADE;"))
        
        # update alembic version
        conn.execute(text("UPDATE alembic_version SET version_num = 'e770c2cd71d5';"))
        conn.commit()
        print("Tables dropped and alembic version updated.")

if __name__ == "__main__":
    drop_tables()
