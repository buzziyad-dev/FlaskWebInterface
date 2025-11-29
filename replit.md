# Yalla - Restaurant Discovery Platform

## Overview

Yalla is a restaurant discovery and review platform focused on Jeddah, Saudi Arabia. The platform enables users to discover, review, and share information about local restaurants, with a particular emphasis on supporting small food businesses and providing reliable, localized dining information. The application features bilingual support (Arabic/English), restaurant listings with filtering capabilities, user-generated reviews and ratings, and community engagement features.

## User Preferences

- Preferred communication style: Simple, everyday language.
- **Database Policy**: Do NOT reset/reseed the database during development. Data persistence is critical. Only run seed_data.py if explicitly requested or during initial setup.
- **Admin Display Policy**: Admin users must be excluded from leaderboard and top community reviewers displays. Banned users must also be excluded.

## System Architecture

### Application Framework
- **Backend Framework**: Flask (Python web framework)
- **Architecture Pattern**: Monolithic MVC (Model-View-Controller)
- **Rationale**: Flask provides simplicity and flexibility for a medium-scale web application. The monolithic approach is appropriate for the initial scope (Jeddah-only) and team size, avoiding unnecessary complexity while maintaining development velocity.

### Data Layer
- **ORM**: Flask-SQLAlchemy with declarative base models
- **Database**: SQL-based (configured via DATABASE_URL environment variable)
- **Migration Strategy**: Simple `db.create_all()` approach for initial development
- **Key Design Decisions**:
  - Relational model chosen for structured data (users, restaurants, reviews, cuisines)
  - Cascade deletes implemented for review/user relationships to maintain referential integrity
  - Indexed fields on username/email for query performance
  - One-to-many relationships: User→Reviews, Restaurant→Reviews, Cuisine→Restaurants
  - FeatureToggle model for admin feature control

### Authentication & Authorization
- **System**: Flask-Login for session-based authentication
- **Password Security**: Werkzeug password hashing (generate_password_hash/check_password_hash)
- **Session Management**: Flask sessions with SECRET_KEY from environment
- **Design Rationale**: Session-based authentication chosen over JWT for simpler implementation and better fit for server-rendered templates. Login required decorator protects sensitive routes.

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask default) with Flask-Babel for i18n
- **CSS Framework**: Bootstrap 5
- **Custom Styling**: Additional CSS for brand-specific design
- **Typography**: Inter and Cairo fonts for bilingual support (Arabic/English)
- **Responsive Design**: Mobile-first approach using Bootstrap grid system
- **Localization**: Flask-Babel for Arabic/English translation with RTL support
- **Key Components**:
  - Base template with navigation and authentication state
  - Card-based layouts for restaurant listings
  - Form components with WTForms validation
  - Hero sections with overlay effects for visual impact
  - Language switcher (🌍) in navbar with dropdown menu

### Form Handling & Validation
- **Library**: Flask-WTF with WTForms
- **Validation Strategy**: Server-side validation with custom validators
- **CSRF Protection**: Enabled via Flask-WTF hidden tags
- **Custom Validators**: Username/email uniqueness checks in registration form
- **Design Rationale**: Server-side validation ensures data integrity regardless of client-side manipulation. Custom validators prevent duplicate accounts at the form level.

### Application Structure
- **Entry Point**: main.py runs the Flask development server
- **Configuration**: app.py initializes Flask app, database, and login manager
- **Models**: Single models.py file defines all database entities
- **Routes**: Single routes.py file contains all view logic
- **Forms**: Dedicated forms.py for form definitions and validators
- **Templates**: Organized by feature (base, index, restaurant views, auth views)
- **Static Assets**: CSS in static/css/

### Database Schema Design
**Core Entities**:
- **User**: Authentication and profile data, tracks review authorship, includes `language` field (en/ar)
- **Restaurant**: Business information (name, address, hours, price range, cuisine type)
- **Review**: User-generated content linking users to restaurants with ratings
- **Cuisine**: Category taxonomy for restaurant classification
- **FeatureToggle**: Admin feature control for temporarily disabling features

