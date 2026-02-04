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

        # Create or update default admin user
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if admin is None:
            admin = User(
                username='admin',
                email='chris.oley@outlook.com',
                forename='Chris',
                surname='Oley',
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
        elif admin.email != 'chris.oley@outlook.com':
            admin.email = 'chris.oley@outlook.com'
            admin.forename = 'Chris'
            admin.surname = 'Oley'
            db.session.commit()
            print("Admin user email updated to chris.oley@outlook.com")
