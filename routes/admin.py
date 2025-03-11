from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from functools import wraps

from app import db
from models import Room, Booking, User
from forms import RoomForm

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)  # This preserves the original function's metadata
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    # Calculate statistics for the dashboard
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    stats = {
        'total_bookings': Booking.query.filter(Booking.created_at >= thirty_days_ago).count(),
        'total_revenue': db.session.query(func.sum(Booking.total_price))
            .filter(Booking.created_at >= thirty_days_ago)
            .scalar() or 0,
        'occupancy_rate': calculate_occupancy_rate(),
        'available_rooms': Room.query.count()
    }

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html', stats=stats, recent_bookings=recent_bookings)

@bp.route('/rooms', methods=['GET'])
@login_required
@admin_required
def rooms():
    rooms = Room.query.all()
    form = RoomForm()
    return render_template('admin/rooms.html', rooms=rooms, form=form)

@bp.route('/rooms/add', methods=['POST'])
@login_required
@admin_required
def add_room():
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            room_number=form.room_number.data,
            room_type=form.room_type.data,
            capacity=int(form.capacity.data),
            price_per_night=float(form.price_per_night.data),
            description=form.description.data,
            amenities=form.amenities.data,
            image_url=form.image_url.data
        )
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully.', 'success')
    return redirect(url_for('admin.rooms'))

@bp.route('/rooms/<int:room_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = RoomForm()
    if form.validate_on_submit():
        room.room_number = form.room_number.data
        room.room_type = form.room_type.data
        room.capacity = int(form.capacity.data)
        room.price_per_night = float(form.price_per_night.data)
        room.description = form.description.data
        room.amenities = form.amenities.data
        room.image_url = form.image_url.data
        db.session.commit()
        flash('Room updated successfully.', 'success')
    return redirect(url_for('admin.rooms'))

@bp.route('/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    if room.bookings:
        flash('Cannot delete room with existing bookings.', 'danger')
    else:
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted successfully.', 'success')
    return redirect(url_for('admin.rooms'))

def calculate_occupancy_rate():
    total_rooms = Room.query.count()
    if total_rooms == 0:
        return 0

    current_date = datetime.utcnow().date()
    occupied_rooms = Booking.query.filter(
        Booking.check_in_date <= current_date,
        Booking.check_out_date >= current_date
    ).count()

    return round((occupied_rooms / total_rooms) * 100, 2)