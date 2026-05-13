import sys
import os
import csv
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import insert
from app.core.database import SessionLocal
from app.modules.visual_distortion.models import VisualDistortionReport

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%m/%d/%Y').date()
    except ValueError:
        return None

def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.strptime(dt_str, '%m/%d/%y %I:%M:%S %p')
    except ValueError:
        # Fallback for unexpected formats
        try:
            return datetime.strptime(dt_str, '%m/%d/%Y %I:%M:%S %p')
        except ValueError:
            return None

def import_data(csv_filepath):
    db = SessionLocal()
    
    # Check if data already exists to prevent duplicate imports
    existing_count = db.query(VisualDistortionReport).count()
    if existing_count > 0:
        print(f"Data already exists in visual_distortion_reports. Found {existing_count} records. Skipping import.")
        db.close()
        return

    print("Starting import...")
    chunk_size = 5000
    records = []
    
    with open(csv_filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            try:
                lon = float(row.get('احداثي X', 0))
                lat = float(row.get('احداثي Y', 0))
            except ValueError:
                lon, lat = 0.0, 0.0
                
            geom_wkt = f"SRID=4326;POINT({lon} {lat})" if lon and lat else None
            
            record = {
                "municipality": row.get('البلدية'),
                "report_number": row.get('رقم البلاغ المجمع'),
                "visit_number": row.get('رقم الزيارة لدى ممتثل'),
                "report_status": row.get('حالة البلاغ'),
                "visit_status": row.get('حالة الزيارة'),
                "observation_date": parse_date(row.get('تاريخ الرصد')),
                "assignment_date": parse_date(row.get('تاريخ الاسناد')),
                "closing_date": parse_date(row.get('تاريخ الاغلاق')),
                "longitude": lon,
                "latitude": lat,
                "geom": geom_wkt,
                "classification_name": row.get('اسم التصنيف'),
                "closing_status": row.get('الحالة حسب الاغلاق'),
                "last_observation_date": parse_datetime(row.get('تاريخ آخر رصد')),
                "first_observation_date": parse_datetime(row.get('تاريخ أول رصد'))
            }
            records.append(record)
            count += 1
            
            if len(records) >= chunk_size:
                db.execute(insert(VisualDistortionReport), records)
                db.commit()
                print(f"Inserted {count} records...")
                records = []
                
        # Insert remaining
        if records:
            db.execute(insert(VisualDistortionReport), records)
            db.commit()
            print(f"Inserted remaining records. Total: {count}")
            
    db.close()
    print("Import completed successfully!")

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "مختصر بوابة البلاغات .csv")
    import_data(csv_file)
