from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta

# Association table for followers
user_follow = db.Table('user_follow',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('following_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)


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
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.Text)
    reputation_score = db.Column(db.Integer, default=0, index=True)
    badge = db.Column(db.String(50))
    bio = db.Column(db.Text, default='')
    profile_picture = db.Column(db.LargeBinary)
    dark_mode = db.Column(db.Boolean, default=False)

    reviews = db.relationship('Review', backref='author', lazy='dynamic')
    
    # Follower/Following relationship
    followers = db.relationship(
        'User',
        secondary='user_follow',
        primaryjoin='User.id==user_follow.c.following_id',
        secondaryjoin='User.id==user_follow.c.follower_id',
        backref='following',
        lazy='dynamic'
    )

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
        reputation = self.reputation_score if self.reputation_score else self.calculate_reputation(
        )
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
        self.assign_auto_badges()

    def assign_auto_badges(self):
        """Automatically assign badges based on reputation"""
        from models import Badge, UserBadge

        # Badge thresholds (reputation -> badge_name)
        badge_mappings = [
            (100, 'Elite Foodie'),
            (75, 'Expert Reviewer'),
            (50, 'Experienced Diner'),
            (25, 'Rising Critic'),
            (10, 'Food Explorer'),
            (0, 'Newcomer'),
        ]

        reputation = self.reputation_score or self.calculate_reputation()

        for threshold, badge_name in badge_mappings:
            if reputation >= threshold:
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
    
    def follow(self, user):
        """Follow another user"""
        if not self.is_following(user):
            self.following.append(user)
            db.session.commit()
    
    def unfollow(self, user):
        """Unfollow another user"""
        if self.is_following(user):
            self.following.remove(user)
            db.session.commit()
    
    def is_following(self, user):
        """Check if following another user"""
        return self.following.filter(user_follow.c.following_id == user.id).first() is not None
    
    def follower_count(self):
        """Get count of followers"""
        return self.followers.count()
    
    def following_count(self):
        """Get count of users this user is following"""
        return self.following.count()


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
    food_categories = db.Column(db.JSON, default=list)
    photos = db.Column(db.JSON, default=list)
    location_latitude = db.Column(db.Float)
    location_longitude = db.Column(db.Float)

    submitter = db.relationship('User',
                                backref='submitted_restaurants',
                                foreign_keys=[user_id])
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
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

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

    def formatted_date(self):
        return self.created_at.strftime('%B %d, %Y')

    def formatted_datetime_ksa(self):
        ksa_tz = timezone(timedelta(hours=3))
        ksa_time = self.created_at.replace(
            tzinfo=timezone.utc).astimezone(ksa_tz)
        return f"{ksa_time.strftime('%B %d, %Y')} at {ksa_time.strftime('%I:%M %p')} (KSA)"


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
