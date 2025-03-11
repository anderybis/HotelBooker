from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField, TextAreaField, URLField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, URL, ValidationError
from datetime import date
from models import User

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class SearchForm(FlaskForm):
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('', 'Any Type'),
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('suite', 'Suite')
    ], default='')
    guests = SelectField('Number of Guests', choices=[
        (1, '1 Guest'),
        (2, '2 Guests'),
        (3, '3 Guests'),
        (4, '4 Guests'),
        (5, '5+ Guests')
    ], default=1, coerce=int)
    submit = SubmitField('Search Rooms')
    
    def validate_check_out(self, check_out):
        if self.check_in.data and check_out.data:
            if check_out.data <= self.check_in.data:
                raise ValidationError('Check-out date must be after check-in date.')
    
    def validate_check_in(self, check_in):
        if check_in.data:
            today = date.today()
            if check_in.data < today:
                raise ValidationError('Check-in date cannot be in the past.')


class BookingForm(FlaskForm):
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])
    guests = SelectField('Number of Guests', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Book Now')
    
    def validate_check_out(self, check_out):
        if self.check_in.data and check_out.data:
            if check_out.data <= self.check_in.data:
                raise ValidationError('Check-out date must be after check-in date.')
    
    def validate_check_in(self, check_in):
        if check_in.data:
            today = date.today()
            if check_in.data < today:
                raise ValidationError('Check-in date cannot be in the past.')


class RoomForm(FlaskForm):
    room_number = StringField('Room Number', validators=[DataRequired(), Length(max=10)])
    room_type = SelectField('Room Type', choices=[
        ('standard', 'Standard'),
        ('deluxe', 'Deluxe'),
        ('suite', 'Suite')
    ], validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1, max=10)])
    price_per_night = IntegerField('Price per Night', validators=[DataRequired(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[DataRequired()])
    amenities = StringField('Amenities', validators=[DataRequired()])
    image_url = URLField('Image URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Save Room')


class ModifyBookingForm(FlaskForm):
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])
    guests = SelectField('Number of Guests', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Booking')
    
    def validate_check_out(self, check_out):
        if self.check_in.data and check_out.data:
            if check_out.data <= self.check_in.data:
                raise ValidationError('Check-out date must be after check-in date.')
    
    def validate_check_in(self, check_in):
        if check_in.data:
            today = date.today()
            if check_in.data < today:
                raise ValidationError('Check-in date cannot be in the past.')
