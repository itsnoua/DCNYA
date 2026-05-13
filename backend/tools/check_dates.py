from sqlalchemy import create_engine, text
import json
import os
from dotenv import load_dotenv

# Try to load DB URL from .env
db_url = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"

engine = create_engine(db_url)

def get_phase_dates(phase_id):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT details FROM compliance.dynamic_points WHERE phase_id = {phase_id}"))
            dates = []
            for row in result:
                details = row[0]
                if details and 'startDate' in details:
                    try:
                        # Assuming format like '01/15/2024 ...'
                        date_str = details['startDate'].split(' ')[0]
                        dates.append(date_str)
                    except:
                        continue
            if not dates:
                return None
            
            # Sort dates correctly (assuming MM/DD/YYYY)
            from datetime import datetime
            parsed_dates = []
            for d in dates:
                try:
                    parsed_dates.append(datetime.strptime(d, '%m/%d/%Y'))
                except:
                    continue
            
            if not parsed_dates: return None
            
            return min(parsed_dates).strftime('%Y/%m/%d'), max(parsed_dates).strftime('%Y/%m/%d')
    except Exception as e:
        return str(e)

print("Phase 1:", get_phase_dates(1))
print("Phase 2:", get_phase_dates(2))
