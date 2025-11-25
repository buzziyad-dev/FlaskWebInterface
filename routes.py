from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, db, login_manager
from models import User, Restaurant, Review, Cuisine
from forms import RegistrationForm, LoginForm, ReviewForm, RestaurantForm

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    featured_restaurants = Restaurant.query.filter_by(is_approved=True).order_by(Restaurant.created_at.desc()).limit(6).all()
    cuisines = Cuisine.query.all()
    top_reviewers = User.query.all()
    top_reviewers.sort(key=lambda u: u.review_count(), reverse=True)
    top_reviewers = top_reviewers[:4]
    return render_template('index.html', restaurants=featured_restaurants, cuisines=cuisines, top_reviewers=top_reviewers)

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
    return render_template('restaurant_detail.html', restaurant=restaurant, reviews=reviews)

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
            is_approved=True
        )
        db.session.add(restaurant)
        db.session.commit()
        flash('Restaurant added successfully!', 'success')
        return redirect(url_for('restaurant_detail', id=restaurant.id))
    
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
