from database import db
from datetime import date, datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer


class ApprenticeRecord(db.Model):
    __tablename__ = 'apprentice_records'

    id = db.Column(db.Integer, primary_key=True)
    ace360_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=True)
    gateway_submitted = db.Column(db.Date, nullable=True)
    approved_for_epa = db.Column(db.Date, nullable=True)
    project_start_date = db.Column(db.Date, nullable=True)
    project_deadline_date = db.Column(db.Date, nullable=True)
    first_attempt_date = db.Column(db.Date, nullable=True)
    second_attempt_date = db.Column(db.Date, nullable=True)
    overall_grade = db.Column(db.String(50), nullable=True)
    grade_date = db.Column(db.Date, nullable=True)

    @property
    def variance_days(self):
        """Calculate variance: first_attempt_date - project_deadline_date"""
        if self.first_attempt_date and self.project_deadline_date:
            return (self.first_attempt_date - self.project_deadline_date).days
        return None

    @property
    def epa_window_closure(self):
        """Calculate EPA Window Closure: EPA Ready date + 84 days (12 weeks)."""
        if self.approved_for_epa:
            closure_date = self.approved_for_epa + timedelta(days=84)
            return closure_date.strftime('%Y-%m-%d')
        return None

    @property
    def within_epa_window(self):
        """Check if grade_date is within 84 days (12 weeks) of approved_for_epa"""
        if self.grade_date and self.approved_for_epa:
            days_diff = (self.grade_date - self.approved_for_epa).days
            return "Yes" if days_diff <= 84 else "No"
        return None

    def __repr__(self):
        return f'<ApprenticeRecord {self.ace360_id}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # New fields for enhanced authentication
    forename = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    telephone = db.Column(db.String(20), nullable=True)
    user_created_date = db.Column(db.DateTime, nullable=False)
    date_last_logged_in = db.Column(db.DateTime, nullable=True)
    password_reset_requested_date = db.Column(db.DateTime, nullable=True)
    password_reset_completed_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    activation_token = db.Column(db.String(200), nullable=True)
    activation_token_expires = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(20), nullable=False, default='viewer')
    deleted_account_date = db.Column(db.DateTime, nullable=True)
    approval_status = db.Column(db.String(20), nullable=True, default='pending')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def generate_activation_token(self, serializer, salt='account-activation-salt'):
        """Generate an activation token for this user."""
        self.activation_token = serializer.dumps(self.email, salt=salt)
        self.activation_token_expires = datetime.now() + timedelta(hours=48)
        return self.activation_token

    def verify_activation_token(self, token, serializer, salt='account-activation-salt', max_age=172800):
        """Verify the activation token (default 48 hours = 172800 seconds)."""
        try:
            email = serializer.loads(token, salt=salt, max_age=max_age)
            return email == self.email
        except:
            return False

    def is_activation_expired(self):
        """Check if the activation token has expired."""
        if self.activation_token_expires:
            return datetime.now() > self.activation_token_expires
        return True

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'

    def is_viewer(self):
        """Check if user has viewer role."""
        return self.role == 'viewer'

    def is_deleted(self):
        """Check if user account has been deleted."""
        return self.deleted_account_date is not None

    def __repr__(self):
        return f'<User {self.forename} {self.surname}>'
