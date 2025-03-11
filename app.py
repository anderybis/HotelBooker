import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize extensions
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Create the Flask application
app = Flask(__name__)

# Load configuration
# Use development configuration for Replit environment
from dev_config import DevelopmentConfig
app.config.from_object(DevelopmentConfig)
logger.info("Using development configuration")

# Initialize extensions with the app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail.init_app(app)
csrf.init_app(app)

# Import models and initialize them
with app.app_context():
    from models import User, Room, Booking
    
    # Create tables if they don't exist
    db.create_all()
    logger.info("Database tables created or already exist")

# Import and register blueprints
from routes.auth import bp as auth_bp
from routes.admin import bp as admin_bp
from routes.booking import bp as booking_bp
from routes.main import bp as main_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(main_bp)
logger.info("Blueprints registered")

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"Server error: {e}")
    return render_template('errors/500.html'), 500

from flask import render_template

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
