# AGENTS.md - Development Guidelines for FlaskWebInterface

## Build/Lint/Test Commands
- **Development server**: `python main.py` (runs on port 5000)
- **Production server**: `gunicorn --bind 0.0.0.0:5000 main:app`
- **Database seeding**: `python seed_data.py`
- **No formal testing setup** - add pytest if implementing tests
- **No linting configuration** - add flake8/black for code formatting

## Code Style Guidelines

### Import Organization
```python
# Standard library imports first
import os
import json
from datetime import datetime

# Third-party imports second  
from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy

# Local imports third
from app import app, db
from models import User, Restaurant
```

### Formatting & Naming
- **Indentation**: 4 spaces
- **Line length**: Under 100 characters
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase` 
- **Constants**: `UPPER_SNAKE_CASE`

### Error Handling
- Use flash messages for user feedback: `flash('Error message', 'danger')`
- Database operations: wrap in try-catch with `db.session.rollback()`
- File validation: check MIME types and size before processing
- Authentication: use `@login_required` decorator

### Flask Patterns
- Use `g` for request-scoped data
- Database queries via SQLAlchemy ORM
- Forms with Flask-WTF and CSRF protection
- Environment variables for sensitive config
- Multi-language support via JSON translation files

### Architecture Notes
- Modular design: separate models, routes, forms files
- No blueprints - single routes.py file
- Reputation system in separate module
- Feature toggles for functionality control