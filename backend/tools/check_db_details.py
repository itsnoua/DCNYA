
import os
from sqlalchemy import create_url, create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def check_compliance_tables():
    with engine.connect() as conn:
        # Check schemas
        schemas = conn.execute(text("SELECT schema_name FROM information_schema.schemata")).fetchall()
        print(f"Schemas: {[s[0] for s in schemas]}")
        
        # Check tables in compliance schema
        tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'compliance'")).fetchall()
        print(f"Tables in 'compliance': {[t[0] for t in tables]}")
        
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM compliance.{table[0]}")).scalar()
            print(f"Table 'compliance.{table[0]}' has {count} rows.")

if __name__ == "__main__":
    check_compliance_tables()
