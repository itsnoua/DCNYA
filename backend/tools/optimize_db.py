from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://gis_user:gis_secure_password@localhost:5432/gis_db"

def optimize_db():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Creating indexes for visual distortion reports...")
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vd_municipality ON visual_distortion.visual_distortion_reports (municipality);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vd_group ON visual_distortion.visual_distortion_reports (management_group);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vd_classification ON visual_distortion.visual_distortion_reports (classification_name);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_vd_status ON visual_distortion.visual_distortion_reports (report_status);"))
        conn.execute(text("COMMIT;"))
        print("Indexes created successfully.")

if __name__ == "__main__":
    optimize_db()
