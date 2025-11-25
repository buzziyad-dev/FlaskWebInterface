from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db, login_manager
from models import User, Restaurant, Review, Cuisine
from forms import RegistrationForm, LoginForm, ReviewForm, RestaurantForm, PhotoUploadForm
import base64
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def check_banned_user():
    if current_user.is_authenticated:
        # Refresh user data from database to check if they've been banned
        user = User.query.get(current_user.id)
        if user and user.is_banned:
            logout_user()
            flash('Your account has been banned.', 'danger')
            return redirect(url_for('banned', username=user.username))

@app.route('/')
def index():
    featured_restaurants = Restaurant.query.filter_by(is_approved=True, is_featured=True).order_by(Restaurant.created_at.desc()).limit(3).all()
    regular_restaurants = Restaurant.query.filter_by(is_approved=True, is_featured=False).order_by(Restaurant.created_at.desc()).limit(6).all()
    cuisines = Cuisine.query.all()
    # Get top reviewers excluding admin users
    top_reviewers = User.query.filter(User.is_admin == False).all()
    top_reviewers.sort(key=lambda u: u.review_count(), reverse=True)
    top_reviewers = top_reviewers[:4]
    return render_template('index.html', featured=featured_restaurants, restaurants=regular_restaurants, cuisines=cuisines, top_reviewers=top_reviewers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registration successful! Welcome to Yalla!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user_input = form.user_input.data
        # Try to find user by username or email
        user = User.query.filter((User.username == user_input) | (User.email == user_input)).first()
        if user and user.check_password(form.password.data):
            # Check if user is banned
            if user.is_banned:
                flash('Your account has been banned.', 'danger')
                return redirect(url_for('banned', username=user.username))
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Please check your username/email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/banned/<username>')
def banned(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not user.is_banned:
        return redirect(url_for('index'))
    return render_template('banned.html', user=user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/restaurants')
def restaurants():
    cuisine_filter = request.args.get('cuisine', type=int)
    price_filter = request.args.get('price', type=int)
    rating_filter = request.args.get('rating', type=int)
    search_query = request.args.get('search', '')
    
    query = Restaurant.query.filter_by(is_approved=True)
    
    if cuisine_filter:
        query = query.filter_by(cuisine_id=cuisine_filter)
    
    if price_filter:
        query = query.filter_by(price_range=price_filter)
    
    if search_query:
        query = query.filter(Restaurant.name.ilike(f'%{search_query}%'))
    
    all_restaurants = query.all()
    
    if rating_filter:
        all_restaurants = [r for r in all_restaurants if r.avg_rating() >= rating_filter]
    
    cuisines = Cuisine.query.all()
    
    return render_template('restaurants.html', restaurants=all_restaurants, cuisines=cuisines, 
                         current_cuisine=cuisine_filter, current_price=price_filter, 
                         current_rating=rating_filter, search_query=search_query)

@app.route('/restaurant/<int:id>')
def restaurant_detail(id):
    restaurant = Restaurant.query.get_or_404(id)
    reviews = restaurant.reviews.order_by(Review.created_at.desc()).all()
    photo_form = PhotoUploadForm()
    return render_template('restaurant_detail.html', restaurant=restaurant, reviews=reviews, photo_form=photo_form)

@app.route('/restaurant/<int:id>/upload-photo', methods=['POST'])
@login_required
def upload_restaurant_photo(id):
    from datetime import datetime
    restaurant = Restaurant.query.get_or_404(id)
    
    if 'photo' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('restaurant_detail', id=id))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('restaurant_detail', id=id))
    
    # Validate file upload more strictly
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    if file and file.filename:
        # Validate MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            flash('Only JPEG, PNG, GIF, and WebP images are allowed', 'danger')
        else:
            try:
                photo_data = file.read()
                
                # Validate file size
                if len(photo_data) > MAX_FILE_SIZE:
                    flash('File size exceeds 5MB limit', 'danger')
                else:
                    encoded_photo = base64.b64encode(photo_data).decode('utf-8')
                    
                    if not restaurant.photos:
                        restaurant.photos = []
                    
                    restaurant.photos.append({
                        'data': encoded_photo,
                        'content_type': file.content_type,
                        'uploaded_by': current_user.username,
                        'uploaded_at': datetime.utcnow().isoformat()
                    })
                    
                    db.session.commit()
                    flash('Photo uploaded successfully!', 'success')
            except Exception as e:
                flash('Error uploading photo. Please try again.', 'danger')
    else:
        flash('Please select a file to upload', 'danger')
    
    return redirect(url_for('restaurant_detail', id=id))

@app.route('/restaurant/<int:id>/review', methods=['GET', 'POST'])
@login_required
def add_review(id):
    restaurant = Restaurant.query.get_or_404(id)
    
    existing_review = Review.query.filter_by(user_id=current_user.id, restaurant_id=id).first()
    if existing_review:
        flash('You have already reviewed this restaurant.', 'warning')
        return redirect(url_for('restaurant_detail', id=id))
    
    form = ReviewForm()
    # Populate menu tag choices from restaurant's menu_tags
    if restaurant.menu_tags:
        form.menu_tag.choices = [(tag, tag) for tag in restaurant.menu_tags]
    else:
        form.menu_tag.choices = [('', 'No menu categories available')]
    
    if form.validate_on_submit():
        review = Review(
            rating=form.rating.data,
            title=form.title.data,
            content=form.content.data,
            menu_tag=form.menu_tag.data if form.menu_tag.data else None,
            user_id=current_user.id,
            restaurant_id=id
        )
        db.session.add(review)
        current_user.update_reputation()
        db.session.commit()
        flash('Your review has been posted!', 'success')
        return redirect(url_for('restaurant_detail', id=id))
    
    return render_template('add_review.html', form=form, restaurant=restaurant)

@app.route('/add-restaurant', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    form = RestaurantForm()
    form.cuisine_id.choices = [(c.id, c.name) for c in Cuisine.query.all()]
    
    if form.validate_on_submit():
        # Parse menu tags from comma-separated input
        menu_tags = [tag.strip() for tag in form.menu_tags.data.split(',') if tag.strip()] if form.menu_tags.data else []
        
        restaurant = Restaurant(
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            phone=form.phone.data,
            working_hours=form.working_hours.data,
            price_range=form.price_range.data,
            cuisine_id=form.cuisine_id.data,
            user_id=current_user.id,
            image_url=form.image_url.data,
            is_small_business=form.is_small_business.data,
            menu_tags=menu_tags,
            is_approved=False
        )
        db.session.add(restaurant)
        db.session.commit()
        flash('Restaurant submitted for review! An admin will approve it shortly.', 'success')
        return redirect(url_for('restaurants'))
    
    return render_template('add_restaurant.html', form=form)

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    reviews = user.reviews.order_by(Review.created_at.desc()).all()
    return render_template('profile.html', user=user, reviews=reviews)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        restaurants = Restaurant.query.filter(
            Restaurant.is_approved == True,
            Restaurant.name.ilike(f'%{query}%')
        ).all()
    else:
        restaurants = []
    return render_template('search_results.html', restaurants=restaurants, query=query)

def get_admin_data():
    """Helper function to get all admin data"""
    pending_restaurants = Restaurant.query.filter_by(is_approved=False).order_by(Restaurant.created_at.desc()).all()
    approved_restaurants = Restaurant.query.filter_by(is_approved=True).order_by(Restaurant.created_at.desc()).all()
    all_users = User.query.all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    all_cuisines = Cuisine.query.all()
    
    return {
        'pending': pending_restaurants,
        'approved': approved_restaurants,
        'all_users': all_users,
        'all_reviews': all_reviews,
        'all_cuisines': all_cuisines,
        'total_users': len(all_users),
        'total_reviews': len(all_reviews)
    }

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    tab = request.args.get('tab', 'overview')
    data = get_admin_data()
    
    return render_template('admin_dashboard.html',
                         tab=tab,
                         pending=data['pending'],
                         approved=data['approved'],
                         all_users=data['all_users'],
                         all_reviews=data['all_reviews'],
                         all_cuisines=data['all_cuisines'],
                         total_users=data['total_users'],
                         total_reviews=data['total_reviews'])

@app.route('/admin/api/data')
@login_required
def admin_api_data():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = get_admin_data()
    
    # Format data for JSON response
    def format_restaurant(r):
        return {
            'id': r.id,
            'name': r.name,
            'cuisine': r.cuisine.name,
            'description': r.description[:100],
            'full_description': r.description,
            'address': r.address,
            'phone': r.phone,
            'working_hours': r.working_hours,
            'price_range': r.price_range,
            'is_small_business': r.is_small_business,
            'is_featured': r.is_featured,
            'is_approved': r.is_approved,
            'menu_tags': r.menu_tags if r.menu_tags else [],
            'review_count': r.review_count(),
            'avg_rating': r.avg_rating(),
            'created_at': r.created_at.strftime('%b %d, %Y'),
            'submitter_username': r.submitter.username if r.submitter else 'Unknown',
            'submitter_email': r.submitter.email if r.submitter else 'Unknown'
        }
    
    def format_user(u):
        return {
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_admin': u.is_admin,
            'is_banned': u.is_banned,
            'ban_reason': u.ban_reason,
            'reputation_score': u.reputation_score or u.calculate_reputation(),
            'review_count': u.review_count(),
            'created_at': u.created_at.strftime('%b %d, %Y')
        }
    
    def format_review(r):
        return {
            'id': r.id,
            'author_id': r.user_id,
            'author_username': r.author.username if r.author else 'Deleted User',
            'restaurant_name': r.restaurant.name,
            'restaurant_id': r.restaurant.id,
            'rating': r.rating,
            'title': r.title,
            'content': r.content[:80] + '...' if len(r.content) > 80 else r.content,
            'created_at': r.created_at.strftime('%b %d, %Y')
        }
    
    def format_cuisine(c):
        return {
            'id': c.id,
            'name': c.name
        }
    
    return jsonify({
        'pending': [format_restaurant(r) for r in data['pending']],
        'approved': [format_restaurant(r) for r in data['approved']],
        'all_users': [format_user(u) for u in data['all_users']],
        'all_reviews': [format_review(r) for r in data['all_reviews']],
        'all_cuisines': [format_cuisine(c) for c in data['all_cuisines']],
        'total_users': data['total_users'],
        'total_reviews': data['total_reviews']
    })

@app.route('/admin/approve/<int:id>', methods=['POST'])
@login_required
def approve_restaurant(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(id)
    restaurant.is_approved = True
    db.session.commit()
    flash(f'{restaurant.name} has been approved!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:id>', methods=['POST'])
@login_required
def reject_restaurant(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(id)
    db.session.delete(restaurant)
    db.session.commit()
    flash(f'{restaurant.name} has been rejected and removed.', 'warning')
    return redirect(url_for('admin_dashboard'))

@app.route('/leaderboard')
def leaderboard():
    # Only show non-admin users who have written at least one review - using optimized query
    from sqlalchemy import func
    all_users = User.query.filter(User.is_admin == False).join(Review).group_by(User.id).having(
        func.count(Review.id) > 0
    ).all()
    # Sort by reputation score in memory
    all_users.sort(key=lambda u: u.reputation_score or u.calculate_reputation(), reverse=True)
    return render_template('leaderboard.html', users=all_users)

@app.route('/admin/toggle-featured/<int:id>', methods=['POST'])
@login_required
def toggle_featured(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(id)
    restaurant.is_featured = not restaurant.is_featured
    db.session.commit()
    status = 'featured' if restaurant.is_featured else 'unfeatured'
    flash(f'{restaurant.name} is now {status}!', 'success')
    return redirect(url_for('admin_dashboard', tab='restaurants'))

@app.route('/admin/delete-restaurant/<int:id>', methods=['POST'])
@login_required
def delete_restaurant(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(id)
    name = restaurant.name
    db.session.delete(restaurant)
    db.session.commit()
    flash(f'{name} has been deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='restaurants'))

@app.route('/admin/manage-user/<int:id>', methods=['POST'])
@login_required
def manage_user(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(id)
    action = request.form.get('action')
    
    if action == 'toggle_admin':
        user.is_admin = not user.is_admin
        status = 'promoted to admin' if user.is_admin else 'demoted from admin'
        flash(f'{user.username} has been {status}.', 'success')
    elif action == 'delete':
        username = user.username
        # Set all reviews to have NULL user_id instead of deleting them
        Review.query.filter_by(user_id=id).update({'user_id': None})
        db.session.delete(user)
        flash(f'{username} has been deleted.', 'success')
    elif action == 'ban':
        ban_reason = request.form.get('ban_reason', '').strip()[:500]  # Limit length & strip whitespace
        user.is_banned = True
        user.ban_reason = ban_reason if ban_reason else 'No reason provided'
        flash(f'{user.username} has been banned.', 'success')
    elif action == 'unban':
        user.is_banned = False
        user.ban_reason = None
        flash(f'{user.username} has been unbanned.', 'success')
    elif action == 'edit':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        
        # Validate new username uniqueness (excluding current user)
        if new_username and new_username != user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash('Username already taken.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
        
        # Validate new email uniqueness (excluding current user)
        if new_email and new_email != user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash('Email already registered.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
        
        # Update fields
        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        try:
            user.reputation_score = int(request.form.get('reputation_score', user.reputation_score))
        except (ValueError, TypeError):
            user.reputation_score = user.reputation_score
        
        flash(f'User has been updated.', 'success')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard', tab='users'))

@app.route('/admin/edit-restaurant/<int:id>', methods=['POST'])
@login_required
def edit_restaurant(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(id)
    
    # Validate and sanitize inputs
    try:
        restaurant.name = request.form.get('name', restaurant.name).strip()[:100] or restaurant.name
        restaurant.description = request.form.get('description', restaurant.description).strip()[:1000] or restaurant.description
        restaurant.address = request.form.get('address', restaurant.address).strip()[:200] or restaurant.address
        restaurant.phone = request.form.get('phone', restaurant.phone).strip()[:20] or restaurant.phone
        restaurant.working_hours = request.form.get('working_hours', restaurant.working_hours).strip()[:100] or restaurant.working_hours
        
        # Validate cuisine exists
        cuisine_id = int(request.form.get('cuisine_id', restaurant.cuisine_id))
        if not Cuisine.query.get(cuisine_id):
            flash('Invalid cuisine selected.', 'danger')
            return redirect(url_for('admin_dashboard', tab='restaurants'))
        restaurant.cuisine_id = cuisine_id
        
        # Validate price range
        price_range = int(request.form.get('price_range', restaurant.price_range))
        if price_range not in [1, 2, 3, 4]:
            price_range = restaurant.price_range
        restaurant.price_range = price_range
        
        restaurant.is_small_business = request.form.get('is_small_business') == 'on'
        
        # Parse menu tags from comma-separated input
        menu_tags_input = request.form.get('menu_tags', '').strip()
        restaurant.menu_tags = [tag.strip() for tag in menu_tags_input.split(',') if tag.strip()] if menu_tags_input else []
        
        db.session.commit()
        flash(f'{restaurant.name} has been updated.', 'success')
    except (ValueError, TypeError) as e:
        flash('Error updating restaurant. Please check your input.', 'danger')
    
    return redirect(url_for('admin_dashboard', tab='restaurants'))

@app.route('/admin/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    item_type = request.form.get('type')
    ids = request.form.getlist('ids[]')
    
    # Validate item_type to prevent errors
    if not item_type or item_type not in ['user', 'restaurant', 'review', 'cuisine']:
        flash('Invalid item type.', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if item_type == 'user':
        for user_id in ids:
            Review.query.filter_by(user_id=int(user_id)).update({'user_id': None})
            User.query.filter_by(id=int(user_id)).delete()
        flash(f'Deleted {len(ids)} user(s).', 'success')
    elif item_type == 'restaurant':
        Restaurant.query.filter(Restaurant.id.in_([int(id) for id in ids])).delete()
        flash(f'Deleted {len(ids)} restaurant(s).', 'success')
    elif item_type == 'review':
        Review.query.filter(Review.id.in_([int(id) for id in ids])).delete()
        flash(f'Deleted {len(ids)} review(s).', 'success')
    elif item_type == 'cuisine':
        Cuisine.query.filter(Cuisine.id.in_([int(id) for id in ids])).delete()
        flash(f'Deleted {len(ids)} cuisine(s).', 'success')
    
    db.session.commit()
    tab_mapping = {'review': 'reviews', 'cuisine': 'cuisines', 'user': 'users', 'restaurant': 'restaurants'}
    return redirect(url_for('admin_dashboard', tab=tab_mapping.get(item_type, 'overview')))

@app.route('/admin/delete-review/<int:id>', methods=['POST'])
@login_required
def delete_review(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    review = Review.query.get_or_404(id)
    db.session.delete(review)
    db.session.commit()
    flash('Review has been deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='reviews'))

@app.route('/admin/add-cuisine', methods=['POST'])
@login_required
def add_cuisine():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    cuisine_name = request.form.get('name')
    if cuisine_name:
        cuisine = Cuisine(name=cuisine_name)
        db.session.add(cuisine)
        db.session.commit()
        flash(f'{cuisine_name} has been added.', 'success')
    else:
        flash('Please enter a cuisine name.', 'danger')
    
    return redirect(url_for('admin_dashboard', tab='cuisines'))

@app.route('/admin/delete-cuisine/<int:id>', methods=['POST'])
@login_required
def delete_cuisine(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    cuisine = Cuisine.query.get_or_404(id)
    name = cuisine.name
    db.session.delete(cuisine)
    db.session.commit()
    flash(f'{name} has been deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='cuisines'))

@app.route('/admin/edit-cuisine/<int:id>', methods=['POST'])
@login_required
def edit_cuisine(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    cuisine = Cuisine.query.get_or_404(id)
    new_name = request.form.get('name', cuisine.name)
    
    if new_name:
        cuisine.name = new_name
        db.session.commit()
        flash(f'Cuisine has been updated to {new_name}.', 'success')
    else:
        flash('Please enter a cuisine name.', 'danger')
    
    return redirect(url_for('admin_dashboard', tab='cuisines'))
