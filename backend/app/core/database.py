from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# إعداد محرك قاعدة البيانات مع تحسين الأداء لـ PostGIS
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=30,
    max_overflow=50,
    pool_timeout=30,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
