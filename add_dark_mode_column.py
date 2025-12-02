#!/usr/bin/env python3
"""
Database migration script to add missing dark_mode column to user table
"""

from app import app, db
from sqlalchemy import text

def add_dark_mode_column():
    """Add dark_mode column to user table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'dark_mode'
            """))
            
            if result.fetchone() is None:
                print("Adding dark_mode column to user table...")
                db.session.execute(text("""
                    ALTER TABLE "user" 
                    ADD COLUMN dark_mode BOOLEAN DEFAULT FALSE
                """))
                db.session.commit()
                print("✓ dark_mode column added successfully")
            else:
                print("✓ dark_mode column already exists")
                
        except Exception as e:
            print(f"Error adding dark_mode column: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    add_dark_mode_column()