**Key Relationships**:
- User has many Reviews (one-to-many)
- Restaurant has many Reviews (one-to-many)

### Internationalization (i18n) & Localization (l10n)
- **Framework**: Custom JSON-based translation system (simple and lightweight)
- **Supported Languages**: English (en), Arabic (ar)
- **Translation Files**: 
  - `translations/en.json` - English translations
  - `translations/ar.json` - Arabic translations
  - Simple key-value JSON structure for easy editing
- **Language Persistence**:
  - Authenticated users: Stored in database (User.language field)
  - Guests: Persisted via cookie (1-year expiration)
  - Current page requests: Via g.locale variable
- **Translation Function**: Custom `translate()` function in app.py
  - No compilation step needed
  - Changes take effect immediately after restart
  - Easy to edit directly in JSON files
- **RTL Support**: CSS automatically applies `dir="rtl"` for Arabic with proper layout adjustments
- **UI**: Language switcher (🌍) in navbar with English/العربية options
- Cuisine has many Restaurants (one-to-many)
- Review belongs to User and Restaurant (many-to-one for both)

### Deployment Considerations
- **Proxy Configuration**: ProxyFix middleware handles reverse proxy headers
- **Connection Pooling**: SQLAlchemy configured with pool recycling and pre-ping
- **Environment Variables**: Sensitive configuration (DATABASE_URL, SESSION_SECRET) externalized
- **Production Readiness**: Debug mode controlled via main.py, separate from app initialization

### Feature Implementation Patterns
- **Restaurant Discovery**: Filter-based browsing with cuisine, price, and rating filters
- **Search Functionality**: Text-based search across restaurant names
- **Review System**: Star ratings (1-5) with title and detailed content
- **Small Business Highlighting**: Boolean flag with visual badges
- **Approval Workflow**: is_approved flag for content moderation (currently defaults to True)
- **Feature Toggles**: Admin controls to temporarily disable features (restaurants, reviews, search, leaderboard, news, profiles, photo uploads, filtering)
- **Photo Management**: Base64-encoded image storage with multi-photo support per restaurant

## Feature Toggles System

### Available Toggles
Admins can temporarily disable the following features via the Settings tab in the admin dashboard:
- **restaurants_enabled**: Allow users to add new restaurants
- **reviews_enabled**: Allow users to post reviews
- **search_enabled**: Enable restaurant search functionality
- **leaderboard_enabled**: Display leaderboard and top reviewers
- **news_enabled**: Allow news posts and viewing
- **profiles_enabled**: Allow user profile viewing
- **photo_uploads_enabled**: Allow photo uploads for restaurants
- **restaurant_filtering_enabled**: Enable cuisine and price filtering

### Implementation
- **Model**: FeatureToggle model stores feature state in database
- **Routes**: Each route checks feature status before allowing action
- **Admin UI**: Settings tab in admin dashboard with toggle buttons
- **User Feedback**: Clear flash messages when features are disabled

## External Dependencies

### Python Packages
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: ORM integration with database abstraction
- **Flask-Login**: User session management and authentication
- **Flask-WTF**: Form handling with CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: Password hashing utilities and WSGI middleware
- **Pillow**: Image processing for thumbnails

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive UI components
- **Google Fonts**: Inter and Cairo fonts for typography (via CDN)

### Environment Configuration
- **DATABASE_URL**: Database connection string (SQL database)
- **SESSION_SECRET**: Secret key for session encryption and security

## Recent Changes (Current Session)

### Complete Bilingual Translation System (Final)
- **160+ translations added** - All templates now fully translated to Arabic & English
- **Translation files**: `translations/en.json` (172 lines), `translations/ar.json` (172 lines)
- **Translated pages**:
  - ✅ Authentication (login, register, banned)
  - ✅ Restaurants (add, browse, detail, search)
  - ✅ Reviews & comments
  - ✅ User profiles & editing
  - ✅ Leaderboard & rankings
  - ✅ News posts & detail pages
  - ✅ Admin dashboard
  - ✅ Error pages & maintenance
