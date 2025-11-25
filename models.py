from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    reputation_score = db.Column(db.Integer, default=0)
    badge = db.Column(db.String(50))
    
    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def review_count(self):
        return self.reviews.count()
    
    def avg_rating_given(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return sum(r.rating for r in reviews) / len(reviews)
    
    def calculate_reputation(self):
        review_count = self.review_count()
        if review_count == 0:
            return 0
        avg_rating = self.avg_rating_given()
        return int(review_count * 10 + avg_rating * 5)
    
    def get_badge(self):
        reputation = self.reputation_score if self.reputation_score else self.calculate_reputation()
        if reputation >= 100:
            return 'Elite Foodie'
        elif reputation >= 75:
            return 'Expert Reviewer'
        elif reputation >= 50:
            return 'Experienced Diner'
        elif reputation >= 25:
            return 'Rising Critic'
        elif reputation >= 10:
            return 'Food Explorer'
        else:
            return 'Newcomer'
    
    def update_reputation(self):
        self.reputation_score = self.calculate_reputation()
        self.badge = self.get_badge()

class Cuisine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    restaurants = db.relationship('Restaurant', backref='cuisine', lazy='dynamic')

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    working_hours = db.Column(db.String(100))
    price_range = db.Column(db.Integer, default=2)
    cuisine_id = db.Column(db.Integer, db.ForeignKey('cuisine.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_small_business = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    has_vegetarian = db.Column(db.Boolean, default=False)
    has_vegan = db.Column(db.Boolean, default=False)
    is_halal = db.Column(db.Boolean, default=True)
    has_gluten_free = db.Column(db.Boolean, default=False)
    photos = db.Column(db.JSON, default=list)
    
    submitter = db.relationship('User', backref='submitted_restaurants', foreign_keys=[user_id])
    reviews = db.relationship('Review', backref='restaurant', lazy='dynamic', cascade='all, delete-orphan')
    
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)
    
    def review_count(self):
        return self.reviews.count()

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    
    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')
