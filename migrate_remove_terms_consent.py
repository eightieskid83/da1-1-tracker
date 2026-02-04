#!/usr/bin/env python3
"""
Migration script to remove the terms_consent_date column from the users table.
Run once manually: python migrate_remove_terms_consent.py
"""

from app import app, db
from sqlalchemy import text

def migrate_remove_terms_consent():
    """Drop terms_consent_date column from users table."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'terms_consent_date' not in columns:
            print("'terms_consent_date' column does not exist. Nothing to do.")
            print("Migration completed!")
            return

        print("Removing 'terms_consent_date' column...")

        # SQLite requires a table rebuild to drop a column
        remaining_columns = [col for col in columns if col != 'terms_consent_date']
        cols_str = ', '.join(remaining_columns)

        with db.engine.connect() as conn:
            conn.execute(text(
                f"CREATE TABLE users_new AS SELECT {cols_str} FROM users"
            ))
            conn.execute(text("DROP TABLE users"))
            conn.execute(text("ALTER TABLE users_new RENAME TO users"))
            conn.commit()

        print("Column removed successfully.")
        print("Migration completed!")

if __name__ == '__main__':
    migrate_remove_terms_consent()
