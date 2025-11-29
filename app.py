import os
import base64
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()
babel = Babel()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB max file size
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_DEFAULT_TIMEZONE"] = "UTC"

db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
babel.init_app(app)
login_manager.login_view = 'login'

@babel.localeselector
def get_locale():
    from flask import request, g
    from flask_login import current_user
    # Check if locale is stored in g (set by set_language route)
    if hasattr(g, 'locale'):
        return g.locale
    # Check user preference if authenticated
    if current_user.is_authenticated:
        return current_user.language or 'en'
    # Check cookie
    locale = request.cookies.get('language', 'en')
    return locale if locale in ['en', 'ar'] else 'en'

@app.template_filter('b64encode')
def b64encode_filter(data):
    if data:
        return base64.b64encode(data).decode('utf-8')
    return ''

@app.after_request
def add_cache_control(response):
    if response.content_type and 'text/css' in response.content_type:
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.headers['Pragma'] = 'no-cache'
    return response

with app.app_context():
    import models
    import routes
    db.create_all()
