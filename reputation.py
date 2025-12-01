"""
Reputation System for Yalla
Manages reputation points earned by users for various actions.

Point System:
- 5 points for posting a review
- 10 points for adding a restaurant with approved status
"""

from app import db
from models import User


def award_review_points(user_id):
    """Award 5 points to user for posting a review"""
    if not user_id:
        return False
    
    user = User.query.get(user_id)
    if not user:
        return False
    
    user.reputation_score = (user.reputation_score or 0) + 5
    db.session.commit()
    return True


def award_restaurant_points(user_id):
    """Award 10 points to user for adding a restaurant with approved status"""
    if not user_id:
        return False
    
    user = User.query.get(user_id)
    if not user:
        return False
    
    user.reputation_score = (user.reputation_score or 0) + 10
    db.session.commit()
    return True


def get_user_reputation(user_id):
    """Get user's current reputation score"""
    user = User.query.get(user_id)
    if not user:
        return 0
    return user.reputation_score or 0


def reset_user_reputation(user_id):
    """Reset user's reputation score to 0 (admin function)"""
    user = User.query.get(user_id)
    if not user:
        return False
    
    user.reputation_score = 0
    db.session.commit()
    return True
