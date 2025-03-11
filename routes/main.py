from flask import Blueprint, render_template, redirect, url_for
from models import Room
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    """Render the home page."""
    try:
        # Get a sample of rooms to display on the home page
        rooms = Room.query.limit(3).all()
        return render_template('home.html', rooms=rooms)
    except Exception as e:
        logger.error(f"Error rendering home page: {e}")
        return render_template('errors/500.html'), 500
