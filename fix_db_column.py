from sqlalchemy import text, create_engine
import os

# Try to get database URL from environment or config
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    # Fallback to local sqlite
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_url = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')

# Clean up postgres URL for SQLAlchemy if needed
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

def fix():
    with engine.connect() as conn:
        print(f"Connecting to {db_url}...")
        
        # 1. Add category to vendors if missing
        try:
            conn.execute(text("SELECT category FROM vendors LIMIT 1"))
            print("vendors.category exists.")
        except Exception:
            print("Adding vendors.category...")
            try:
                conn.execute(text("ALTER TABLE vendors ADD COLUMN category VARCHAR(255) DEFAULT 'Washroom'"))
                conn.commit()
                print("Added category column.")
            except Exception as e:
                print(f"Error adding category: {e}")

        # 2. Add image_data to vendor_images if missing
        try:
            conn.execute(text("SELECT image_data FROM vendor_images LIMIT 1"))
            print("vendor_images.image_data exists.")
        except Exception:
            print("Adding vendor_images.image_data...")
            try:
                conn.execute(text("ALTER TABLE vendor_images ADD COLUMN image_data TEXT"))
                # Also try to make image_url nullable
                if 'postgresql' in db_url:
                   try:
                       conn.execute(text("ALTER TABLE vendor_images ALTER COLUMN image_url DROP NOT NULL"))
                   except: pass
                conn.commit()
                print("Added image_data column.")
            except Exception as e:
                print(f"Error adding image_data: {e}")
        
        print("Database schema check complete.")

if __name__ == "__main__":
    fix()
