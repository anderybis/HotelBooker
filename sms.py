import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def send_sms(to_phone_number, message):
    """Send an SMS message using Twilio.
    
    Args:
        to_phone_number (str): The recipient's phone number in E.164 format
        message (str): The message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        logger.info(f"SMS sent successfully to {to_phone_number}. SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Failed to send SMS to {to_phone_number}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending SMS to {to_phone_number}: {str(e)}")
        return False

def send_booking_confirmation_sms(booking):
    """Send booking confirmation SMS."""
    message = f"""
    Booking Confirmed - Luxury Hotel
    
    ID: #{booking.id}
    Room: {booking.room.room_type.title()} ({booking.room.room_number})
    Check-in: {booking.check_in_date.strftime('%b %d, %Y')}
    Check-out: {booking.check_out_date.strftime('%b %d, %Y')}
    Guests: {booking.guests}
    Total: ${booking.total_price}
    
    Welcome to Luxury Hotel!
    """
    return send_sms(booking.user.phone_number, message.strip())

def send_booking_modification_sms(booking, old_data):
    """Send booking modification SMS."""
    message = f"""
    Booking Modified - Luxury Hotel
    
    ID: #{booking.id}
    Room: {booking.room.room_type.title()} ({booking.room.room_number})
    
    Changes:
    Check-in: {old_data['old_check_in'].strftime('%b %d')} → {booking.check_in_date.strftime('%b %d')}
    Check-out: {old_data['old_check_out'].strftime('%b %d')} → {booking.check_out_date.strftime('%b %d')}
    Guests: {old_data['old_guests']} → {booking.guests}
    Price: ${old_data['old_total_price']} → ${booking.total_price}
    """
    return send_sms(booking.user.phone_number, message.strip())

def send_booking_cancellation_sms(booking):
    """Send booking cancellation SMS."""
    message = f"""
    Booking Canceled - Luxury Hotel
    
    ID: #{booking.id}
    Room: {booking.room.room_type.title()} ({booking.room.room_number})
    Check-in: {booking.check_in_date.strftime('%b %d, %Y')}
    Check-out: {booking.check_out_date.strftime('%b %d, %Y')}
    
    If this was a mistake, please contact us.
    """
    return send_sms(booking.user.phone_number, message.strip())