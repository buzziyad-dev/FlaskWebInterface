from app import app, db
from models import User, Cuisine, Restaurant, Review

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        print("Creating cuisines...")
        cuisines = [
            Cuisine(name='Saudi'),
            Cuisine(name='Italian'),
            Cuisine(name='Mexican'),
            Cuisine(name='Asian'),
            Cuisine(name='American'),
            Cuisine(name='Mediterranean'),
            Cuisine(name='Indian'),
            Cuisine(name='Lebanese'),
            Cuisine(name='Turkish'),
            Cuisine(name='Fast Food')
        ]
        for cuisine in cuisines:
            db.session.add(cuisine)
        db.session.commit()
        print(f"Created {len(cuisines)} cuisines")
        
        print("Creating users...")
        users = []
        
        admin = User(username='admin', email='admin@yalla.com', is_admin=True)
        admin.set_password('admin123')
        users.append(admin)
        
        user1 = User(username='ahmed_jeddah', email='ahmed@example.com')
        user1.set_password('password123')
        users.append(user1)
        
        user2 = User(username='sara_foodie', email='sara@example.com')
        user2.set_password('password123')
        users.append(user2)
        
        user3 = User(username='khalid_reviews', email='khalid@example.com')
        user3.set_password('password123')
        users.append(user3)
        
        user4 = User(username='fatima_eats', email='fatima@example.com')
        user4.set_password('password123')
        users.append(user4)
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        print(f"Created {len(users)} users")
        
        print("Creating restaurants...")
        restaurants = [
            Restaurant(
                name='Al Baik',
                description='Famous Saudi fast food chain known for delicious fried chicken and garlic sauce. A must-try for anyone visiting Jeddah!',
                address='Al Hamra District, Jeddah',
                phone='+966 12 234 5678',
                working_hours='11:00 AM - 2:00 AM',
                price_range=1,
                cuisine_id=1,
                image_url='https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=800',
                is_small_business=False,
                is_approved=True
            ),
            Restaurant(
                name='Mama Noura',
                description='Traditional Saudi restaurant serving authentic dishes in a family-friendly atmosphere. Known for kabsa and mandi.',
                address='Tahlia Street, Jeddah',
                phone='+966 12 345 6789',
                working_hours='12:00 PM - 12:00 AM',
                price_range=2,
                cuisine_id=1,
                image_url='https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800',
                is_small_business=False,
                is_approved=True
            ),
            Restaurant(
                name='Bella Napoli',
                description='Authentic Italian pizzeria with wood-fired oven. Fresh ingredients and traditional recipes from Naples.',
                address='Corniche Road, Jeddah',
                phone='+966 12 456 7890',
                working_hours='1:00 PM - 11:00 PM',
                price_range=3,
                cuisine_id=2,
                image_url='https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800',
                is_small_business=True,
                is_approved=True
            ),
            Restaurant(
                name='Tacos Locos',
                description='Vibrant Mexican restaurant bringing authentic flavors to Jeddah. Great tacos, burritos, and margaritas!',
                address='Red Sea Mall, Jeddah',
                phone='+966 12 567 8901',
                working_hours='2:00 PM - 12:00 AM',
                price_range=2,
                cuisine_id=3,
                image_url='https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=800',
                is_small_business=True,
                is_approved=True
            ),
            Restaurant(
                name='Sushi Garden',
                description='Premium Japanese restaurant with skilled sushi chefs. Fresh fish and elegant presentation.',
                address='Al Andalus District, Jeddah',
                phone='+966 12 678 9012',
                working_hours='12:00 PM - 11:00 PM',
                price_range=4,
                cuisine_id=4,
                image_url='https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=800',
                is_small_business=False,
                is_approved=True
            ),
            Restaurant(
                name='The Burger Hub',
                description='Gourmet burger joint with creative combinations. Great atmosphere and friendly service.',
                address='Palestine Street, Jeddah',
                phone='+966 12 789 0123',
                working_hours='11:00 AM - 1:00 AM',
                price_range=2,
                cuisine_id=5,
                image_url='https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800',
                is_small_business=True,
                is_approved=True
            ),
            Restaurant(
                name='Mediterranean Breeze',
                description='Fresh Mediterranean cuisine with a modern twist. Great seafood and mezze selection.',
                address='Obhur Corniche, Jeddah',
                phone='+966 12 890 1234',
                working_hours='1:00 PM - 12:00 AM',
                price_range=3,
                cuisine_id=6,
                image_url='https://images.unsplash.com/photo-1544025162-d76694265947?w=800',
                is_small_business=False,
                is_approved=True
            ),
            Restaurant(
                name='Spice Palace',
                description='Authentic Indian restaurant with rich flavors and aromatic spices. Best biryani in town!',
                address='Al Rawdah District, Jeddah',
                phone='+966 12 901 2345',
                working_hours='12:00 PM - 11:30 PM',
                price_range=2,
                cuisine_id=7,
                image_url='https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800',
                is_small_business=True,
                is_approved=True
            ),
            Restaurant(
                name='Cedar House',
                description='Lebanese restaurant offering traditional mezze, grills, and fresh salads in a cozy setting.',
                address='King Fahd Road, Jeddah',
                phone='+966 12 012 3456',
                working_hours='11:00 AM - 12:00 AM',
                price_range=2,
                cuisine_id=8,
                image_url='https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800',
                is_small_business=True,
                is_approved=True
            ),
            Restaurant(
                name='Istanbul Grill',
                description='Turkish restaurant with authentic kebabs, pide, and baklava. Warm hospitality guaranteed.',
                address='Al Zahra District, Jeddah',
                phone='+966 12 123 4567',
                working_hours='12:00 PM - 1:00 AM',
                price_range=2,
                cuisine_id=9,
                image_url='https://images.unsplash.com/photo-1529006557810-274b9b2fc783?w=800',
                is_small_business=False,
                is_approved=True
            )
        ]
        
        for restaurant in restaurants:
            db.session.add(restaurant)
        db.session.commit()
        print(f"Created {len(restaurants)} restaurants")
        
        print("Creating reviews...")
        reviews = [
            Review(rating=5, title='Amazing chicken!', content='Best fried chicken I have ever had. The garlic sauce is incredible and the prices are very reasonable. Highly recommend!', user_id=1, restaurant_id=1, is_approved=True),
            Review(rating=4, title='Great value', content='Tasty food at affordable prices. Sometimes crowded but worth the wait.', user_id=2, restaurant_id=1, is_approved=True),
            Review(rating=5, title='Authentic Saudi cuisine', content='The kabsa here is outstanding. Generous portions and authentic flavors. Perfect for family gatherings.', user_id=1, restaurant_id=2, is_approved=True),
            Review(rating=4, title='Traditional and delicious', content='Great mandi and excellent service. The atmosphere is very family-friendly.', user_id=3, restaurant_id=2, is_approved=True),
            Review(rating=5, title='Best pizza in Jeddah', content='Authentic Italian pizza with fresh ingredients. The margherita is perfection!', user_id=2, restaurant_id=3, is_approved=True),
            Review(rating=5, title='Hidden gem', content='Small place but amazing quality. The owner is very friendly and the pizza is delicious.', user_id=4, restaurant_id=3, is_approved=True),
            Review(rating=4, title='Great tacos', content='Authentic Mexican flavors. The fish tacos are my favorite!', user_id=1, restaurant_id=4, is_approved=True),
            Review(rating=5, title='Love it!', content='Best Mexican food in Jeddah. The atmosphere is fun and the food is amazing.', user_id=3, restaurant_id=4, is_approved=True),
            Review(rating=5, title='Fresh and delicious', content='High-quality sushi with excellent presentation. A bit pricey but worth it for special occasions.', user_id=2, restaurant_id=5, is_approved=True),
            Review(rating=4, title='Premium experience', content='Great sushi selection and professional staff. The omakase is highly recommended.', user_id=4, restaurant_id=5, is_approved=True),
            Review(rating=5, title='Amazing burgers', content='Creative burger combinations and great quality beef. The truffle fries are a must-try!', user_id=1, restaurant_id=6, is_approved=True),
            Review(rating=4, title='Good spot', content='Tasty burgers in a casual setting. Good value for money.', user_id=2, restaurant_id=6, is_approved=True),
            Review(rating=5, title='Fresh seafood', content='Beautiful location on the corniche with delicious Mediterranean food. The grilled fish is excellent.', user_id=3, restaurant_id=7, is_approved=True),
            Review(rating=5, title='Best biryani ever', content='The chicken biryani here is unmatched. Rich flavors and perfect spice level.', user_id=1, restaurant_id=8, is_approved=True),
            Review(rating=4, title='Great Lebanese food', content='Authentic mezze and excellent grilled meats. Very friendly staff.', user_id=4, restaurant_id=9, is_approved=True),
            Review(rating=5, title='Love the kebabs', content='Authentic Turkish kebabs and wonderful baklava for dessert. Highly recommend!', user_id=2, restaurant_id=10, is_approved=True)
        ]
        
        for review in reviews:
            db.session.add(review)
        db.session.commit()
        print(f"Created {len(reviews)} reviews")
        
        print("\nDatabase seeded successfully!")
        print("\nTest users:")
        print(f"  Admin: admin@yalla.com / admin123")
        print("\nRegular users (all with password 'password123'):")
        for user in users[1:]:
            print(f"  - {user.email}")

if __name__ == '__main__':
    seed_database()
