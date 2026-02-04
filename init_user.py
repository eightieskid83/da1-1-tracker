#!/usr/bin/env python3
"""
Script to create the database tables and add a default admin user.
Run this once before starting the application for the first time.
"""

from app import app, db
from models import User
from datetime import datetime

def init_database():
    """Initialize the database with tables and create a default admin user."""
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created successfully.")

        # Check if any users exist
        if User.query.count() == 0:
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                forename='Admin',
                surname='User',
                job_title='Administrator',
                telephone=None,
                user_created_date=datetime.now(),
                is_active=True,
                role='admin',
                approval_status='approved'
            )
            admin.set_password('admin123')  # Change this password after first login

            db.session.add(admin)
            db.session.commit()

            print("\nDefault admin user created:")
            print("  Username: admin")
            print("  Password: admin123")
            print("\nIMPORTANT: Change this password after your first login!")
        else:
            print(f"\nUser table already contains {User.query.count()} user(s).")
            print("Skipping default user creation.")

if __name__ == '__main__':
    init_database()
