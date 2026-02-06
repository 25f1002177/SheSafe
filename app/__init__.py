from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()


def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Create instance folder if it doesn't exist (skip on Vercel)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Create upload folder if it doesn't exist
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except OSError:
        pass
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # User loader callback
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template('error_403.html'), 403
    
    # Create database tables (handled safely for serverless)
    if os.environ.get('FLASK_ENV') != 'production' or os.environ.get('INIT_DB') == 'true':
        with app.app_context():
            try:
                from app import models
                db.create_all()
            except Exception as e:
                print(f"Database initialization skipped or failed: {e}")
    
    return app
