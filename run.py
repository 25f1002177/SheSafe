import os
from app import create_app

# Get configuration from environment or use default
config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    with app.app_context():
        from app import db
        from app.models import User
        
        # Reset Database
        db.drop_all()
        db.create_all()
        
        # Create Default Admin
        admin = User(name='Admin', email='admin@admin.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Database reset and default admin created.")
        
    app.run(debug=True, host='0.0.0.0', port=5000)
