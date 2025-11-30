import os

class LocalDevelopmentConfig:
    DEBUG = True
    # Use absolute path to ensure database is found regardless of working directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(PROJECT_ROOT, "instance", "parkease2.sqlite3")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'dev-secret-key-change-in-production'
    SECURITY_PASSWORD_SALT = 'dev-salt-change-in-production'
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_KEY = 'auth-token'
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'auth-token'
    
    # Redis Cache Configuration
    REDIS_CACHE_URL = 'redis://localhost:6379/1'  # Separate database for caching
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default
    CACHE_KEY_PREFIX = 'parkease_cache:'