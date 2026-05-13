import sys
import os
import csv
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from sqlalchemy import insert, text
from app.core.database import SessionLocal
from app.modules.compliance.models import DynamicPoint

def parse_datetime(dt_str):
    if not dt_str:
        return None
    # Input format: 2/5/2026 0:00 (M/D/Y H:M)
    formats = ['%m/%d/%Y %H:%M', '%d/%m/%Y %H:%M', '%Y/%m/%d %H:%M']
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    return None

def import_compliance_data(csv_filepath):
    db = SessionLocal()
    
    print(f"Starting import from {csv_filepath}...")
    chunk_size = 500
    records = []
    
    try:
        with open(csv_filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                try:
                    lon = float(row.get('X', 0))
                    lat = float(row.get('Y', 0))
                except ValueError:
                    lon, lat = 0.0, 0.0
                
                if not lon or not lat:
                    continue
                    
                geom_wkt = f"SRID=4326;POINT({lon} {lat})"
                
                # Normalize municipality name (optional but good)
                mun = row.get('البلدية', '').strip()
                
                record = {
                    "name": f"شهادة - {mun}",
                    "phase_id": 1, # Phase 1 as requested
                    "municipality": mun,
                    "street": "غير محدد",
                    "district": "غير محدد",
                    "status": "active",
                    "is_relevant": True,
                    "geom": geom_wkt,
                    "details": {
                        "startDate": row.get('تاريخ إصدار الشهادة ميلادي'),
                        "endDate": row.get('تاريخ إنتهاء الشهادة ميلادي'),
                        "source": "نظام الشهادات 2026"
                    },
                    "updated_at": datetime.utcnow()
                }
                records.append(record)
                count += 1
                
                if len(records) >= chunk_size:
                    db.execute(insert(DynamicPoint), records)
                    db.commit()
                    print(f"Inserted {count} records...")
                    records = []
                    
            # Insert remaining
            if records:
                db.execute(insert(DynamicPoint), records)
                db.commit()
                print(f"Inserted remaining records. Total: {count}")
                
        print("Import completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during import: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # The CSV is in the root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    csv_file = os.path.join(root_dir, "شهادات الامتثال 2026.csv")
    
    if os.path.exists(csv_file):
        import_compliance_data(csv_file)
    else:
        try:
            print(f"File not found: {csv_file}")
        except UnicodeEncodeError:
            print("File not found (path contains special characters)")
