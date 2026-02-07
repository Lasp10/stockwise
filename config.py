"""
Configuration file for StockWise MVP
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# NEVER commit .env or keys.env to git!
load_dotenv()

class Config:
    """Application configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # MongoDB configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/'
    MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME') or 'stockwise'
    
    # Email configuration (SendGrid)
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY') or ''
    ALERT_EMAIL_FROM = os.environ.get('ALERT_EMAIL_FROM') or 'alerts@stockwise.com'
    
    # SMTP configuration (alternative to SendGrid)
    SMTP_SERVER = os.environ.get('SMTP_SERVER') or 'smtp.gmail.com'
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME') or ''
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') or ''
    
    # Alert threshold (days)
    LOW_STOCK_THRESHOLD = 2  # Alert when ingredient projected to run out in < 2 days
    
    # Test mode - set to True to send alerts for all ingredients (for testing)
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    
    # Upload settings
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'csv'}
