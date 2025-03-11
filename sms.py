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
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send message
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone_number
        )
        
        logger.info(f"SMS sent successfully. SID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return False


def send_booking_confirmation_sms(booking):
    """Send booking confirmation SMS."""
    if not booking.user.phone_number:
        logger.info("No phone number available for booking confirmation SMS")
        return False
        
    message = f"""
Your Luxury Hotel booking is confirmed!
Booking #{booking.id}
{booking.room.room_type.title()} Room {booking.room.room_number}
Check-in: {booking.check_in_date.strftime('%B %d, %Y')}
Check-out: {booking.check_out_date.strftime('%B %d, %Y')}
Total: ${booking.total_price}
    """
    
    return send_sms(booking.user.phone_number, message.strip())


def send_booking_modification_sms(booking, old_data):
    """Send booking modification SMS."""
    if not booking.user.phone_number:
        logger.info("No phone number available for booking modification SMS")
        return False
        
    message = f"""
Your Luxury Hotel booking #{booking.id} has been modified.
New dates: {booking.check_in_date.strftime('%B %d, %Y')} to {booking.check_out_date.strftime('%B %d, %Y')}
New total: ${booking.total_price}
    """
    
    return send_sms(booking.user.phone_number, message.strip())


def send_booking_cancellation_sms(booking):
    """Send booking cancellation SMS."""
    if not booking.user.phone_number:
        logger.info("No phone number available for booking cancellation SMS")
        return False
        
    message = f"""
Your Luxury Hotel booking #{booking.id} has been cancelled.
Room: {booking.room.room_type.title()} {booking.room.room_number}
Dates: {booking.check_in_date.strftime('%B %d, %Y')} to {booking.check_out_date.strftime('%B %d, %Y')}
    """
    
    return send_sms(booking.user.phone_number, message.strip())