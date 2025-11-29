from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, login_manager
from models import User, Restaurant, Review, Cuisine, News, FoodCategory, FeatureToggle, ReviewComment
from forms import RegistrationForm, LoginForm, ReviewForm, RestaurantForm, PhotoUploadForm, NewsForm, ProfileEditForm, ReviewCommentForm, AdminChangePasswordForm, AdminChangeUsernameForm
import base64
import os


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def check_banned_user():
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        if user and user.is_banned:
            logout_user()
            flash('Your account has been banned.', 'danger')
            return redirect(url_for('banned', username=user.username))


def get_client_ip():
    """Get the client's IP address, considering proxy headers"""
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs, get the first one
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


@app.before_request
def check_maintenance_mode():
    """Check if maintenance mode is enabled - redirect non-admins to maintenance page"""
    if FeatureToggle.get_feature_status('maintenance_mode'):
        # Allow admins and certain routes to bypass maintenance mode
        if current_user.is_authenticated and current_user.is_admin:
            return None
        
        # Check if client IP is whitelisted
        whitelisted_ips = os.environ.get('MAINTENANCE_WHITELIST_IPS', '')
        if whitelisted_ips:
            client_ip = get_client_ip()
            ip_list = [ip.strip() for ip in whitelisted_ips.split(',')]
            if client_ip in ip_list:
                return None
        
        # Routes that should be accessible during maintenance
        allowed_routes = ['maintenance', 'login', 'logout', 'banned', 'restaurant_detail', 'restaurants']
        if request.endpoint and request.endpoint in allowed_routes:
            return None
        
        # API routes for admins
        if request.endpoint and request.endpoint.startswith('admin_'):
            if not (current_user.is_authenticated and current_user.is_admin):
                return redirect(url_for('maintenance'))
            return None
        
        # Redirect to maintenance page for all other routes
        return redirect(url_for('maintenance'))


@app.before_request
def refresh_user_dark_mode():
    """Refresh user dark mode preference from database on each request"""
    if current_user.is_authenticated:
        user = User.query.get(current_user.id)
        if user:
            current_user.dark_mode = user.dark_mode


@app.route('/')
def index():
    from sqlalchemy import func
    promoted_restaurants = Restaurant.query.filter_by(
        is_approved=True, is_promoted=True).order_by(
            Restaurant.created_at.desc()).limit(6).all()
    regular_restaurants = Restaurant.query.filter_by(
        is_approved=True).order_by(Restaurant.created_at.desc()).all()
    cuisines = Cuisine.query.all()
    top_reviewers = (User.query.filter(
        User.is_admin == False, User.is_banned == False).join(Review).group_by(
            User.id).having(func.count(Review.id) > 0).order_by(
                User.reputation_score.desc()).limit(4).all())
    return render_template('index.html',
                           promoted=promoted_restaurants,
                           restaurants=regular_restaurants,
                           cuisines=cuisines,
                           top_reviewers=top_reviewers)


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
        user = User.query.filter((User.username == user_input)
                                 | (User.email == user_input)).first()
        if user and user.check_password(form.password.data):
            if user.is_banned:
                flash('Your account has been banned.', 'danger')
                return redirect(url_for('banned', username=user.username))
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(
                url_for('index'))
        flash('Login failed. Please check your username/email and password.',
              'danger')
    return render_template('login.html', form=form)


@app.route('/banned/<username>')
def banned(username):
    user = User.query.filter_by(username=username).first()
    if not user or not user.is_banned:
        return redirect(url_for('index'))
    return render_template('banned.html', user=user)


@app.route('/maintenance')
def maintenance():
    """Maintenance mode page for non-admin users"""
    return render_template('maintenance.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/review/<int:review_id>/comment', methods=['POST'])
@login_required
def add_comment(review_id):
    review = Review.query.get_or_404(review_id)
    form = ReviewCommentForm()
    if form.validate_on_submit():
        comment = ReviewComment(content=form.content.data, user_id=current_user.id, review_id=review.id)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    return redirect(url_for('restaurant_detail', id=review.restaurant_id) + f'#review-{review.id}')


@app.route('/comment/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = ReviewComment.query.get_or_404(comment_id)
    review_id = comment.review_id
    restaurant_id = comment.review.restaurant_id
    
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'status': 'deleted'}), 200


