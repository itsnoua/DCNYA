from sqlalchemy import create_engine, text, func, distinct, cast, String
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.getcwd())
from app.modules.compliance.models import DynamicPoint

db_url = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def test():
    db = SessionLocal()
    try:
        print("Testing simple key access...")
        res = db.query(DynamicPoint.details['startDate']).limit(1).scalar()
        print("Result:", res, type(res))
        
        print("Testing cast to string...")
        res = db.query(cast(DynamicPoint.details['startDate'], String)).limit(1).scalar()
        print("Result:", res, type(res))
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

test()
