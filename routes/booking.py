from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, mail
from models import Room, Booking
from forms import SearchForm, BookingForm
from datetime import datetime
from flask_mail import Message
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('booking', __name__, url_prefix='/booking')

@bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search for available rooms."""
    form = SearchForm()
    rooms = []
    
    if form.validate_on_submit():
        try:
            # Get the search parameters
            check_in = form.check_in.data
            check_out = form.check_out.data
            room_type = form.room_type.data
            guests = form.guests.data
            
            # Query for available rooms
            query = Room.query
            
            # Filter by room type if specified
            if room_type:
                query = query.filter(Room.room_type == room_type)
            
            # Filter by capacity
            query = query.filter(Room.capacity >= guests)
            
            # Get all rooms that match the criteria
            potential_rooms = query.all()
            
            # Filter out rooms that are already booked for the given dates
            rooms = [room for room in potential_rooms if 
                     Booking.check_availability(room.id, check_in, check_out)]
            
            if not rooms:
                flash('No rooms available for the selected dates and criteria.', 'info')
            
            logger.info(f"Room search: {len(rooms)} rooms found for {check_in} to {check_out}")
        except Exception as e:
            logger.error(f"Error during room search: {e}")
            flash('An error occurred during the search. Please try again.', 'danger')
    
    return render_template('booking/search.html', form=form, rooms=rooms)

@bp.route('/room/<int:room_id>')
def room_detail(room_id):
    """Display room details."""
    try:
        room = Room.query.get_or_404(room_id)
        
        # Create a booking form with the capacity constraint
        form = BookingForm()
        form.guests.choices = [(i, f"{i} Guest{'s' if i > 1 else ''}") for i in range(1, room.capacity + 1)]
        
        return render_template('booking/room_detail.html', room=room, form=form)
    except Exception as e:
        logger.error(f"Error displaying room details: {e}")
        flash('An error occurred while loading the room details.', 'danger')
        return redirect(url_for('booking.search'))

@bp.route('/check_availability/<int:room_id>', methods=['POST'])
def check_availability(room_id):
    """Check room availability for given dates."""
    try:
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        
        if not check_in_str or not check_out_str:
            return jsonify({
                'available': False,
                'message': 'Please select both check-in and check-out dates.',
                'total_price': 0
            })
        
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Validate dates
        today = datetime.now().date()
        if check_in < today:
            return jsonify({
                'available': False,
                'message': 'Check-in date cannot be in the past.',
                'total_price': 0
            })
        
        if check_out <= check_in:
            return jsonify({
                'available': False,
                'message': 'Check-out date must be after check-in date.',
                'total_price': 0
            })
        
        # Check availability
        is_available = Booking.check_availability(room_id, check_in, check_out)
        total_price = Booking.calculate_total_price(room_id, check_in, check_out)
        
        return jsonify({
            'available': is_available,
            'message': 'Room is available for the selected dates.' if is_available else 'Room is not available for the selected dates.',
            'total_price': total_price
        })
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return jsonify({
            'available': False,
            'message': 'An error occurred while checking availability.',
            'total_price': 0
        })

@bp.route('/book/<int:room_id>', methods=['POST'])
@login_required
def book(room_id):
    """Book a room."""
    try:
        room = Room.query.get_or_404(room_id)
        
        # Parse form data
        check_in_str = request.form.get('check_in')
        check_out_str = request.form.get('check_out')
        guests = int(request.form.get('guests', 1))
        
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        
        # Validate dates
        today = datetime.now().date()
        if check_in < today:
            flash('Check-in date cannot be in the past.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))
        
        if check_out <= check_in:
            flash('Check-out date must be after check-in date.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))
        
        # Check room availability
        if not Booking.check_availability(room_id, check_in, check_out):
            flash('Room is not available for the selected dates.', 'danger')
            return redirect(url_for('booking.room_detail', room_id=room_id))
        
        # Calculate total price
        total_price = Booking.calculate_total_price(room_id, check_in, check_out)
        
        # Create booking
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in_date=check_in,
            check_out_date=check_out,
            guests=guests,
            total_price=total_price,
            booking_status='confirmed',
            payment_status='paid'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Send confirmation email
        try:
            send_booking_confirmation(booking)
        except Exception as e:
            logger.error(f"Failed to send booking confirmation email: {e}")
        
        logger.info(f"New booking created: ID {booking.id} by user {current_user.username}")
        flash('Your booking has been confirmed!', 'success')
        return redirect(url_for('booking.confirmation', booking_id=booking.id))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during booking creation: {e}")
        flash('An error occurred during the booking process. Please try again.', 'danger')
        return redirect(url_for('booking.room_detail', room_id=room_id))

@bp.route('/confirmation/<int:booking_id>')
@login_required
def confirmation(booking_id):
    """Display booking confirmation."""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only see their own bookings (unless admin)
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to view this booking.', 'danger')
            return redirect(url_for('main.home'))
        
        return render_template('booking/confirmation.html', booking=booking)
    except Exception as e:
        logger.error(f"Error displaying booking confirmation: {e}")
        flash('An error occurred while loading the booking confirmation.', 'danger')
        return redirect(url_for('main.home'))

def send_booking_confirmation(booking):
    """Send booking confirmation email."""
    msg = Message(
        'Booking Confirmation - Luxury Hotel',
        recipients=[booking.user.email]
    )
    
    msg.body = f"""
    Dear {booking.user.username},
    
    Thank you for choosing Luxury Hotel. Your booking has been confirmed!
    
    Booking Details:
    - Booking ID: #{booking.id}
    - Room Type: {booking.room.room_type.title()}
    - Room Number: {booking.room.room_number}
    - Check-in Date: {booking.check_in_date.strftime('%B %d, %Y')}
    - Check-out Date: {booking.check_out_date.strftime('%B %d, %Y')}
    - Number of Guests: {booking.guests}
    - Total Price: ${booking.total_price}
    
    We look forward to welcoming you to our hotel!
    
    Best regards,
    Luxury Hotel Team
    """
    
    msg.html = f"""
    <h2>Booking Confirmation</h2>
    <p>Dear {booking.user.username},</p>
    <p>Thank you for choosing Luxury Hotel. Your booking has been confirmed!</p>
    
    <h3>Booking Details:</h3>
    <ul>
        <li><strong>Booking ID:</strong> #{booking.id}</li>
        <li><strong>Room Type:</strong> {booking.room.room_type.title()}</li>
        <li><strong>Room Number:</strong> {booking.room.room_number}</li>
        <li><strong>Check-in Date:</strong> {booking.check_in_date.strftime('%B %d, %Y')}</li>
        <li><strong>Check-out Date:</strong> {booking.check_out_date.strftime('%B %d, %Y')}</li>
        <li><strong>Number of Guests:</strong> {booking.guests}</li>
        <li><strong>Total Price:</strong> ${booking.total_price}</li>
    </ul>
    
    <p>We look forward to welcoming you to our hotel!</p>
    
    <p>Best regards,<br>
    Luxury Hotel Team</p>
    """
    
    mail.send(msg)
    logger.info(f"Booking confirmation email sent to {booking.user.email}")
