#!/usr/bin/env python3
"""
Migration script to add role column to User table and set default roles.
Run this script after updating models.py to add the role field.
"""

from app import app, db
from models import User
from sqlalchemy import text

def migrate_add_roles():
    """Add role column and set default roles for existing users."""
    with app.app_context():
        # Check if role column already exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'role' not in columns:
            print("Adding 'role' column to users table...")
            # Add the role column using raw SQL (SQLite doesn't support ADD COLUMN with DEFAULT for existing rows)
            with db.engine.connect() as conn:
                # Add column without default first
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20)"))
                conn.commit()
            print("Column added successfully.")
        else:
            print("'role' column already exists.")

        # Get all users and update their roles
        users = User.query.all()

        if not users:
            print("\nNo users found in the database.")
            return

        # Update roles for existing users
        updated_count = 0
        for user in users:
            # Check if role is already set
            if user.role:
                print(f"{user.username}: role already set to '{user.role}'")
                continue

            # Set admin role for user named 'admin', viewer for all others
            if user.username.lower() == 'admin':
                user.role = 'admin'
                print(f"{user.username}: set to 'admin' role")
            else:
                user.role = 'viewer'
                print(f"{user.username}: set to 'viewer' role")
            updated_count += 1

        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            print(f"\nUpdated {updated_count} user(s).")
        else:
            print("\nNo users needed updating.")

        print("\nMigration completed successfully!")

        # Display summary
        admin_count = User.query.filter_by(role='admin').count()
        viewer_count = User.query.filter_by(role='viewer').count()
        print(f"\nRole Summary:")
        print(f"  Admin users: {admin_count}")
        print(f"  Viewer users: {viewer_count}")

if __name__ == '__main__':
    migrate_add_roles()
