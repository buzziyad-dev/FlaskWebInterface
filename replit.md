# Yalla - Restaurant Discovery Platform

## Overview

Yalla is a restaurant discovery and review platform focused on Jeddah, Saudi Arabia. The platform enables users to discover, review, and share information about local restaurants, with a particular emphasis on supporting small food businesses and providing reliable, localized dining information. The application features bilingual support (Arabic/English), restaurant listings with filtering capabilities, user-generated reviews and ratings, and community engagement features.

## User Preferences

- Preferred communication style: Simple, everyday language.
- **Database Policy**: Do NOT reset/reseed the database during development. Data persistence is critical. Only run seed_data.py if explicitly requested or during initial setup.

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

### Authentication & Authorization
- **System**: Flask-Login for session-based authentication
- **Password Security**: Werkzeug password hashing (generate_password_hash/check_password_hash)
- **Session Management**: Flask sessions with SECRET_KEY from environment
- **Design Rationale**: Session-based authentication chosen over JWT for simpler implementation and better fit for server-rendered templates. Login required decorator protects sensitive routes.

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask default)
- **CSS Framework**: Bootstrap 5
- **Custom Styling**: Additional CSS for brand-specific design
- **Typography**: Inter and Cairo fonts for bilingual support (Arabic/English)
- **Responsive Design**: Mobile-first approach using Bootstrap grid system
- **Key Components**:
  - Base template with navigation and authentication state
  - Card-based layouts for restaurant listings
  - Form components with WTForms validation
  - Hero sections with overlay effects for visual impact

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
- **User**: Authentication and profile data, tracks review authorship
- **Restaurant**: Business information (name, address, hours, price range, cuisine type)
- **Review**: User-generated content linking users to restaurants with ratings
- **Cuisine**: Category taxonomy for restaurant classification

**Key Relationships**:
- User has many Reviews (one-to-many)
- Restaurant has many Reviews (one-to-many)
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

## External Dependencies

### Python Packages
- **Flask**: Web application framework
- **Flask-SQLAlchemy**: ORM integration with database abstraction
- **Flask-Login**: User session management and authentication
- **Flask-WTF**: Form handling with CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: Password hashing utilities and WSGI middleware

### Frontend Libraries
- **Bootstrap 5**: CSS framework for responsive UI components
- **Google Fonts**: Inter and Cairo fonts for typography (via CDN)

### Environment Configuration
- **DATABASE_URL**: Database connection string (SQL database)
- **SESSION_SECRET**: Secret key for session encryption and security

### Future Integration Considerations
Based on design guidelines, the platform plans to integrate:
- Map services for location display
- Image hosting for restaurant photos
- Potential business collaboration features
- Leaderboard systems for top reviewers
- Food pickup/ordering functionality (long-term)