from datetime import datetime
from flask_mail import Message
from app import mail, db, app
from models import Room, Booking

def check_room_availability(room_id, check_in, check_out):
    """Check if a room is available for the given dates"""
    if check_in >= check_out:
        return False, "Check-out date must be after check-in date"

    # Convert string dates to datetime if needed
    if isinstance(check_in, str):
        check_in = datetime.strptime(check_in, '%Y-%m-%d').date()
    if isinstance(check_out, str):
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()

    # Check if dates are in the past
    today = datetime.utcnow().date()
    if check_in < today:
        return False, "Check-in date cannot be in the past"

    existing_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.check_out_date >= check_in,
        Booking.check_in_date <= check_out,
        Booking.booking_status != 'cancelled'  # Exclude cancelled bookings
    ).all()

    return len(existing_bookings) == 0, "Room is already booked for these dates" if existing_bookings else "Room is available"

def calculate_total_price(room_id, check_in, check_out):
    """Calculate total price for the booking"""
    room = Room.query.get(room_id)
    if not room:
        return 0

    # Convert string dates to datetime if needed
    if isinstance(check_in, str):
        check_in = datetime.strptime(check_in, '%Y-%m-%d').date()
    if isinstance(check_out, str):
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()

    delta = (check_out - check_in).days
    return room.price_per_night * delta

def send_booking_confirmation(booking):
    """Send booking confirmation email"""
    try:
        msg = Message(
            'Booking Confirmation',
            sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@hotel.com'),
            recipients=[booking.user.email]
        )
        msg.body = f"""
        Dear {booking.user.username},

        Your booking has been confirmed!

        Booking Details:
        Room: {booking.room.room_number} ({booking.room.room_type})
        Check-in: {booking.check_in_date}
        Check-out: {booking.check_out_date}
        Total Price: ${booking.total_price}

        Thank you for choosing our hotel!
        """
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Failed to send confirmation email: {str(e)}")
        return False

def process_payment(booking):
    """Mock payment processing"""
    try:
        # In a real application, this would integrate with a payment gateway
        booking.payment_status = 'paid'
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(f"Payment processing failed: {str(e)}")
        return False

def award_loyalty_points(booking):
    """Award loyalty points for a booking"""
    try:
        points = int(booking.total_price / 10)  # 1 point per $10 spent
        booking.user.loyalty_points += points
        db.session.commit()
        return True
    except Exception as e:
        app.logger.error(f"Failed to award loyalty points: {str(e)}")
        return False