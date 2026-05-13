from sqlalchemy import create_engine, text
from app.core.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

def check_counts():
    with engine.connect() as conn:
        print("Checking public schema:")
        for table in ['phases', 'buildings', 'dynamic_points']:
            try:
                res = conn.execute(text(f"SELECT count(*) FROM public.{table}")).scalar()
                print(f"  public.{table}: {res}")
            except Exception as e:
                print(f"  public.{table} does not exist or error: {e}")

        print("\nChecking compliance schema:")
        for table in ['phases', 'buildings', 'dynamic_points']:
            try:
                res = conn.execute(text(f"SELECT count(*) FROM compliance.{table}")).scalar()
                print(f"  compliance.{table}: {res}")
            except Exception as e:
                print(f"  compliance.{table} does not exist or error: {e}")

        print("\nChecking visual_distortion schema:")
        for table in ['visual_distortion_reports']:
            try:
                res = conn.execute(text(f"SELECT count(*) FROM visual_distortion.{table}")).scalar()
                print(f"  visual_distortion.{table}: {res}")
            except Exception as e:
                print(f"  visual_distortion.{table} does not exist or error: {e}")

if __name__ == "__main__":
    check_counts()
