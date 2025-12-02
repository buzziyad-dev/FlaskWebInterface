import os
import base64
import json
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB max file size

# Load translations
TRANSLATIONS = {}
for lang in ['en', 'ar']:
    try:
        with open(f'translations/{lang}.json', 'r', encoding='utf-8') as f:
            TRANSLATIONS[lang] = json.load(f)
    except:
        TRANSLATIONS[lang] = {}

def get_locale():
    """Get current locale from g, user preference, cookie, or default"""
    # Check if locale is stored in g (set by set_language route)
    if hasattr(g, 'locale'):
        return g.locale
    # Check user preference if authenticated
    if current_user.is_authenticated:
        return current_user.language or 'en'
    # Check cookie
    locale = request.cookies.get('language', 'en')
    return locale if locale in ['en', 'ar'] else 'en'

def translate(text):
    """Translate text to current locale"""
    locale = get_locale()
    if locale in TRANSLATIONS and text in TRANSLATIONS[locale]:
        return TRANSLATIONS[locale][text]
    return text

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
login_manager.login_view = 'login'

# Make helpers available to templates
app.jinja_env.globals.update(get_locale=get_locale, _=translate)

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

@app.after_request
def add_cache_control(response):
    # Add proper caching headers for static files
    if response.content_type:
        if 'text/css' in response.content_type:
            # Cache CSS for 1 hour with ETag validation
            response.cache_control.max_age = 3600
            response.cache_control.public = True
            response.cache_control.must_revalidate = True
            response.headers['ETag'] = f'"{hash(response.data)}"'
        elif 'application/javascript' in response.content_type:
            # Cache JS for 1 hour
            response.cache_control.max_age = 3600
            response.cache_control.public = True
        elif 'image/' in response.content_type:
            # Cache images for 1 day
            response.cache_control.max_age = 86400
            response.cache_control.public = True
        elif 'text/html' not in response.content_type:
            # Cache other static assets for 30 minutes
            response.cache_control.max_age = 1800
            response.cache_control.public = True
    return response

with app.app_context():
    import models
    import routes
    db.create_all()