@app.route("/save_dark_mode", methods=["POST"])
def save_dark_mode():
    if not current_user.is_authenticated:
        return {"status": "unauthenticated"}, 401

    dark_mode_value = request.form.get("darkMode") == "true"
    current_user.dark_mode = dark_mode_value
    db.session.commit()
    return {"status": "ok", "dark_mode": dark_mode_value}, 200


@app.route('/restaurants')
def restaurants():
    if not FeatureToggle.get_feature_status('restaurant_filtering_enabled'):
        flash('Restaurant browsing is temporarily disabled.', 'warning')
        return redirect(url_for('index'))
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
        all_restaurants = [
            r for r in all_restaurants if r.avg_rating() >= rating_filter
        ]
    cuisines = Cuisine.query.all()
    return render_template('restaurants.html',
                           restaurants=all_restaurants,
                           cuisines=cuisines,
                           current_cuisine=cuisine_filter,
                           current_price=price_filter,
                           current_rating=rating_filter,
                           search_query=search_query)


@app.route('/restaurant/<int:id>')
def restaurant_detail(id):
    restaurant = Restaurant.query.get_or_404(id)
    reviews = restaurant.reviews.all()
    reviews = sorted(
        reviews,
        key=lambda r:
        (not (r.author and r.author.is_admin), -r.created_at.timestamp()))
    photo_form = PhotoUploadForm()
    comment_form = ReviewCommentForm()
    return render_template('restaurant_detail.html',
                           restaurant=restaurant,
                           reviews=reviews,
                           photo_form=photo_form,
                           comment_form=comment_form)


