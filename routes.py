from flask import render_template, redirect, url_for, flash, request
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

@app.route('/')
def index():
    featured_restaurants = Restaurant.query.filter_by(is_approved=True, is_featured=True).order_by(Restaurant.created_at.desc()).limit(3).all()
    regular_restaurants = Restaurant.query.filter_by(is_approved=True, is_featured=False).order_by(Restaurant.created_at.desc()).limit(6).all()
    cuisines = Cuisine.query.all()
    top_reviewers = User.query.all()
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
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)

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
    dietary_filter = request.args.get('dietary', '')
    
    query = Restaurant.query.filter_by(is_approved=True)
    
    if cuisine_filter:
        query = query.filter_by(cuisine_id=cuisine_filter)
    
    if price_filter:
        query = query.filter_by(price_range=price_filter)
    
    if search_query:
        query = query.filter(Restaurant.name.ilike(f'%{search_query}%'))
    
    if dietary_filter == 'vegetarian':
        query = query.filter_by(has_vegetarian=True)
    elif dietary_filter == 'vegan':
        query = query.filter_by(has_vegan=True)
    elif dietary_filter == 'halal':
        query = query.filter_by(is_halal=True)
    elif dietary_filter == 'gluten_free':
        query = query.filter_by(has_gluten_free=True)
    
    all_restaurants = query.all()
    
    if rating_filter:
        all_restaurants = [r for r in all_restaurants if r.avg_rating() >= rating_filter]
    
    cuisines = Cuisine.query.all()
    
    return render_template('restaurants.html', restaurants=all_restaurants, cuisines=cuisines, 
                         current_cuisine=cuisine_filter, current_price=price_filter, 
                         current_rating=rating_filter, current_dietary=dietary_filter, search_query=search_query)

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
    
    if file and file.content_type.startswith('image/'):
        try:
            photo_data = file.read()
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
            flash(f'Error uploading photo: {str(e)}', 'danger')
    else:
        flash('Only image files are allowed', 'danger')
    
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
    if form.validate_on_submit():
        review = Review(
            rating=form.rating.data,
            title=form.title.data,
            content=form.content.data,
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
        restaurant = Restaurant(
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            phone=form.phone.data,
            working_hours=form.working_hours.data,
            price_range=form.price_range.data,
            cuisine_id=form.cuisine_id.data,
            image_url=form.image_url.data,
            is_small_business=form.is_small_business.data,
            has_vegetarian=form.has_vegetarian.data,
            has_vegan=form.has_vegan.data,
            is_halal=form.is_halal.data,
            has_gluten_free=form.has_gluten_free.data,
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

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    pending_restaurants = Restaurant.query.filter_by(is_approved=False).order_by(Restaurant.created_at.desc()).all()
    approved_restaurants = Restaurant.query.filter_by(is_approved=True).order_by(Restaurant.created_at.desc()).limit(10).all()
    total_users = User.query.count()
    total_reviews = Review.query.count()
    
    return render_template('admin_dashboard.html', 
                         pending=pending_restaurants,
                         approved=approved_restaurants,
                         total_users=total_users,
                         total_reviews=total_reviews)

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
    all_users = User.query.filter(User.reputation_score > 0).all()
    all_users.sort(key=lambda u: u.reputation_score, reverse=True)
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
    return redirect(url_for('admin_dashboard'))
