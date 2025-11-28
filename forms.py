from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SelectMultipleField, IntegerField, BooleanField, FileField, HiddenField, FloatField
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
    price_range = SelectField('Price Range', choices=[(1, '$ - Budget'), (2, '$$ - Moderate'), (3, '$$$ - Expensive'), (4, '$$$$ - Very Expensive')], coerce=int, validators=[DataRequired()])
    cuisine_id = SelectField('Cuisine Type', coerce=int, validators=[DataRequired()])
    restaurant_image = FileField('Restaurant Image')
    location_latitude = FloatField('Latitude', validators=[DataRequired()])
    location_longitude = FloatField('Longitude', validators=[DataRequired()])
    
    # Working hours for each day
    monday_hours = StringField('Monday', validators=[Length(max=50)])
    tuesday_hours = StringField('Tuesday', validators=[Length(max=50)])
    wednesday_hours = StringField('Wednesday', validators=[Length(max=50)])
    thursday_hours = StringField('Thursday', validators=[Length(max=50)])
    friday_hours = StringField('Friday', validators=[Length(max=50)])
    saturday_hours = StringField('Saturday', validators=[Length(max=50)])
    sunday_hours = StringField('Sunday', validators=[Length(max=50)])
    
    food_categories = SelectMultipleField('Food Categories', coerce=int, validators=[DataRequired()])
    
    def validate_restaurant_image(self, restaurant_image):
        if restaurant_image.data and restaurant_image.data.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            filename = restaurant_image.data.filename.lower()
            if not any(filename.endswith('.' + ext) for ext in allowed_extensions):
                raise ValidationError('Only PNG and JPG files are allowed.')

class PhotoUploadForm(FlaskForm):
    photo = FileField('Upload Photo', validators=[DataRequired()])

class NewsForm(FlaskForm):
    title = StringField('News Title', validators=[DataRequired(), Length(min=5, max=200)])
    content = TextAreaField('News Content')

class ProfileEditForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    profile_picture = FileField('Profile Picture')
    
    def validate_profile_picture(self, profile_picture):
        if profile_picture.data and profile_picture.data.filename:
            allowed_extensions = {'png', 'jpg', 'jpeg'}
            filename = profile_picture.data.filename.lower()
            if not any(filename.endswith('.' + ext) for ext in allowed_extensions):
                raise ValidationError('Only PNG and JPG files are allowed.')

class ReviewCommentForm(FlaskForm):
    content = TextAreaField('Add a Comment', validators=[DataRequired(), Length(min=2, max=500)])

class AdminChangePasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])

class AdminChangeUsernameForm(FlaskForm):
    current_username = StringField('Current Username', validators=[DataRequired()])
    new_username = StringField('New Username', validators=[DataRequired(), Length(min=3, max=64)])
    
    def validate_new_username(self, new_username):
        user = User.query.filter_by(username=new_username.data).first()
        if user is not None:
            raise ValidationError('Username already exists.')
