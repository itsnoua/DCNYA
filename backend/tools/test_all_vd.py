import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.modules.visual_distortion.service import VisualDistortionService

def main():
    db = SessionLocal()
    try:
        print("Testing KPIs...")
        kpis = VisualDistortionService.get_kpis(db, "all")
        print("KPIs:", kpis)
        
        print("Testing Classifications...")
        classifications = VisualDistortionService.get_classifications(db, "all")
        print("Classifications:", classifications)
        
        print("Testing Points...")
        points = VisualDistortionService.get_points(db, "all")
        print("Points Count:", len(points))
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
