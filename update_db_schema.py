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
                # Rollback in case the previous transaction failed
                # conn.rollback() # Not needed for connect() context manager usually, but auto-commit is tricky
                
                # Add the column
                try:
                    # PostgreSQL syntax (also works for SQLite mostly, but let's assume Postgres for Vercel)
                    conn.execute(text("ALTER TABLE vendors ADD COLUMN category VARCHAR(50) DEFAULT 'Washroom' NOT NULL"))
                    conn.commit()
                    print("Successfully added 'category' column to 'vendors' table.")
                except Exception as e:
                    print(f"Error adding column: {e}")

if __name__ == "__main__":
    update_schema()
