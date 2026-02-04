#!/usr/bin/env python3
from app import app, db
from sqlalchemy import text

def migrate_add_deleted_date():
    """Add deleted_account_date column to users table."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'deleted_account_date' not in columns:
            print("Adding 'deleted_account_date' column...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN deleted_account_date DATETIME"))
                conn.commit()
            print("Column added successfully.")
        else:
            print("'deleted_account_date' column already exists.")

        print("Migration completed!")

if __name__ == '__main__':
    migrate_add_deleted_date()
