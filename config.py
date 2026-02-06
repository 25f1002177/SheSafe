import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    @staticmethod
    def fix_database_url(url):
        if not url or not isinstance(url, str):
            return url
        
        url = url.strip()
        
        # 1. Correct the scheme for SQLAlchemy 1.4/2.0
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        # 2. Add driver explicitly
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
        # 3. Robustly encode auth part (handles @ and : in passwords)
        try:
            scheme_end = url.find("://")
            if scheme_end == -1: return url
            scheme = url[:scheme_end+3]
            rest = url[scheme_end+3:]
            
            auth_end = rest.rfind("@")
            if auth_end == -1: return url
            auth = rest[:auth_end]
            host_db_params = rest[auth_end+1:]
            
            import urllib.parse
            colon_pos = auth.find(":")
            if colon_pos == -1:
                user = urllib.parse.quote_plus(urllib.parse.unquote(auth))
                auth_part = user
            else:
                user = urllib.parse.quote_plus(urllib.parse.unquote(auth[:colon_pos]))
                password = urllib.parse.quote_plus(urllib.parse.unquote(auth[colon_pos+1:]))
                auth_part = f"{user}:{password}"
            
            return f"{scheme}{auth_part}@{host_db_params}"
        except Exception:
            return url

    DATABASE_URL = fix_database_url.__func__(os.environ.get('DATABASE_URL'))
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
        
        # Optimize for Supabase and Serverless (Vercel)
        from sqlalchemy.pool import NullPool
        SQLALCHEMY_ENGINE_OPTIONS = {
            'poolclass': NullPool,
            'pool_pre_ping': True,
            'connect_args': {
                'sslmode': 'require',
                'connect_timeout': 30
            }
        }
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
