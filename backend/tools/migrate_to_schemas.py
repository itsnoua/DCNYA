import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def migrate_to_schemas():
    with engine.connect() as conn:
        print("Creating schemas...")
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS compliance;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS visual_distortion;"))
        conn.commit()
        
        print("Moving tables to compliance schema...")
        tables_to_compliance = ["phases", "buildings", "dynamic_points", "roads"]
        for table in tables_to_compliance:
            try:
                conn.execute(text(f"ALTER TABLE public.{table} SET SCHEMA compliance;"))
                print(f"Moved {table} to compliance schema.")
            except Exception as e:
                print(f"Skipping {table} or error: {e}")
                
        print("Moving tables to visual_distortion schema...")
        tables_to_visual_distortion = ["visual_distortion_reports"]
        for table in tables_to_visual_distortion:
            try:
                conn.execute(text(f"ALTER TABLE public.{table} SET SCHEMA visual_distortion;"))
                print(f"Moved {table} to visual_distortion schema.")
            except Exception as e:
                print(f"Skipping {table} or error: {e}")
                
        conn.commit()
        print("Migration to schemas completed successfully!")

if __name__ == "__main__":
    migrate_to_schemas()
