import os
from app import create_app, db
from app.models import User

app = create_app()

def create_admin():
    with app.app_context():
        print("Checking for admin user...")
        
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@admin.com').first()
        
        if admin:
            print("Admin user already exists!")
            print(f"Email: {admin.email}")
            print(f"Role: {admin.role}")
        else:
            print("Creating admin user...")
            admin = User(
                name='Admin',
                email='admin@admin.com',
                role='admin'
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("Admin user created successfully!")
            print("Email: admin@admin.com")
            print("Password: admin123")

if __name__ == "__main__":
    create_admin()
