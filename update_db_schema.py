import os
from app import create_app, db
from sqlalchemy import text

app = create_app()

def update_schema():
    with app.app_context():
        print("Checking database schema...")
        
        # Check if column exists
        with db.engine.connect() as conn:
            # Check for PostgreSQL/SQLite compatibility
            try:
                # Attempt to select the column to see if it exists
                conn.execute(text("SELECT category FROM vendors LIMIT 1"))
                print("Column 'category' already exists in 'vendors' table.")
            except Exception:
                print("Column 'category' missing. Adding it now...")
                try:
                    conn.execute(text("ALTER TABLE vendors ADD COLUMN category VARCHAR(255) DEFAULT 'Washroom' NOT NULL"))
                    conn.commit()
                    print("Successfully added 'category' column to 'vendors' table.")
                except Exception as e:
                    print(f"Error adding column category: {e}")

        # Check for image_data in vendor_images
        with db.engine.connect() as conn:
            try:
                conn.execute(text("SELECT image_data FROM vendor_images LIMIT 1"))
                print("Column 'image_data' already exists in 'vendor_images' table.")
            except Exception:
                print("Column 'image_data' missing. Adding it now...")
                try:
                    conn.execute(text("ALTER TABLE vendor_images ADD COLUMN image_data TEXT"))
                    conn.execute(text("ALTER TABLE vendor_images ALTER COLUMN image_url DROP NOT NULL"))
                    conn.commit()
                    print("Successfully added 'image_data' column and updated 'image_url' to nullable.")
                except Exception as e:
                    print(f"Error updating vendor_images: {e}")

if __name__ == "__main__":
    update_schema()