- **Key strings translated**: All UI labels, buttons, placeholders, messages, titles, table headers
- **RTL support**: Automatic `dir="rtl"` for Arabic pages
- **Zero compilation**: Edit JSON files directly, restart app to see changes
- **171 template translation calls** - All hardcoded text now wrapped with `_()` function

## Previous Changes (Prior Session)

### Arabic Language Support Implementation (Revised)
- **Translation System**: Replaced Flask-Babel with simple JSON-based system
  - No compilation needed - edit `translations/en.json` and `translations/ar.json` directly
  - Changes take effect immediately after app restart
  - Much simpler than Babel's `.po` files
  - Custom `translate()` function in app.py handles all translations
- **Language Switcher**: Added to navbar as 🌍 dropdown
  - English/العربية options visible to all users
  - Route: `/set_language/<language>` handles language switching
- **Persistence Strategy**:
  - Authenticated users: Language preference saved to `User.language` database field
  - Non-authenticated users: Language preference saved to `language` cookie
  - Automatic detection via `get_locale()` function with priority: g.locale → User.language → cookie → default (en)
- **Arabic Translations**: 22+ key UI strings translated in JSON files
  - Covers: navigation, hero section, forms, buttons, messages, placeholders
  - Easy to add new translations - just add key-value pairs to JSON
- **RTL Support**: Comprehensive CSS changes for Arabic
  - HTML automatically sets `dir="rtl"` when Arabic is selected
  - Bootstrap components adapted for RTL layout
  - Text alignment, margins, floats properly flipped for Arabic
  - Search bar maintains LTR structure for proper UX
- **Database Migration**: Added `language` VARCHAR(10) column to `user` table with 'en' default

### Recent Changes (Previous Session)

### User Profile & Social Features
- **User Profiles**: Added comprehensive profile pages showing review history, badges, reputation
- **Follow System**: Users can follow/unfollow other reviewers to build social connections
  - Follower counts displayed on profiles
  - Many-to-many relationship via `user_follow` association table
  - `/follow/<user_id>` and `/unfollow/<user_id>` routes with AJAX support
- **Methods added to User model**: `follow()`, `unfollow()`, `is_following()`, `follower_count()`, `following_count()`

### Admin Dashboard Dark Mode
- Added comprehensive dark mode styling for admin dashboard
- All UI elements styled: modals, forms, tables, cards, buttons, badges, tabs
- Proper contrast and visibility in dark mode
- Covers all Bootstrap components and custom elements

### Review Comments System
- **ReviewComment Model**: New model linking comments to reviews and users
  - Supports nested discussions on individual reviews
  - Cascade delete when reviews are removed
  - Stores user_id, review_id, content, created_at
- **Comment Routes**: 
  - `/review/<review_id>/comment` (POST) - Add comment to review
  - `/comment/<comment_id>` (DELETE) - Remove comment (auth required)
- **Comment Display**:
  - Comments show under each review with author, timestamp (KSA time), content
  - Comment count displayed next to each review
  - Authenticated users can add inline comments via simple form
- **Comment Form**: `ReviewCommentForm` with validation (2-500 chars)
- **UI**: Comments appear in left-indented section below review content

### Photo Upload System
- Fixed SQLAlchemy JSON mutation tracking using `flag_modified()` for multiple photo uploads
- Users can now upload multiple photos per restaurant
- Photos stored as base64 in database with metadata (uploader, timestamp, mime type)

### Feature Toggle System
- Added comprehensive admin controls to temporarily disable website features
- 8 feature toggles covering all major user-facing functionality
- Settings tab in admin dashboard with real-time toggle UI
- Feature checks integrated into all relevant routes
- Clear user feedback when features are disabled

### Data Quality Improvements
- Fixed top community reviewers to exclude banned users
- Fixed leaderboard to exclude banned users
- Both now only show users with at least 1 review
- Proper database queries using joins and group_by

### Bug Fixes
- Fixed photo upload mutation tracking
- Fixed CSRF token handling for AJAX feature toggle requests
- Fixed user display logic in leaderboards
