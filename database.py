import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the Flask app."""
    # Use DATABASE_URL from environment (Render provides this for PostgreSQL)
    # Fall back to SQLite for local development
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///da11_tracker.db')

    # Render uses postgres:// but SQLAlchemy requires postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Create default admin user if no users exist
        from models import User
        if User.query.count() == 0:
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
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (admin/admin123)")
