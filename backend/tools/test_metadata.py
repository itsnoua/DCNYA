from sqlalchemy import create_engine, text, func, distinct
import json
from datetime import datetime
from sqlalchemy.orm import Session, sessionmaker
import sys
import os

# Add parent dir to path to import models
sys.path.append(os.getcwd())

from app.modules.compliance.models import DynamicPoint

db_url = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)

def test_metadata(phase_id):
    db = SessionLocal()
    try:
        from app.modules.compliance.service import GeoService
        data = GeoService.get_phase_metadata(db, phase_id)
        print(f"Phase {phase_id} Metadata:", data)
    finally:
        db.close()

test_metadata(1)
test_metadata(2)
test_metadata(3)
