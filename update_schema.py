from app import create_app, db
from sqlalchemy import text

app = create_app()

def update_schema():
    with app.app_context():
        try:
            # Check if column exists
            db.session.execute(text("SELECT thumbnail_url FROM vendors LIMIT 1"))
            print("Column 'thumbnail_url' already exists.")
        except Exception:
            print("Adding column 'thumbnail_url' to vendors table...")
            try:
                db.session.execute(text("ALTER TABLE vendors ADD COLUMN thumbnail_url VARCHAR(255)"))
                db.session.commit()
                print("Column added successfully.")
            except Exception as e:
                print(f"Error adding column: {e}")
                db.session.rollback()

if __name__ == "__main__":
    update_schema()