@app.route('/restaurant/<int:id>/upload-photo', methods=['POST'])
@login_required
def upload_restaurant_photo(id):
    if not FeatureToggle.get_feature_status('photo_uploads_enabled'):
        flash('Photo uploads are currently disabled.', 'warning')
        return redirect(url_for('restaurant_detail', id=id))
    from datetime import datetime
    restaurant = Restaurant.query.get_or_404(id)
    if 'photo' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('restaurant_detail', id=id))
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('restaurant_detail', id=id))
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    if file and file.filename:
        if file.content_type not in ALLOWED_MIME_TYPES:
            flash('Only JPEG, PNG, GIF, and WebP images are allowed', 'danger')
        else:
            try:
                photo_data = file.read()
                if len(photo_data) > MAX_FILE_SIZE:
                    flash('File size exceeds 5MB limit', 'danger')
                else:
                    encoded_photo = base64.b64encode(photo_data).decode(
                        'utf-8')
                    if restaurant.photos is None:
                        restaurant.photos = []
                    new_photo = {
                        'data': encoded_photo,
                        'content_type': file.content_type,
                        'uploaded_by': current_user.username,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                    restaurant.photos = restaurant.photos + [new_photo]
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(restaurant, 'photos')
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
    if not FeatureToggle.get_feature_status('reviews_enabled'):
        flash('Reviews are currently disabled by administrators.', 'warning')
        return redirect(url_for('restaurant_detail', id=id))
    restaurant = Restaurant.query.get_or_404(id)
    existing_review = Review.query.filter_by(user_id=current_user.id,
                                             restaurant_id=id).first()
    if existing_review:
        flash('You have already reviewed this restaurant.', 'warning')
        return redirect(url_for('restaurant_detail', id=id))
    form = ReviewForm()
    if restaurant.food_categories:
        form.food_category.choices = [(tag, tag)
                                      for tag in restaurant.food_categories]
    else:
        form.food_category.choices = [('', 'No food categories available')]
    if form.validate_on_submit():
        review = Review(rating=form.rating.data,
                        title=form.title.data,
                        content=form.content.data,
                        food_category=form.food_category.data
                        if form.food_category.data else None,
                        user_id=current_user.id,
                        restaurant_id=id)
        db.session.add(review)
        current_user.update_reputation()
        db.session.commit()
        flash('Your review has been posted!', 'success')
        return redirect(url_for('restaurant_detail', id=id))
    return render_template('add_review.html', form=form, restaurant=restaurant)


@app.route('/add-restaurant', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    if not FeatureToggle.get_feature_status('restaurants_enabled'):
        flash('Adding restaurants is currently disabled by administrators.',
              'warning')
        return redirect(url_for('restaurants'))
    form = RestaurantForm()
    form.cuisine_id.choices = [(c.id, c.name) for c in Cuisine.query.all()]
    food_categories = FoodCategory.query.order_by(FoodCategory.name).all()
    form.food_categories.choices = [(c.id, c.name) for c in food_categories]
    if form.validate_on_submit():
        selected_category_ids = [int(idx) for idx in form.food_categories.data]
        selected_categories = []
        for cat_id in selected_category_ids:
            category = FoodCategory.query.get(cat_id)
            if category:
                selected_categories.append(category.name)
        working_hours = {
            'monday': form.monday_hours.data,
            'tuesday': form.tuesday_hours.data,
            'wednesday': form.wednesday_hours.data,
            'thursday': form.thursday_hours.data,
            'friday': form.friday_hours.data,
            'saturday': form.saturday_hours.data,
            'sunday': form.sunday_hours.data,
        }
        image_url = None
        if form.restaurant_image.data:
            file = form.restaurant_image.data
            if file.filename:
                from PIL import Image
                from io import BytesIO
                import base64
                try:
                    img = Image.open(file)
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    img_io = BytesIO()
                    img.save(img_io, 'PNG')
                    img_io.seek(0)
                    image_data = base64.b64encode(
                        img_io.getvalue()).decode('utf-8')
                    image_url = f"data:image/png;base64,{image_data}"
                except Exception as e:
                    flash(
                        'Invalid image file. Please upload a valid PNG or JPG.',
                        'danger')
                    return redirect(url_for('add_restaurant'))
        import json
        restaurant = Restaurant(name=form.name.data,
                                description=form.description.data,
                                working_hours=json.dumps(working_hours),
                                price_range=form.price_range.data,
                                cuisine_id=form.cuisine_id.data,
                                user_id=current_user.id,
                                image_url=image_url,
                                is_small_business=False,
                                food_categories=selected_categories,
                                location_latitude=form.location_latitude.data,
                                location_longitude=form.location_longitude.data,
                                is_approved=current_user.is_admin)
        db.session.add(restaurant)
        db.session.commit()
        if current_user.is_admin:
            flash(
                "The restaurant submission is awaiting approval, but you're too special for approval.",
                'success')
        else:
            flash(
                'Restaurant submitted for review! An admin will approve it shortly.',
                'success')
        return redirect(url_for('restaurants'))
    return render_template('add_restaurant.html', form=form)


@app.route('/create-food-category', methods=['POST'])
@login_required
def create_food_category():
    data = request.get_json()
    category_name = data.get('name', '').strip()
    if not category_name or len(category_name) < 2 or len(category_name) > 50:
        return jsonify({
            'success':
            False,
            'error':
            'Category name must be between 2 and 50 characters'
        }), 400
    existing = FoodCategory.query.filter_by(name=category_name).first()
    if existing:
        return jsonify({
            'success': True,
            'id': existing.id,
            'name': existing.name
        })
    new_category = FoodCategory(name=category_name)
    db.session.add(new_category)
    db.session.commit()
    return jsonify({
        'success': True,
        'id': new_category.id,
        'name': new_category.name
    })


@app.route('/profile/<int:user_id>')
def profile(user_id):
    if not FeatureToggle.get_feature_status('profiles_enabled'):
        flash('User profiles are temporarily disabled.', 'warning')
        return redirect(url_for('index'))
    user = User.query.get_or_404(user_id)
    reviews = user.reviews.order_by(Review.created_at.desc()).all()
    is_own_profile = current_user.is_authenticated and current_user.id == user.id
    return render_template('profile.html',
                           user=user,
                           reviews=reviews,
                           is_own_profile=is_own_profile)


@app.route('/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_profile(user_id):
    user = User.query.get_or_404(user_id)
    if user.id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own profile.', 'danger')
        return redirect(url_for('profile', user_id=user_id))
    form = ProfileEditForm()
    if form.validate_on_submit():
        user.bio = form.bio.data
        if form.profile_picture.data:
            file = form.profile_picture.data
            if file.filename:
                from PIL import Image
                from io import BytesIO
                try:
                    img = Image.open(file)
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    img_io = BytesIO()
                    img.save(img_io, 'PNG')
                    img_io.seek(0)
                    user.profile_picture = img_io.getvalue()
                except Exception as e:
                    flash(
                        'Invalid image file. Please upload a valid PNG or JPG.',
                        'danger')
                    return redirect(
                        url_for('edit_profile', user_id=user.id))
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))
    if request.method == 'GET':
        form.bio.data = user.bio
    return render_template('edit_profile.html', user=user, form=form)


@app.route('/search')
def search():
    if not FeatureToggle.get_feature_status('search_enabled'):
        flash('Search is temporarily disabled.', 'warning')
        return redirect(url_for('restaurants'))
    query = request.args.get('q', '').strip()
    restaurants = []
    if query:
        name_matches = Restaurant.query.filter(
            Restaurant.is_approved == True,
            Restaurant.name.ilike(f'%{query}%')).all()
        restaurants.extend(name_matches)
        if not name_matches:
            from sqlalchemy import or_
            related = Restaurant.query.join(Cuisine).filter(
                Restaurant.is_approved == True,
                or_(Cuisine.name.ilike(f'%{query}%'),
                    Restaurant.description.ilike(f'%{query}%'))).all()
            restaurants.extend(related)
            if not related:
                restaurants = Restaurant.query.filter(
                    Restaurant.is_approved == True).order_by(
                        Restaurant.is_promoted.desc(),
                        Restaurant.created_at.desc()).limit(10).all()
    return render_template(
        'search_results.html',
        restaurants=restaurants,
        query=query,
        is_suggestion=bool(query and not any(query.lower() in r.name.lower()
                                             for r in restaurants)))


def get_admin_data():
    """Helper function to get all admin data"""
    pending_restaurants = Restaurant.query.filter_by(
        is_approved=False).order_by(Restaurant.created_at.desc()).all()
    approved_restaurants = Restaurant.query.filter_by(
        is_approved=True).order_by(Restaurant.created_at.desc()).all()
    all_users = User.query.all()
    all_reviews = Review.query.order_by(Review.created_at.desc()).all()
    all_cuisines = Cuisine.query.all()
    feature_toggles = FeatureToggle.query.all()
    toggle_dict = {
        t.feature_name: {
            'is_enabled': t.is_enabled,
            'description': t.description
        }
        for t in feature_toggles
    }
    default_toggles = {
        'restaurants_enabled': 'Allow users to add new restaurants',
        'reviews_enabled': 'Allow users to post reviews',
        'search_enabled': 'Enable restaurant search functionality',
        'leaderboard_enabled': 'Display leaderboard and top reviewers',
        'news_enabled': 'Allow news posts and viewing',
        'profiles_enabled': 'Allow user profile viewing',
        'photo_uploads_enabled': 'Allow photo uploads for restaurants',
        'restaurant_filtering_enabled': 'Enable cuisine and price filtering',
        'user_registration_enabled': 'Allow new users to sign up',
        'review_comments_enabled': 'Allow users to comment on reviews',
        'review_images_enabled': 'Allow image uploads in review posts',
        'badges_display_enabled': 'Display user badges on reviews and profiles',
        'dark_mode_enabled': 'Allow users to toggle dark mode',
        'review_approval_enabled': 'Require admin approval for reviews',
        'content_reporting_enabled': 'Allow users to report inappropriate content',
        'maintenance_mode': 'Put website in maintenance mode (shows message to non-admins)'
    }
    for feature_name, description in default_toggles.items():
        if feature_name not in toggle_dict:
            new_toggle = FeatureToggle(feature_name=feature_name,
                                       is_enabled=True,
                                       description=description)
            db.session.add(new_toggle)
            toggle_dict[feature_name] = {
                'is_enabled': True,
                'description': description
            }
    db.session.commit()
    return {
        'pending': pending_restaurants,
        'approved': approved_restaurants,
        'all_users': all_users,
        'all_reviews': all_reviews,
        'all_cuisines': all_cuisines,
        'total_users': len(all_users),
        'total_reviews': len(all_reviews),
        'feature_toggles': toggle_dict
    }


def seed_default_badges():
    """Seed default badges into the database if they don't exist"""
    from models import Badge

    default_badges = [
        {
            'name': 'Newcomer',
            'color': '#6c757d',
            'description': 'Just started exploring restaurants'
        },
        {
            'name': 'Food Explorer',
            'color': '#17a2b8',
            'description': 'Visited and reviewed multiple restaurants'
        },
        {
            'name': 'Rising Critic',
            'color': '#ffc107',
            'description': 'Active community member with helpful reviews'
        },
        {
            'name': 'Experienced Diner',
            'color': '#28a745',
            'description': 'Trusted reviewer with extensive experience'
        },
        {
            'name': 'Expert Reviewer',
            'color': '#007bff',
            'description': 'Highly influential food critic'
        },
        {
            'name': 'Elite Foodie',
            'color': '#e83e8c',
            'description': 'Community leader and food connoisseur'
        },
    ]

    for badge_data in default_badges:
        existing = Badge.query.filter_by(name=badge_data['name']).first()
        if not existing:
            new_badge = Badge(name=badge_data['name'],
                              color=badge_data['color'],
                              description=badge_data['description'])
            db.session.add(new_badge)

    db.session.commit()


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
    from models import Badge, UserBadge

    # Ensure default badges exist
    seed_default_badges()

    # Get admin data first
    data = get_admin_data()

    def format_restaurant(r):
        return {
            'id': r.id,
            'name': r.name,
            'cuisine': r.cuisine.name,
            'description': r.description[:100],
            'full_description': r.description,
            'working_hours': r.working_hours,
            'price_range': r.price_range,
            'is_small_business': r.is_small_business,
            'is_promoted': r.is_promoted,
            'is_approved': r.is_approved,
            'food_categories': r.food_categories if r.food_categories else [],
            'image_url': r.image_url,
            'review_count': r.review_count(),
            'avg_rating': r.avg_rating(),
            'created_at': r.created_at.strftime('%b %d, %Y'),
            'submitter_username':
            r.submitter.username if r.submitter else 'Unknown',
            'submitter_email': r.submitter.email if r.submitter else 'Unknown',
            'cuisine_id': r.cuisine_id
        }

    def format_user(u, include_badges=False):
        user_data = {
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
        if include_badges:
            user_badges = [{
                'id': ub.badge_id,
                'name': ub.badge.name,
                'color': ub.badge.color
            } for ub in u.custom_badges.all()]
            user_data['custom_badges'] = user_badges
        return user_data

    def format_review(r):
        return {
            'id': r.id,
            'author_id': r.user_id,
            'author_username':
            r.author.username if r.author else 'Deleted User',
            'restaurant_name': r.restaurant.name,
            'restaurant_id': r.restaurant.id,
            'rating': r.rating,
            'title': r.title,
            'content':
            r.content[:80] + '...' if len(r.content) > 80 else r.content,
            'created_at': r.created_at.strftime('%b %d, %Y')
        }

    def format_cuisine(c):
        return {'id': c.id, 'name': c.name}

    def format_badge(b):
        return {
            'id': b.id,
            'name': b.name,
            'color': b.color,
            'description': b.description,
            'hierarchy': b.hierarchy,
            'created_at': b.created_at.strftime('%b %d, %Y')
        }

    all_badges = Badge.query.all()

    return jsonify({
        'pending': [format_restaurant(r) for r in data['pending']],
        'approved': [format_restaurant(r) for r in data['approved']],
        'all_users':
        [format_user(u, include_badges=False) for u in data['all_users']],
        'all_reviews': [format_review(r) for r in data['all_reviews']],
        'all_cuisines': [format_cuisine(c) for c in data['all_cuisines']],
        'all_badges': [format_badge(b) for b in all_badges],
        'total_users':
        data['total_users'],
        'total_reviews':
        data['total_reviews'],
        'feature_toggles':
        data['feature_toggles']
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
    return redirect(url_for('admin_dashboard', tab='restaurants'))


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
    return redirect(url_for('admin_dashboard', tab='overview'))


@app.route('/admin/badge/<int:badge_id>/hierarchy', methods=['POST'])
@login_required
def update_badge_hierarchy(badge_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    from models import Badge
    badge = Badge.query.get_or_404(badge_id)
    hierarchy = request.form.get('hierarchy', '').strip()
    try:
        badge.hierarchy = int(hierarchy)
        db.session.commit()
        return jsonify({'success': True, 'hierarchy': badge.hierarchy})
    except ValueError:
        return jsonify({'error': 'Invalid hierarchy value'}), 400


@app.route('/leaderboard')
def leaderboard():
    if not FeatureToggle.get_feature_status('leaderboard_enabled'):
        flash('Leaderboard is temporarily disabled.', 'warning')
        return redirect(url_for('index'))
    from sqlalchemy import func
    all_users = (User.query.filter(
        User.is_admin == False, User.is_banned == False).join(Review).group_by(
            User.id).having(func.count(Review.id) > 0).all())
    all_users.sort(
        key=lambda u: u.reputation_score or u.calculate_reputation(),
        reverse=True)
    return render_template('leaderboard.html', users=all_users)


@app.route('/admin/toggle-promoted/<int:id>', methods=['POST'])
@login_required
def toggle_promoted(id):
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    restaurant = Restaurant.query.get_or_404(id)
    restaurant.is_promoted = not restaurant.is_promoted
    db.session.commit()
    status = 'promoted' if restaurant.is_promoted else 'unpromoted'
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
        Review.query.filter_by(user_id=id).update({'user_id': None})
        db.session.delete(user)
        flash(f'{username} has been deleted.', 'success')
    elif action == 'ban':
        ban_reason = request.form.get('ban_reason', '').strip()[:500]
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
        change_to_username = request.form.get('change_to_username', '').strip()
        new_password = request.form.get('new_password', '').strip()
        
        if new_username and new_username != user.username:
            existing = User.query.filter_by(username=new_username).first()
            if existing:
                flash('Username already taken.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
        if new_email and new_email != user.email:
            existing = User.query.filter_by(email=new_email).first()
            if existing:
                flash('Email already registered.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
        
        if new_username:
            user.username = new_username
        if new_email:
            user.email = new_email
        if change_to_username:
            if len(change_to_username) < 3 or len(change_to_username) > 64:
                flash('Username must be between 3-64 characters.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
            existing = User.query.filter_by(username=change_to_username).first()
            if existing:
                flash('New username already taken.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
            user.username = change_to_username
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'danger')
                return redirect(url_for('admin_dashboard', tab='users'))
            user.set_password(new_password)
        
        try:
            user.reputation_score = int(
                request.form.get('reputation_score', user.reputation_score))
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
    try:
        restaurant.name = request.form.get(
            'name', restaurant.name).strip()[:100] or restaurant.name
        restaurant.description = request.form.get(
            'description',
            restaurant.description).strip()[:1000] or restaurant.description
        restaurant.address = request.form.get(
            'address', restaurant.address).strip()[:300] or restaurant.address
        restaurant.phone = request.form.get(
            'phone', restaurant.phone).strip()[:50] or restaurant.phone
        restaurant.working_hours = request.form.get(
            'working_hours',
            restaurant.working_hours).strip()[:500] or restaurant.working_hours
        
        # Handle location coordinates
        try:
            lat = request.form.get('location_latitude', '').strip()
            lon = request.form.get('location_longitude', '').strip()
            if lat and lon:
                restaurant.location_latitude = float(lat)
                restaurant.location_longitude = float(lon)
        except (ValueError, TypeError):
            pass
        
        if 'restaurant_image' in request.files:
            file = request.files['restaurant_image']
            if file and file.filename:
                from PIL import Image
                from io import BytesIO
                import base64
                allowed_extensions = {'png', 'jpg', 'jpeg'}
                filename = file.filename.lower()
                if any(
                        filename.endswith('.' + ext)
                        for ext in allowed_extensions):
                    try:
                        img = Image.open(file)
                        img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                        img_io = BytesIO()
                        img.save(img_io, 'PNG')
                        img_io.seek(0)
                        image_data = base64.b64encode(
                            img_io.getvalue()).decode('utf-8')
                        restaurant.image_url = f"data:image/png;base64,{image_data}"
                    except Exception as e:
                        pass
        cuisine_id = int(request.form.get('cuisine_id', restaurant.cuisine_id))
        if not Cuisine.query.get(cuisine_id):
            flash('Invalid cuisine selected.', 'danger')
            return redirect(url_for('admin_dashboard', tab='restaurants'))
        restaurant.cuisine_id = cuisine_id
        price_range = int(
            request.form.get('price_range', restaurant.price_range))
        if price_range not in [1, 2, 3, 4]:
            price_range = restaurant.price_range
        restaurant.price_range = price_range
        restaurant.is_small_business = request.form.get(
            'is_small_business') == 'on'
        restaurant.is_approved = request.form.get('is_approved') == 'on'
        restaurant.is_promoted = request.form.get('is_promoted') == 'on'
        food_categories_input = request.form.get('food_categories', '').strip()
        restaurant.food_categories = [
            tag.strip() for tag in food_categories_input.split(',')
            if tag.strip()
        ] if food_categories_input else []
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
    if not item_type or item_type not in [
            'user', 'restaurant', 'review', 'cuisine'
    ]:
        flash('Invalid item type.', 'danger')
        tab_mapping = {
            'review': 'reviews',
            'cuisine': 'cuisines',
            'user': 'users',
            'restaurant': 'restaurants'
        }
        return redirect(
            url_for('admin_dashboard',
                    tab=tab_mapping.get(item_type, 'overview')))
    if item_type == 'user':
        for user_id in ids:
            Review.query.filter_by(user_id=int(user_id)).update(
                {'user_id': None})
            User.query.filter_by(id=int(user_id)).delete()
        flash(f'Deleted {len(ids)} user(s).', 'success')
    elif item_type == 'restaurant':
        Restaurant.query.filter(Restaurant.id.in_([int(id)
                                                   for id in ids])).delete()
        flash(f'Deleted {len(ids)} restaurant(s).', 'success')
    elif item_type == 'review':
        Review.query.filter(Review.id.in_([int(id) for id in ids])).delete()
        flash(f'Deleted {len(ids)} review(s).', 'success')
    elif item_type == 'cuisine':
        Cuisine.query.filter(Cuisine.id.in_([int(id) for id in ids])).delete()
        flash(f'Deleted {len(ids)} cuisine(s).', 'success')
    db.session.commit()
    tab_mapping = {
        'review': 'reviews',
        'cuisine': 'cuisines',
        'user': 'users',
        'restaurant': 'restaurants'
    }
    return redirect(
        url_for('admin_dashboard', tab=tab_mapping.get(item_type, 'overview')))


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


@app.route('/news')
def news():
    if not FeatureToggle.get_feature_status('news_enabled'):
        flash('News is temporarily disabled.', 'warning')
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    news_posts = News.query.order_by(News.created_at.desc()).paginate(
        page=page, per_page=10)
    return render_template('news.html', news_posts=news_posts)


@app.route('/news/<int:news_id>')
def news_detail(news_id):
    if not FeatureToggle.get_feature_status('news_enabled'):
        flash('News is temporarily disabled.', 'warning')
        return redirect(url_for('index'))
    news_post = News.query.get_or_404(news_id)
    related_posts = News.query.filter(News.user_id == news_post.user_id, News.id != news_post.id).order_by(News.created_at.desc()).limit(3).all()
    return render_template('news_detail.html', post=news_post, related_posts=related_posts)


@app.route('/post_news', methods=['GET', 'POST'])
@login_required
def post_news():
    if not FeatureToggle.get_feature_status('news_enabled'):
        flash('News posting is temporarily disabled.', 'warning')
        return redirect(url_for('news'))
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    form = NewsForm()
    if form.validate_on_submit():
        news_post = News(title=form.title.data,
                         content=form.content.data,
                         user_id=current_user.id)
        db.session.add(news_post)
        db.session.commit()
        flash('News posted successfully!', 'success')
        return redirect(url_for('news'))
    return render_template('post_news.html', form=form)


@app.route('/admin/change-password', methods=['POST'])
@login_required
def admin_change_password():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard', tab='settings'))
    form = AdminChangePasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user:
            flash('User not found.', 'danger')
        else:
            user.set_password(form.new_password.data)
            db.session.commit()
            flash(f'Password for {user.username} changed successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='settings'))


@app.route('/admin/change-username', methods=['POST'])
@login_required
def admin_change_username():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard', tab='settings'))
    form = AdminChangeUsernameForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.current_username.data).first()
        if not user:
            flash('User not found.', 'danger')
        else:
            user.username = form.new_username.data
            db.session.commit()
            flash(f'Username changed to {form.new_username.data} successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='settings'))


@app.route('/admin/toggle-feature/<feature_name>', methods=['POST'])
@login_required
def toggle_feature(feature_name):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    feature = FeatureToggle.query.filter_by(feature_name=feature_name).first()
    if not feature:
        feature = FeatureToggle(feature_name=feature_name, is_enabled=False)
        db.session.add(feature)
    else:
        feature.is_enabled = not feature.is_enabled
    db.session.commit()
    return jsonify({
        'success': True,
        'feature_name': feature_name,
        'is_enabled': feature.is_enabled
    })


@app.route('/admin/create-badge', methods=['POST'])
@login_required
def create_badge():
    from models import Badge
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    name = request.form.get('badge_name', '').strip()
    color = request.form.get('badge_color', '#007bff')
    description = request.form.get('badge_description', '').strip()
    if not name:
        flash('Please enter a badge name.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    if Badge.query.filter_by(name=name).first():
        flash(f'Badge "{name}" already exists.', 'warning')
        return redirect(url_for('admin_dashboard', tab='badges'))
    badge = Badge(name=name, color=color, description=description)
    db.session.add(badge)
    db.session.commit()
    flash(f'Badge "{name}" created successfully!', 'success')
    return redirect(url_for('admin_dashboard', tab='badges'))


@app.route('/admin/delete-badge/<int:id>', methods=['POST'])
@login_required
def delete_badge(id):
    from models import Badge
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    badge = Badge.query.get_or_404(id)
    name = badge.name
    db.session.delete(badge)
    db.session.commit()
    flash(f'Badge "{name}" deleted.', 'success')
    return redirect(url_for('admin_dashboard', tab='badges'))


@app.route('/admin/assign-badge/<int:user_id>/<int:badge_id>',
           methods=['POST'])
@login_required
def assign_badge(user_id, badge_id):
    from models import Badge, UserBadge
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get_or_404(user_id)
    badge = Badge.query.get_or_404(badge_id)
    if UserBadge.query.filter_by(user_id=user_id, badge_id=badge_id).first():
        return jsonify({'error': 'Badge already assigned'}), 400
    user_badge = UserBadge(user_id=user_id, badge_id=badge_id)
    db.session.add(user_badge)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'Badge assigned to {user.username}'
    })


@app.route('/admin/remove-badge/<int:user_id>/<int:badge_id>',
           methods=['POST'])
@login_required
def remove_badge(user_id, badge_id):
    from models import UserBadge
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    ub = UserBadge.query.filter_by(user_id=user_id,
                                   badge_id=badge_id).first_or_404()
    db.session.delete(ub)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Badge removed'})


@app.route('/admin/api/user-badges/<int:user_id>')
@login_required
def user_badges_api(user_id):
    from models import UserBadge
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    user = User.query.get_or_404(user_id)
    custom_badges = [{
        'id': ub.badge_id,
        'name': ub.badge.name,
        'color': ub.badge.color
    } for ub in user.custom_badges.all()]
    return jsonify({'custom_badges': custom_badges})


@app.route('/admin/edit-badge/<int:id>', methods=['POST'])
@login_required
def edit_badge(id):
    from models import Badge
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    badge = Badge.query.get_or_404(id)
    name = request.form.get('badge_name', '').strip()
    color = request.form.get('badge_color', '#007bff')
    description = request.form.get('badge_description', '').strip()
    if not name:
        flash('Badge name required.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    # Check for duplicate name (excluding current badge)
    if Badge.query.filter(Badge.name == name, Badge.id != id).first():
        flash('Badge name already exists.', 'danger')
        return redirect(url_for('admin_dashboard', tab='badges'))
    badge.name = name
    badge.color = color
    badge.description = description
    db.session.commit()
    flash('Badge updated.', 'success')
    return redirect(url_for('admin_dashboard', tab='badges'))


@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        'error.html',
        error_code=404,
        error_title='Page Not Found',
        error_message='The page you are looking for does not exist.',
        error_description=
        'The URL you tried to access was not found on this server. Please check the URL and try again.'
    ), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template(
        'error.html',
        error_code=500,
        error_title='Internal Server Error',
        error_message='Something went wrong on our end.',
        error_description=
        'An unexpected error occurred while processing your request. Our team has been notified. Please try again later.'
    ), 500


@app.errorhandler(403)
def forbidden_error(error):
    return render_template(
        'error.html',
        error_code=403,
        error_title='Access Forbidden',
        error_message='You do not have permission to access this resource.',
        error_description=
        'You do not have the necessary permissions to view this page. If you believe this is an error, please contact support.'
    ), 403


@app.errorhandler(400)
def bad_request_error(error):
    return render_template(
        'error.html',
        error_code=400,
        error_title='Bad Request',
        error_message='The request could not be understood by the server.',
        error_description=
        'The request you sent was malformed or invalid. Please check your input and try again.'
    ), 400
