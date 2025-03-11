from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amenities = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    
    # Relationships
    bookings = db.relationship('Booking', backref='room', lazy='dynamic')
    
    @hybrid_property
    def is_available(self):
        """Check if a room is currently booked."""
        current_date = datetime.utcnow().date()
        return not Booking.query.filter(
            Booking.room_id == self.id,
            Booking.check_in_date <= current_date,
            Booking.check_out_date > current_date,
            Booking.booking_status != 'canceled'
        ).first()


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_status = db.Column(db.String(20), default='confirmed')
    payment_status = db.Column(db.String(20), default='paid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @classmethod
    def check_availability(cls, room_id, check_in_date, check_out_date, exclude_booking_id=None):
        """Check if a room is available for the given dates.
        
        Args:
            room_id: The ID of the room to check
            check_in_date: The check-in date
            check_out_date: The check-out date
            exclude_booking_id: Optional booking ID to exclude from the check (for modifications)
        
        Returns:
            bool: True if the room is available, False otherwise
        """
        query = cls.query.filter(
            cls.room_id == room_id,
            cls.booking_status != 'canceled',  # Note: fixed spelling from 'cancelled' to 'canceled'
            db.or_(
                db.and_(
                    cls.check_in_date <= check_in_date,
                    cls.check_out_date > check_in_date
                ),
                db.and_(
                    cls.check_in_date < check_out_date,
                    cls.check_out_date >= check_out_date
                ),
                db.and_(
                    cls.check_in_date >= check_in_date,
                    cls.check_out_date <= check_out_date
                )
            )
        )
        
        # If we're modifying an existing booking, exclude it from the availability check
        if exclude_booking_id:
            query = query.filter(cls.id != exclude_booking_id)
            
        overlapping_bookings = query.count()
        
        return overlapping_bookings == 0
    
    @staticmethod
    def calculate_total_price(room_id, check_in_date, check_out_date):
        """Calculate the total price for a booking."""
        room = Room.query.get(room_id)
        if not room:
            return 0
        
        days = (check_out_date - check_in_date).days
        return room.price_per_night * days
