import os
from app import create_app, db
from app.models import User

app = create_app()

def reset_admin_password():
    with app.app_context():
        print("Resetting admin password...")
        
        # Find admin user
        admin = User.query.filter_by(email='admin@admin.com').first()
        
        if admin:
            # Reset password
            admin.set_password('admin123')
            db.session.commit()
            
            print("Admin password reset successfully!")
            print("Email: admin@admin.com")
            print("Password: admin123")
            print(f"Role: {admin.role}")
            
            # Verify password works
            if admin.check_password('admin123'):
                print("✓ Password verification successful!")
            else:
                print("✗ Password verification failed!")
        else:
            print("Admin user not found. Creating new admin...")
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
    reset_admin_password()
