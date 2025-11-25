from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SelectMultipleField, IntegerField, BooleanField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class LoginForm(FlaskForm):
    user_input = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class ReviewForm(FlaskForm):
    rating = SelectField('Rating', choices=[(5, '5 Stars'), (4, '4 Stars'), (3, '3 Stars'), (2, '2 Stars'), (1, '1 Star')], coerce=int, validators=[DataRequired()])
    title = StringField('Review Title', validators=[Length(max=100)])
    content = TextAreaField('Your Review', validators=[DataRequired(), Length(min=10, max=1000)])
    food_category = SelectField('What did you try?', choices=[], render_kw={'data-placeholder': 'Optional - select a food category...'})

class RestaurantForm(FlaskForm):
    name = StringField('Restaurant Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    address = StringField('Address', validators=[DataRequired(), Length(max=200)])
    phone = StringField('Phone Number', validators=[Length(max=20)])
    working_hours = StringField('Working Hours', validators=[Length(max=100)])
    price_range = SelectField('Price Range', choices=[(1, '$ - Budget'), (2, '$$ - Moderate'), (3, '$$$ - Expensive'), (4, '$$$$ - Very Expensive')], coerce=int, validators=[DataRequired()])
    cuisine_id = SelectField('Cuisine Type', coerce=int, validators=[DataRequired()])
    image_url = StringField('Image URL', validators=[Length(max=500)])
    food_categories = SelectMultipleField('Food Categories', coerce=int, validators=[DataRequired()])

class PhotoUploadForm(FlaskForm):
    photo = FileField('Upload Photo', validators=[DataRequired()])

class NewsForm(FlaskForm):
    title = StringField('News Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('News Content', validators=[DataRequired(), Length(min=20, max=5000)])
