from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, mail
from models import Room, Booking
from forms import SearchForm, BookingForm, ModifyBookingForm
from datetime import datetime, date
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

@bp.route('/view/<int:booking_id>')
@login_required
def view(booking_id):
    """View booking details with options to modify or cancel."""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only see their own bookings (unless admin)
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to view this booking.', 'danger')
            return redirect(url_for('auth.profile'))
        
        today = date.today()
        
        return render_template('booking/view_booking.html', booking=booking, today=today)
    except Exception as e:
        logger.error(f"Error viewing booking details: {e}")
        flash('An error occurred while loading the booking details.', 'danger')
        return redirect(url_for('auth.profile'))

@bp.route('/modify/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def modify(booking_id):
    """Modify an existing booking."""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only modify their own bookings (unless admin)
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to modify this booking.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check if booking is in the past
        today = date.today()
        if booking.check_in_date <= today:
            flash('You cannot modify a booking that has already started or is in the past.', 'warning')
            return redirect(url_for('booking.view', booking_id=booking_id))
            
        # Check if booking is canceled
        if booking.booking_status == 'canceled':
            flash('You cannot modify a canceled booking.', 'warning')
            return redirect(url_for('booking.view', booking_id=booking_id))
        
        # Create form and populate with existing booking data
        form = ModifyBookingForm()
        
        # Set choices for guests based on room capacity
        form.guests.choices = [(i, f"{i} Guest{'s' if i > 1 else ''}") for i in range(1, booking.room.capacity + 1)]
        
        if request.method == 'GET':
            form.check_in.data = booking.check_in_date
            form.check_out.data = booking.check_out_date
            form.guests.data = booking.guests
        
        if form.validate_on_submit():
            # Check if the room is available for the new dates
            if form.check_in.data != booking.check_in_date or form.check_out.data != booking.check_out_date:
                # We need to exclude current booking when checking availability
                is_available = Booking.check_availability(booking.room_id, form.check_in.data, form.check_out.data, exclude_booking_id=booking.id)
                
                if not is_available:
                    flash('The room is not available for the selected dates.', 'danger')
                    return redirect(url_for('booking.modify', booking_id=booking_id))
            
            # Calculate new total price
            new_total_price = Booking.calculate_total_price(booking.room_id, form.check_in.data, form.check_out.data)
            
            # Store old values for notification
            old_check_in = booking.check_in_date
            old_check_out = booking.check_out_date
            old_guests = booking.guests
            old_total_price = booking.total_price
            
            # Update booking
            booking.check_in_date = form.check_in.data
            booking.check_out_date = form.check_out.data
            booking.guests = form.guests.data
            booking.total_price = new_total_price
            
            db.session.commit()
            
            # Send modification email
            try:
                send_booking_modification(booking, {
                    'old_check_in': old_check_in,
                    'old_check_out': old_check_out,
                    'old_guests': old_guests,
                    'old_total_price': old_total_price
                })
            except Exception as e:
                logger.error(f"Failed to send booking modification email: {e}")
            
            logger.info(f"Booking {booking.id} modified by user {current_user.username}")
            flash('Your booking has been successfully updated!', 'success')
            return redirect(url_for('booking.view', booking_id=booking_id))
        
        return render_template('booking/modify_booking.html', booking=booking, form=form, today=today)
    except Exception as e:
        logger.error(f"Error modifying booking: {e}")
        flash('An error occurred while processing your request.', 'danger')
        return redirect(url_for('booking.view', booking_id=booking_id))

@bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel(booking_id):
    """Cancel a booking."""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Ensure user can only cancel their own bookings (unless admin)
        if booking.user_id != current_user.id and not current_user.is_admin:
            flash('You do not have permission to cancel this booking.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check if booking is in the past
        today = date.today()
        if booking.check_in_date <= today:
            flash('You cannot cancel a booking that has already started or is in the past.', 'warning')
            return redirect(url_for('booking.view', booking_id=booking_id))
            
        # Check if booking is already canceled
        if booking.booking_status == 'canceled':
            flash('This booking is already canceled.', 'info')
            return redirect(url_for('booking.view', booking_id=booking_id))
        
        # Update booking status
        booking.booking_status = 'canceled'
        db.session.commit()
        
        # Send cancellation email
        try:
            send_booking_cancellation(booking)
        except Exception as e:
            logger.error(f"Failed to send booking cancellation email: {e}")
        
        logger.info(f"Booking {booking.id} canceled by user {current_user.username}")
        flash('Your booking has been successfully canceled.', 'success')
        return redirect(url_for('auth.profile'))
    except Exception as e:
        logger.error(f"Error canceling booking: {e}")
        flash('An error occurred while processing your request.', 'danger')
        return redirect(url_for('booking.view', booking_id=booking_id))

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
    
    try:
        mail.send(msg)
        logger.info(f"Booking confirmation email sent to {booking.user.email}")
        # Log a more detailed message for debugging
        logger.info(f"EMAIL CONTENT: Subject: {msg.subject}, Recipient: {msg.recipients}, Body: {msg.body[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")

def send_booking_modification(booking, old_data):
    """Send booking modification email."""
    msg = Message(
        'Booking Modification - Luxury Hotel',
        recipients=[booking.user.email]
    )
    
    msg.body = f"""
    Dear {booking.user.username},
    
    Your booking has been successfully modified. Here are the details:
    
    Booking Details:
    - Booking ID: #{booking.id}
    - Room Type: {booking.room.room_type.title()}
    - Room Number: {booking.room.room_number}
    
    Changes:
    - Check-in Date: {old_data['old_check_in'].strftime('%B %d, %Y')} → {booking.check_in_date.strftime('%B %d, %Y')}
    - Check-out Date: {old_data['old_check_out'].strftime('%B %d, %Y')} → {booking.check_out_date.strftime('%B %d, %Y')}
    - Number of Guests: {old_data['old_guests']} → {booking.guests}
    - Total Price: ${old_data['old_total_price']} → ${booking.total_price}
    
    If you have any questions about these changes, please contact us.
    
    Best regards,
    Luxury Hotel Team
    """
    
    msg.html = f"""
    <h2>Booking Modification</h2>
    <p>Dear {booking.user.username},</p>
    <p>Your booking has been successfully modified. Here are the details:</p>
    
    <h3>Booking Details:</h3>
    <ul>
        <li><strong>Booking ID:</strong> #{booking.id}</li>
        <li><strong>Room Type:</strong> {booking.room.room_type.title()}</li>
        <li><strong>Room Number:</strong> {booking.room.room_number}</li>
    </ul>
    
    <h3>Changes:</h3>
    <table border="0" cellpadding="5" style="border-collapse: collapse; width: 100%;">
        <tr>
            <th style="text-align: left; border-bottom: 1px solid #ddd;"></th>
            <th style="text-align: left; border-bottom: 1px solid #ddd;">Previous</th>
            <th style="text-align: left; border-bottom: 1px solid #ddd;">New</th>
        </tr>
        <tr>
            <td style="border-bottom: 1px solid #ddd;"><strong>Check-in Date</strong></td>
            <td style="border-bottom: 1px solid #ddd;">{old_data['old_check_in'].strftime('%B %d, %Y')}</td>
            <td style="border-bottom: 1px solid #ddd;">{booking.check_in_date.strftime('%B %d, %Y')}</td>
        </tr>
        <tr>
            <td style="border-bottom: 1px solid #ddd;"><strong>Check-out Date</strong></td>
            <td style="border-bottom: 1px solid #ddd;">{old_data['old_check_out'].strftime('%B %d, %Y')}</td>
            <td style="border-bottom: 1px solid #ddd;">{booking.check_out_date.strftime('%B %d, %Y')}</td>
        </tr>
        <tr>
            <td style="border-bottom: 1px solid #ddd;"><strong>Guests</strong></td>
            <td style="border-bottom: 1px solid #ddd;">{old_data['old_guests']}</td>
            <td style="border-bottom: 1px solid #ddd;">{booking.guests}</td>
        </tr>
        <tr>
            <td style="border-bottom: 1px solid #ddd;"><strong>Total Price</strong></td>
            <td style="border-bottom: 1px solid #ddd;">${old_data['old_total_price']}</td>
            <td style="border-bottom: 1px solid #ddd;">${booking.total_price}</td>
        </tr>
    </table>
    
    <p>If you have any questions about these changes, please contact us.</p>
    
    <p>Best regards,<br>
    Luxury Hotel Team</p>
    """
    
    try:
        mail.send(msg)
        logger.info(f"Booking modification email sent to {booking.user.email}")
        # Log a more detailed message for debugging
        logger.info(f"EMAIL CONTENT: Subject: {msg.subject}, Recipient: {msg.recipients}, Body: {msg.body[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send modification email: {e}")

def send_booking_cancellation(booking):
    """Send booking cancellation email."""
    msg = Message(
        'Booking Cancellation - Luxury Hotel',
        recipients=[booking.user.email]
    )
    
    msg.body = f"""
    Dear {booking.user.username},
    
    Your booking has been canceled as requested. Here is a summary of the canceled booking:
    
    Canceled Booking Details:
    - Booking ID: #{booking.id}
    - Room Type: {booking.room.room_type.title()}
    - Room Number: {booking.room.room_number}
    - Check-in Date: {booking.check_in_date.strftime('%B %d, %Y')}
    - Check-out Date: {booking.check_out_date.strftime('%B %d, %Y')}
    - Number of Guests: {booking.guests}
    - Total Price: ${booking.total_price}
    
    If this cancellation was made in error, please contact us immediately.
    
    We hope to have the opportunity to welcome you to Luxury Hotel in the future.
    
    Best regards,
    Luxury Hotel Team
    """
    
    msg.html = f"""
    <h2>Booking Cancellation</h2>
    <p>Dear {booking.user.username},</p>
    <p>Your booking has been canceled as requested. Here is a summary of the canceled booking:</p>
    
    <h3>Canceled Booking Details:</h3>
    <ul>
        <li><strong>Booking ID:</strong> #{booking.id}</li>
        <li><strong>Room Type:</strong> {booking.room.room_type.title()}</li>
        <li><strong>Room Number:</strong> {booking.room.room_number}</li>
        <li><strong>Check-in Date:</strong> {booking.check_in_date.strftime('%B %d, %Y')}</li>
        <li><strong>Check-out Date:</strong> {booking.check_out_date.strftime('%B %d, %Y')}</li>
        <li><strong>Number of Guests:</strong> {booking.guests}</li>
        <li><strong>Total Price:</strong> ${booking.total_price}</li>
    </ul>
    
    <p>If this cancellation was made in error, please contact us immediately.</p>
    
    <p>We hope to have the opportunity to welcome you to Luxury Hotel in the future.</p>
    
    <p>Best regards,<br>
    Luxury Hotel Team</p>
    """
    
    try:
        mail.send(msg)
        logger.info(f"Booking cancellation email sent to {booking.user.email}")
        # Log a more detailed message for debugging
        logger.info(f"EMAIL CONTENT: Subject: {msg.subject}, Recipient: {msg.recipients}, Body: {msg.body[:100]}...")
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")
