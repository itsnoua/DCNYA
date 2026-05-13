import sys
import os

# Add the backend path to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.modules.visual_distortion.service import VisualDistortionService

def main():
    db = SessionLocal()
    try:
        kpis = VisualDistortionService.get_kpis(db, "all")
        print("KPIs:", kpis)
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
