from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db, app # Added app import for logging
from forms import BookingSearchForm
from models import Room, Booking
from utils import check_room_availability, calculate_total_price, process_payment, send_booking_confirmation, award_loyalty_points

bp = Blueprint('booking', __name__, url_prefix='/booking')

@bp.route('/search', methods=['GET', 'POST'])
def search():
    form = BookingSearchForm()
    rooms = []

    if form.validate_on_submit():
        room_type = form.room_type.data
        capacity = int(form.guests.data)
        check_in = form.check_in.data
        check_out = form.check_out.data

        # Get all rooms matching criteria
        rooms = Room.query.filter(
            Room.room_type == room_type,
            Room.capacity >= capacity
        ).all()

        # Filter out unavailable rooms
        available_rooms = []
        for room in rooms:
            is_available, _ = check_room_availability(room.id, check_in, check_out)
            if is_available:
                available_rooms.append(room)
        rooms = available_rooms

        if not rooms:
            flash('No available rooms found for the selected dates.', 'info')

    return render_template('booking/search.html', form=form, rooms=rooms)

@bp.route('/room/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('booking/room_detail.html', room=room)

@bp.route('/check_availability/<int:room_id>', methods=['POST'])
def check_availability(room_id):
    """AJAX endpoint to check room availability"""
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')

    if not all([check_in, check_out]):
        return jsonify({'available': False, 'message': 'Please select both check-in and check-out dates'})

    is_available, message = check_room_availability(room_id, check_in, check_out)
    total_price = calculate_total_price(room_id, check_in, check_out) if is_available else 0

    return jsonify({
        'available': is_available,
        'message': message,
        'total_price': total_price
    })

@bp.route('/book/<int:room_id>', methods=['POST'])
@login_required
def book(room_id):
    """Create a new booking for the specified room"""
    room = Room.query.get_or_404(room_id)

    try:
        # Validate input data
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        guests = request.form.get('guests', type=int)

        if not all([check_in, check_out, guests]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))

        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))

        # Verify room availability
        is_available, message = check_room_availability(room_id, check_in_date, check_out_date)
        if not is_available:
            flash(message, 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))

        # Calculate total price
        total_price = calculate_total_price(room_id, check_in_date, check_out_date)

        # Create booking
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            booking_status='pending',
            payment_status='pending'
        )

        db.session.add(booking)
        db.session.commit()

        # Process payment
        if process_payment(booking):
            booking.payment_status = 'paid'
            booking.booking_status = 'confirmed'
            db.session.commit()

            # Try to send confirmation email but don't fail if it doesn't work
            email_sent = send_booking_confirmation(booking)
            if not email_sent:
                app.logger.warning(f"Confirmation email could not be sent for booking {booking.id}")

            # Try to award loyalty points
            points_awarded = award_loyalty_points(booking)
            if not points_awarded:
                app.logger.warning(f"Failed to award loyalty points for booking {booking.id}")

            flash('Booking confirmed! Thank you for your reservation.', 'success')
            return redirect(url_for('booking.confirmation', booking_id=booking.id))
        else:
            booking.booking_status = 'cancelled'
            db.session.commit()
            flash('Payment processing failed. Please try again.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error processing booking: {str(e)}")
        flash('An error occurred while processing your booking. Please try again.', 'danger')
        return redirect(url_for('booking.room_detail', room_id=room_id))

@bp.route('/confirmation/<int:booking_id>')
@login_required
def confirmation(booking_id):
    """Display booking confirmation page"""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    return render_template('booking/confirmation.html', booking=booking)