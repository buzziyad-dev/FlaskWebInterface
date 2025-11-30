# Yalla - Restaurant Discovery Platform

## Overview

Yalla is a restaurant discovery and review platform for Jeddah, Saudi Arabia. It aims to help users find, review, and share information about local restaurants, supporting small food businesses and providing reliable, localized dining information. The platform features bilingual support (Arabic/English), restaurant listings with filtering, user-generated reviews and ratings, and community engagement features.

## User Preferences

- Preferred communication style: Simple, everyday language.
- **Database Policy**: Do NOT reset/reseed the database during development. Data persistence is critical. Only run seed_data.py if explicitly requested or during initial setup.
- **Admin Display Policy**: Admin users must be excluded from leaderboard and top community reviewers displays. Banned users must also be excluded.

## System Architecture

### Application Framework
- **Backend**: Flask (Python)
- **Architecture**: Monolithic MVC
- **Database**: SQL-based (configured via DATABASE_URL) with Flask-SQLAlchemy ORM
- **Authentication**: Flask-Login (session-based) with Werkzeug for password hashing
- **Frontend**: Jinja2 templates, Bootstrap 5, custom CSS
- **Responsive Design**: Mobile-first approach
- **Internationalization**: Custom JSON-based translation system (English/Arabic) with RTL support and language persistence (database for users, cookie for guests).
- **Form Handling**: Flask-WTF with WTForms for server-side validation and CSRF protection.

### Core Features
- **Restaurant Discovery**: Filter-based browsing (cuisine, price, rating) and text-based search.
- **Review System**: 1-5 star ratings with detailed content, user comments, and photo uploads (Base64 storage).
- **User Profiles**: Displays review history, badges, and reputation. Includes a follow/unfollow system.
- **Admin Dashboard**: Comprehensive dark mode styling, and feature toggle system to enable/disable core functionalities (e.g., adding restaurants, reviews, search, leaderboard, photo uploads, filtering).
- **Localization**: Full bilingual support (English/Arabic) for all UI elements, forms, and messages, including RTL layout adjustments.
- **Google Maps Integration**: "Open in Google Maps" link on restaurant detail pages.

### Design Principles
- **Data Integrity**: Relational model, cascade deletes, indexed fields, and server-side validation.
- **User Experience**: Mobile-first, clear navigation, consistent styling, and localized content.
- **Modularity**: Separation of concerns for models, views, and forms.

## External Dependencies

### Python Packages
- **Flask**: Web framework
- **Flask-SQLAlchemy**: ORM
- **Flask-Login**: Authentication
- **Flask-WTF**: Form handling
- **WTForms**: Form validation
- **Werkzeug**: Security utilities
- **Pillow**: Image processing

### Frontend Libraries
- **Bootstrap 5**: CSS framework
- **Google Fonts**: Inter and Cairo (via CDN)

### Environment Configuration
- **DATABASE_URL**: Database connection string
- **SESSION_SECRET**: Secret key for session security