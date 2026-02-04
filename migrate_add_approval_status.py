#!/usr/bin/env python3
from app import app, db
from sqlalchemy import text

def migrate_add_approval_status():
    """Add approval_status column to users table and backfill existing rows."""
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]

        if 'approval_status' not in columns:
            print("Adding 'approval_status' column...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN approval_status VARCHAR(20)"))
                conn.commit()
            print("Column added successfully.")
        else:
            print("'approval_status' column already exists.")

        # Backfill all existing users so the badge starts at zero
        print("Backfilling existing users to 'approved'...")
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE users SET approval_status = 'approved' WHERE approval_status IS NULL"))
            conn.commit()
        print("Backfill completed.")

        print("Migration completed!")

if __name__ == '__main__':
    migrate_add_approval_status()
