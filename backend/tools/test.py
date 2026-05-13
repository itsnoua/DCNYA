import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.modules.compliance.service import GeoService

db = SessionLocal()
try:
    kpis = GeoService.get_kpis(db, 1)
    print(kpis)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
