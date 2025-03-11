from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Room, Booking, User
from forms import RoomForm
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin access decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            logger.warning(f"Non-admin user {current_user.username} attempted to access admin area")
            flash('You do not have permission to access this area.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard showing booking and revenue statistics."""
    try:
        # Calculate statistics for the past 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        today = datetime.utcnow().date()
        
        # Total bookings in last 30 days
        total_bookings = Booking.query.filter(
            Booking.created_at >= thirty_days_ago
        ).count()
        
        # Total revenue in last 30 days
        total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Current occupancy rate
        total_rooms = Room.query.count()
        occupied_rooms = Booking.query.filter(
            Booking.check_in_date <= today,
            Booking.check_out_date > today,
            Booking.booking_status != 'cancelled'
        ).count()
        
        occupancy_rate = round((occupied_rooms / total_rooms * 100), 2) if total_rooms > 0 else 0
        
        # Available rooms
        available_rooms = total_rooms - occupied_rooms
        
        # Recent bookings
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
        
        stats = {
            'total_bookings': total_bookings,
            'total_revenue': round(total_revenue, 2),
            'occupancy_rate': occupancy_rate,
            'available_rooms': available_rooms
        }
        
        return render_template('admin/dashboard.html', stats=stats, recent_bookings=recent_bookings)
    except Exception as e:
        logger.error(f"Error in admin dashboard: {e}")
        flash('An error occurred while loading the dashboard.', 'danger')
        return redirect(url_for('main.home'))

@bp.route('/rooms')
@admin_required
def rooms():
    """Room management page."""
    try:
        rooms = Room.query.all()
        return render_template('admin/rooms.html', rooms=rooms)
    except Exception as e:
        logger.error(f"Error loading rooms management page: {e}")
        flash('An error occurred while loading the rooms.', 'danger')
        return redirect(url_for('admin.dashboard'))

@bp.route('/add_room', methods=['POST'])
@admin_required
def add_room():
    """Add a new room."""
    form = RoomForm()
    if form.validate_on_submit():
        try:
            room = Room(
                room_number=form.room_number.data,
                room_type=form.room_type.data,
                capacity=form.capacity.data,
                price_per_night=form.price_per_night.data,
                description=form.description.data,
                amenities=form.amenities.data,
                image_url=form.image_url.data
            )
            db.session.add(room)
            db.session.commit()
            logger.info(f"New room added: {room.room_number}")
            flash(f'Room {room.room_number} added successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding room: {e}")
            flash('An error occurred while adding the room.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin.rooms'))

@bp.route('/edit_room/<int:room_id>', methods=['POST'])
@admin_required
def edit_room(room_id):
    """Edit an existing room."""
    room = Room.query.get_or_404(room_id)
    form = RoomForm()
    if form.validate_on_submit():
        try:
            room.room_number = form.room_number.data
            room.room_type = form.room_type.data
            room.capacity = form.capacity.data
            room.price_per_night = form.price_per_night.data
            room.description = form.description.data
            room.amenities = form.amenities.data
            room.image_url = form.image_url.data
            
            db.session.commit()
            logger.info(f"Room updated: {room.room_number}")
            flash(f'Room {room.room_number} updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating room: {e}")
            flash('An error occurred while updating the room.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin.rooms'))

@bp.route('/delete_room/<int:room_id>', methods=['POST'])
@admin_required
def delete_room(room_id):
    """Delete a room."""
    room = Room.query.get_or_404(room_id)
    try:
        # Check if room has bookings
        if room.bookings.count() > 0:
            flash('Cannot delete room with existing bookings.', 'danger')
            return redirect(url_for('admin.rooms'))
        
        room_number = room.room_number
        db.session.delete(room)
        db.session.commit()
        logger.info(f"Room deleted: {room_number}")
        flash(f'Room {room_number} deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting room: {e}")
        flash('An error occurred while deleting the room.', 'danger')
    
    return redirect(url_for('admin.rooms'))

@bp.route('/bookings')
@admin_required
def bookings():
    """View all bookings."""
    try:
        bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        return render_template('admin/bookings.html', bookings=bookings)
    except Exception as e:
        logger.error(f"Error loading bookings page: {e}")
        flash('An error occurred while loading the bookings.', 'danger')
        return redirect(url_for('admin.dashboard'))
