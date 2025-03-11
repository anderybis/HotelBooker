from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import db
from forms import LoginForm, RegisterForm
from models import User
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            logger.info(f"User {user.username} logged in successfully")
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))
        flash('Invalid email or password.', 'danger')
        logger.warning(f"Failed login attempt for email: {form.email.data}")
    
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data if form.phone_number.data else None,
            sms_notifications=form.sms_notifications.data
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"New user registered: {user.username} (Phone: {user.phone_number}, SMS: {user.sms_notifications})")
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during user registration: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    username = current_user.username
    logout_user()
    logger.info(f"User {username} logged out")
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

@bp.route('/profile')
@login_required
def profile():
    """Display user profile."""
    try:
        # Get user's bookings
        bookings = current_user.bookings.order_by(db.desc('created_at')).all()
        return render_template('auth/profile.html', bookings=bookings)
    except Exception as e:
        logger.error(f"Error displaying user profile: {e}")
        flash('An error occurred while loading your profile.', 'danger')
        return redirect(url_for('main.home'))
