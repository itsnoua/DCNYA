from sqlalchemy import create_engine, text
import json

db_url = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(db_url)

def inspect(phase_id):
    print(f"--- Inspecting Phase {phase_id} ---")
    try:
        with engine.connect() as conn:
            # Check count
            count = conn.execute(text(f"SELECT count(*) FROM compliance.dynamic_points WHERE phase_id = {phase_id}")).scalar()
            print(f"Total points: {count}")
            
            # Check first 5 details
            result = conn.execute(text(f"SELECT details FROM compliance.dynamic_points WHERE phase_id = {phase_id} LIMIT 5"))
            for i, row in enumerate(result):
                print(f"Record {i+1}: {row[0]}")
    except Exception as e:
        print(f"Error: {e}")

inspect(1)
inspect(2)
inspect(3)
