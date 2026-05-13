import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine

def truncate_tables():
    print("Connecting to database...")
    try:
        with engine.connect() as conn:
            print("Truncating visual distortion tables...")
            # Use TRUNCATE to quickly delete all rows while keeping structure
            # We target the tables in the visual_distortion schema
            conn.execute(text("TRUNCATE TABLE visual_distortion.visual_distortion_reports RESTART IDENTITY CASCADE;"))
            
            # Check if visual_violations exists
            try:
                conn.execute(text("TRUNCATE TABLE visual_distortion.visual_violations RESTART IDENTITY CASCADE;"))
                print("Truncated visual_violations table.")
            except Exception:
                # Table might not exist in this schema
                pass

            conn.commit()
            print("Successfully deleted all data from Visual Distortion tables.")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    confirm = input("This will delete ALL data in Visual Distortion tables. Are you sure? (y/n): ")
    if confirm.lower() == 'y':
        truncate_tables()
    else:
        print("Operation cancelled.")
