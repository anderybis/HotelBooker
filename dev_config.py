import os
from datetime import timedelta

class Config:
    """Base configuration with common settings."""
    # Secret key
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-key-not-for-production")
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///hotel.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 15
    }
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Mail settings
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = bool(os.environ.get("MAIL_USE_TLS", True))
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "development@example.com")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "development_password")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@luxuryhotel.com")
    
    # Application settings
    HOTEL_NAME = "Luxury Hotel"
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@luxuryhotel.com")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    # Print emails to console instead of sending them
    MAIL_SUPPRESS_SEND = False  # Enable email sending
    MAIL_DEBUG = True  # Log more information about mail
    TESTING = False  # Not in testing mode