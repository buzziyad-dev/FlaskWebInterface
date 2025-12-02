from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64),
                         unique=True,
                         nullable=False,
                         index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False, index=True)
    is_banned = db.Column(db.Boolean, default=False, index=True)
    ban_reason = db.Column(db.Text)
    reputation_score = db.Column(db.Integer, default=0, index=True)
    
    __table_args__ = (
        db.Index('idx_user_admin_banned_reputation', 'is_admin', 'is_banned', 'reputation_score'),
    )
    badge = db.Column(db.String(50))
    bio = db.Column(db.Text, default='')
    profile_picture = db.Column(db.LargeBinary)
    dark_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(10), default='en')

    reviews = db.relationship('Review', foreign_keys='Review.user_id', backref='author', lazy='dynamic')

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
        rc = self.review_count()
        if rc == 0:
            return 0
        return int(rc * 10 + self.avg_rating_given() * 5)

    def get_badge(self):
        """Get badge based on review count"""
        review_count = self.review_count()
        if review_count >= 50:
            return 'Elite Foodie'
        elif review_count >= 30:
            return 'Expert Reviewer'
        elif review_count >= 15:
            return 'Experienced Diner'
        elif review_count >= 8:
            return 'Rising Critic'
        elif review_count >= 3:
            return 'Food Explorer'
        else:
            return 'Newcomer'

    def update_reputation(self):
        """Update badge based on review count"""
        self.badge = self.get_badge()
        self.assign_auto_badges()

    def assign_auto_badges(self):
        """Automatically assign badges based on review count"""
        from models import Badge, UserBadge

        # Badge thresholds (review_count -> badge_name)
        badge_mappings = [
            (50, 'Elite Foodie'),
            (30, 'Expert Reviewer'),
            (15, 'Experienced Diner'),
            (8, 'Rising Critic'),
            (3, 'Food Explorer'),
            (0, 'Newcomer'),
        ]

        review_count = self.review_count()

        for threshold, badge_name in badge_mappings:
            if review_count >= threshold:
                # Find badge by name
                badge = Badge.query.filter_by(name=badge_name).first()
                if badge:
                    # Check if user already has this badge
                    existing = UserBadge.query.filter_by(
                        user_id=self.id, badge_id=badge.id).first()
                    if not existing:
                        # Remove previous tier badges (only keep highest tier)
                        UserBadge.query.filter_by(user_id=self.id).delete()
                        # Assign new badge
                        user_badge = UserBadge(user_id=self.id,
                                               badge_id=badge.id)
                        db.session.add(user_badge)
                break
    
    def get_highest_hierarchy_badge(self):
        """Get the badge with highest hierarchy for this user"""
        user_badges = self.custom_badges.all()
        if not user_badges:
            return None
        return max(user_badges, key=lambda ub: ub.badge.hierarchy).badge


class Cuisine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    restaurants = db.relationship('Restaurant',
                                  backref='cuisine',
                                  lazy='dynamic')


class FoodCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    working_hours = db.Column(db.String(500))
    price_range = db.Column(db.Integer, default=2, index=True)
    cuisine_id = db.Column(db.Integer,
                           db.ForeignKey('cuisine.id'),
                           nullable=False,
                           index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    image_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_small_business = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True, index=True)
    is_promoted = db.Column(db.Boolean, default=False, index=True)
    
    __table_args__ = (
        db.Index('idx_restaurant_approval_promotion', 'is_approved', 'is_promoted', 'created_at'),
        db.Index('idx_restaurant_cuisine_approval', 'cuisine_id', 'is_approved'),
    )
    food_categories = db.Column(db.JSON, default=list)
    photos = db.Column(db.JSON, default=list)
    location_latitude = db.Column(db.Float)
    location_longitude = db.Column(db.Float)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    submitter = db.relationship('User',
                                backref='submitted_restaurants',
                                foreign_keys=[user_id])
    approver = db.relationship('User',
                               backref='approved_restaurants',
                               foreign_keys=[approved_by_id])
    reviews = db.relationship('Review',
                              backref='restaurant',
                              lazy='dynamic',
                              cascade='all, delete-orphan')

    def get_formatted_hours(self):
        """Parse JSON working_hours and return formatted dict, or fallback"""
        if not self.working_hours:
            return {}
        try:
            import json
            return json.loads(self.working_hours)
        except (json.JSONDecodeError, TypeError):
            return {}

    def avg_rating(self):
        from sqlalchemy import func
        from app import db
        result = db.session.query(func.avg(Review.rating)).filter(
            Review.restaurant_id == self.id).scalar()
        return round(float(result), 1) if result else 0

    def review_count(self):
        return self.reviews.count()


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False, index=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    food_category = db.Column(db.String(100))

    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=True,
                        index=True)
    restaurant_id = db.Column(db.Integer,
                              db.ForeignKey('restaurant.id'),
                              nullable=False,
                              index=True)
    
    # Review approval fields
    is_approved = db.Column(db.Boolean, default=False, index=True)
    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    receipt_image = db.Column(db.Text, nullable=True)  # Base64 encoded receipt photo
    receipt_confirmed = db.Column(db.Boolean, default=False, index=True)  # Receipt verified by admin

    __table_args__ = (
        db.Index('idx_review_user_approval', 'user_id', 'is_approved', 'created_at'),
        db.Index('idx_review_restaurant_rating', 'restaurant_id', 'rating'),
    )

    approver = db.relationship('User',
                               backref='approved_reviews',
                               foreign_keys=[approved_by_id])

    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')

    def formatted_datetime_ksa(self):
        ksa_tz = timezone(timedelta(hours=3))
        ksa_time = self.created_at.replace(
            tzinfo=timezone.utc).astimezone(ksa_tz)
        return f"{ksa_time.strftime('%B %d, %Y')} at {ksa_time.strftime('%I:%M %p')} (KSA)"
    
    comments = db.relationship('ReviewComment',
                              backref='review',
                              lazy='dynamic',
                              cascade='all, delete-orphan')


class ReviewComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=True,
                        index=True)
    review_id = db.Column(db.Integer,
                         db.ForeignKey('review.id'),
                         nullable=False,
                         index=True)
    
    author = db.relationship('User', backref='review_comments')
    
    def formatted_datetime_ksa(self):
        ksa_tz = timezone(timedelta(hours=3))
        ksa_time = self.created_at.replace(
            tzinfo=timezone.utc).astimezone(ksa_tz)
        return f"{ksa_time.strftime('%b %d, %Y')} at {ksa_time.strftime('%I:%M %p')}"


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'),
                        nullable=False,
                        index=True)

    author = db.relationship('User', backref='news_posts')
    
    def get_plain_text(self):
        """Extract plain text from HTML content (for previews)"""
        from html.parser import HTMLParser
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.text = []
            def handle_data(self, d):
                self.text.append(d)
            def get_data(self):
                return ''.join(self.text)
        s = MLStripper()
        s.feed(self.content)
        return s.get_data()[:150] + '...'

    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    color = db.Column(db.String(7), default='#007bff')
    description = db.Column(db.String(255), default='')
    hierarchy = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_badges = db.relationship('UserBadge',
                                  backref='badge',
                                  lazy='dynamic',
                                  cascade='all, delete-orphan')


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id', ondelete='CASCADE'),
                        nullable=False,
                        index=True)
    badge_id = db.Column(db.Integer,
                         db.ForeignKey('badge.id', ondelete='CASCADE'),
                         nullable=False,
                         index=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User',
                           backref=db.backref('custom_badges',
                                              lazy='dynamic',
                                              cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('user_id',
                                          'badge_id',
                                          name='uq_user_badge'), )


class FeatureToggle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feature_name = db.Column(db.String(100),
                             unique=True,
                             nullable=False,
                             index=True)
    is_enabled = db.Column(db.Boolean, default=True)
    description = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    @staticmethod
    def get_feature_status(feature_name):
        toggle = FeatureToggle.query.filter_by(
            feature_name=feature_name).first()
        return toggle.is_enabled if toggle else True
