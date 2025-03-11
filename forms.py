from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class BookingSearchForm(FlaskForm):
    check_in = DateField('Check-in Date', validators=[DataRequired()])
    check_out = DateField('Check-out Date', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('standard', 'Standard Room'),
        ('deluxe', 'Deluxe Room'),
        ('suite', 'Suite')
    ])
    guests = SelectField('Number of Guests', choices=[
        ('1', '1 Guest'),
        ('2', '2 Guests'),
        ('3', '3 Guests'),
        ('4', '4 Guests')
    ])
    submit = SubmitField('Search')

class RoomForm(FlaskForm):
    room_number = StringField('Room Number', validators=[DataRequired()])
    room_type = SelectField('Room Type', choices=[
        ('standard', 'Standard Room'),
        ('deluxe', 'Deluxe Room'),
        ('suite', 'Suite')
    ])
    capacity = SelectField('Capacity', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')])
    price_per_night = StringField('Price per Night', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    amenities = StringField('Amenities', validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[DataRequired()])
    submit = SubmitField('Save Room')
