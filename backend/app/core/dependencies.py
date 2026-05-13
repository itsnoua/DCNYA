from typing import Generator
from app.core.database import SessionLocal

def get_db() -> Generator:
    """
    Dependency لقاعدة البيانات تضمن فتح اتصال واحد لكل Request
    وإغلاقه تلقائياً عند الانتهاء.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
