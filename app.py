import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from database import db, init_db
from models import ApprenticeRecord, User
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import csv
import io
import pandas as pd
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from functools import wraps

def admin_required(f):
    """Decorator to restrict route access to admin users only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin():
            flash('You do not have permission to access this page. Admin access required.', 'danger')
            return redirect(url_for('records'))
        return f(*args, **kwargs)
    return decorated_function

# Status options for dropdown
STATUS_OPTIONS = [
    'In Training',
    'Gateway in Progress',
    'Gateway Evidence Complete',
    'Gateway Submitted',
    'Denied EPA',
    'Approved for EPA',
    'EPA in Progress',
    'EPA Evidence Complete',
    'EPA Failed',
    'EPA Passed'
]

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'da11-tracker-secret-key-change-in-production')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME', ''))

# Initialize extensions
init_db(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Token serializer for password reset
serializer = URLSafeTimedSerializer(app.secret_key)


@app.context_processor
def utility_processor():
    def get_pending_registration_count():
        return User.query.filter_by(approval_status='pending').count()
    return dict(get_pending_registration_count=get_pending_registration_count)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Check if account is deleted
            if user.is_deleted():
                flash('This account has been deleted. Please contact administrator if this is an error.', 'danger')
                return render_template('login.html')

            if not user.is_active:
                flash('Account not activated. Please check your email or use "Forgot password" to reactivate.', 'danger')
                return render_template('login.html')

            # Update last login timestamp
            user.date_last_logged_in = datetime.now()
            db.session.commit()

            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password request."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            # Set password reset requested timestamp
            user.password_reset_requested_date = datetime.now()
            db.session.commit()

            # Generate password reset token
            token = serializer.dumps(user.email, salt='password-reset-salt')

            # Create reset link
            reset_url = url_for('reset_password', token=token, _external=True)

            # Send email
            msg = Message(
                'Password Reset Request - DA1.1 Tracker',
                recipients=[user.email]
            )
            msg.body = f'''Hello {user.forename},

You have requested to reset your password for DA1.1 Tracker.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not make this request, please ignore this email.

Best regards,
DA1.1 Tracker Team
'''
            try:
                mail.send(msg)
                flash('A password reset link has been sent to your email address.', 'success')
            except Exception as e:
                flash('Error sending email. Please contact the administrator.', 'danger')
                print(f"Email error: {e}")
        else:
            # Don't reveal whether the email exists or not
            flash('If that email address is in our system, you will receive a password reset link.', 'info')

        return redirect(url_for('login'))

    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        # Verify token (valid for 1 hour)
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except SignatureExpired:
        flash('The password reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('forgot_password'))
    except BadSignature:
        flash('Invalid password reset link.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html', token=token)

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('reset_password.html', token=token)

        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            user.password_reset_completed_date = datetime.now()
            # Reactivate account if it was disabled
            user.is_active = True
            db.session.commit()
            flash('Your password has been reset successfully. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        forename = request.form.get('forename', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        job_title = request.form.get('job_title', '').strip()
        telephone = request.form.get('telephone', '').strip()

        if not all([forename, surname, email, job_title]):
            return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

        # Check email uniqueness (exclude current user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'success': False, 'message': 'Email address already in use.'}), 400

        current_user.forename = forename
        current_user.surname = surname
        current_user.email = email
        current_user.job_title = job_title
        current_user.telephone = telephone if telephone else None

        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully!'}), 200

    except Exception as e:
        print(f"Profile update error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500


@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (soft delete)."""
    try:
        user = current_user
        user.deleted_account_date = datetime.now()
        db.session.commit()

        # Send confirmation email
        msg = Message(
            'Account Deletion Confirmation - DA1.1 Tracker',
            recipients=[user.email]
        )
        msg.body = f'''Hello {user.forename},

Your DA1.1 Tracker account has been successfully deleted.

Account Details:
- Name: {user.forename} {user.surname}
- Email: {user.email}
- Deletion Date: {user.deleted_account_date.strftime('%d/%m/%Y %H:%M')}

If you did not request this deletion, please contact your administrator immediately.

Best regards,
DA1.1 Tracker Team
'''
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Email error: {e}")

        logout_user()
        return jsonify({'success': True, 'message': 'Account deleted successfully.'}), 200

    except Exception as e:
        print(f"Account deletion error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500


@app.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        # Get form data
        forename = request.form.get('forename', '').strip()
        surname = request.form.get('surname', '').strip()
        email = request.form.get('email', '').strip()
        job_title = request.form.get('job_title', '').strip()
        telephone = request.form.get('telephone', '').strip()
        password = request.form.get('password', '')

        # Validate required fields
        if not all([forename, surname, email, job_title, password]):
            return jsonify({'success': False, 'message': 'All required fields must be filled.'}), 400

        # Check email uniqueness
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email address already registered.'}), 400

        # Validate password strength (server-side)
        import re
        password_pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$'
        if not re.match(password_pattern, password):
            return jsonify({'success': False, 'message': 'Password does not meet security requirements.'}), 400

        # Create username from email (before @)
        username = email.split('@')[0]
        # Ensure username uniqueness
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        # Create new user
        new_user = User(
            username=username,
            email=email,
            forename=forename,
            surname=surname,
            job_title=job_title,
            telephone=telephone if telephone else None,
            user_created_date=datetime.now(),
            is_active=False,
            role='viewer',
            approval_status='pending'
        )
        new_user.set_password(password)

        # Generate activation token (stored for admin approve route to use later)
        new_user.generate_activation_token(serializer)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Registration successful! Your account is pending admin approval. You will receive an email once your request has been reviewed.'}), 200

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during registration. Please try again.'}), 500


@app.route('/admin/notifications')
@login_required
@admin_required
def get_notifications():
    """Return pending registration requests as JSON."""
    pending_users = User.query.filter_by(approval_status='pending').order_by(User.user_created_date.desc()).all()
    notifications = [
        {
            'id': u.id,
            'forename': u.forename,
            'surname': u.surname,
            'email': u.email,
            'registered_date': u.user_created_date.strftime('%d/%m/%Y %H:%M')
        }
        for u in pending_users
    ]
    return jsonify(notifications)


@app.route('/admin/notifications/approve/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def approve_registration(user_id):
    """Approve a pending registration and send activation email."""
    user = User.query.get_or_404(user_id)

    if user.approval_status != 'pending':
        return jsonify({'success': False, 'message': 'Already processed.'}), 400

    user.approval_status = 'approved'

    # Regenerate token if expired so the activation link is valid
    if user.is_activation_expired():
        user.generate_activation_token(serializer)

    db.session.commit()

    # Send activation email
    activation_url = url_for('activate_account', token=user.activation_token, _external=True)
    msg = Message('Activate Your DA1.1 Tracker Account', recipients=[user.email])
    msg.html = render_template('emails/activation.html', forename=user.forename, activation_url=activation_url)
    msg.body = render_template('emails/activation.txt', forename=user.forename, activation_url=activation_url)
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

    return jsonify({'success': True, 'message': 'Approved. Activation email sent.'}), 200


@app.route('/admin/notifications/reject/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reject_registration(user_id):
    """Reject a pending registration and send rejection email."""
    user = User.query.get_or_404(user_id)

    if user.approval_status != 'pending':
        return jsonify({'success': False, 'message': 'Already processed.'}), 400

    user.approval_status = 'rejected'
    db.session.commit()

    # Send rejection email
    msg = Message('DA1.1 Tracker \u2014 Registration Request', recipients=[user.email])
    msg.html = render_template('emails/rejection.html', forename=user.forename)
    msg.body = render_template('emails/rejection.txt', forename=user.forename)
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Email error: {e}")

    return jsonify({'success': True, 'message': 'Rejected. Notification sent.'}), 200


@app.route('/activate/<token>')
def activate_account(token):
    """Handle account activation from email link."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        # Verify token (48 hours = 172800 seconds)
        email = serializer.loads(token, salt='account-activation-salt', max_age=172800)
    except SignatureExpired:
        return render_template('activation_expired.html')
    except BadSignature:
        flash('Invalid activation link.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))

    if user.is_active:
        flash('Account already activated. Please log in.', 'info')
        return redirect(url_for('login'))

    # Activate account
    user.is_active = True
    user.activation_token = None
    user.activation_token_expires = None
    db.session.commit()

    return render_template('activation_success.html')


def count_business_days(start_date, end_date):
    """Count business days (excluding weekends) between two dates."""
    if not start_date or not end_date:
        return None
    if end_date < start_date:
        return 0
    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            count += 1
        current += timedelta(days=1)
    return count


def parse_date(date_string):
    """Parse date string to date object, return None if empty or invalid."""
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


@app.route('/')
@login_required
def index():
    """Display dashboard with metrics."""
    records = ApprenticeRecord.query.all()

    total_learners = len(records)

    # Grade distribution
    graded_records = [r for r in records if r.overall_grade]
    total_graded = len(graded_records)

    if total_graded > 0:
        distinction_count = sum(1 for r in graded_records if r.overall_grade == 'Distinction')
        merit_count = sum(1 for r in graded_records if r.overall_grade == 'Merit')
        pass_count = sum(1 for r in graded_records if r.overall_grade == 'Pass')
        fail_count = sum(1 for r in graded_records if r.overall_grade == 'Fail')

        grade_dist = {
            'distinction': round(distinction_count / total_graded * 100, 1),
            'merit': round(merit_count / total_graded * 100, 1),
            'pass': round(pass_count / total_graded * 100, 1),
            'fail': round(fail_count / total_graded * 100, 1)
        }

        # Overall pass rate (Distinction + Merit + Pass)
        passed = distinction_count + merit_count + pass_count
        pass_rate = round(passed / total_graded * 100, 1)
    else:
        grade_dist = {'distinction': 0, 'merit': 0, 'pass': 0, 'fail': 0}
        pass_rate = 0

    # Within 12-week window percentage
    records_with_window = [r for r in records if r.within_epa_window is not None]
    if records_with_window:
        within_window = sum(1 for r in records_with_window if r.within_epa_window == 'Yes')
        within_window_pct = round(within_window / len(records_with_window) * 100, 1)
    else:
        within_window_pct = 0

    # First attempts booked within 12-week EPA window
    records_with_first_attempt = [r for r in records if r.first_attempt_date and r.approved_for_epa]
    if records_with_first_attempt:
        first_in_window = sum(1 for r in records_with_first_attempt
                             if (r.first_attempt_date - r.approved_for_epa).days <= 84)
        first_attempt_in_window_pct = round(first_in_window / len(records_with_first_attempt) * 100, 1)
    else:
        first_attempt_in_window_pct = 0

    # Average days to complete for those within 12 weeks (as percentage of 84-day window)
    within_window_records = [r for r in records if r.within_epa_window == 'Yes'
                            and r.grade_date and r.approved_for_epa]
    if within_window_records:
        total_days = sum((r.grade_date - r.approved_for_epa).days for r in within_window_records)
        avg_days = total_days / len(within_window_records)
        avg_days_within_window = round(avg_days / 84 * 100, 1)
    else:
        avg_days_within_window = 0

    # Beyond 12-week window percentage
    beyond_window_pct = round(100 - within_window_pct, 1)

    # Gateway approval within 5 working days
    records_with_gateway = [r for r in records if r.gateway_submitted and r.approved_for_epa]
    if records_with_gateway:
        approved_within_5_days = sum(
            1 for r in records_with_gateway
            if count_business_days(r.gateway_submitted, r.approved_for_epa) <= 5
        )
        gateway_approval_pct = round(approved_within_5_days / len(records_with_gateway) * 100, 1)
    else:
        gateway_approval_pct = 0

    metrics = {
        'total_learners': total_learners,
        'grade_dist': grade_dist,
        'pass_rate': pass_rate,
        'within_window_pct': within_window_pct,
        'beyond_window_pct': beyond_window_pct,
        'first_attempt_in_window_pct': first_attempt_in_window_pct,
        'avg_days_within_window': avg_days_within_window,
        'gateway_approval_pct': gateway_approval_pct
    }

    return render_template('dashboard.html', metrics=metrics)


@app.route('/records')
@login_required
def records():
    """Display all apprentice records with filtering and pagination support."""
    query = ApprenticeRecord.query

    # Collect all active filters for template
    active_filters = {}

    # Status filter
    status_filter = request.args.get('status')
    if status_filter:
        query = query.filter(ApprenticeRecord.status == status_filter)
        active_filters['status'] = status_filter

    # Grade filter
    grade_filter = request.args.get('grade')
    if grade_filter:
        query = query.filter(ApprenticeRecord.overall_grade == grade_filter)
        active_filters['grade'] = grade_filter

    # Within EPA Window filter (handled in Python since it's a computed property)
    window_filter = request.args.get('window')
    if window_filter:
        active_filters['window'] = window_filter

    # Date range filters
    date_filters = [
        ('gateway', 'gateway_submitted'),
        ('approved', 'approved_for_epa'),
        ('project_start', 'project_start_date'),
        ('deadline', 'project_deadline_date'),
        ('first_attempt', 'first_attempt_date'),
        ('second_attempt', 'second_attempt_date'),
        ('grade_date', 'grade_date'),
    ]

    for filter_prefix, model_field in date_filters:
        from_date = request.args.get(f'{filter_prefix}_from')
        to_date = request.args.get(f'{filter_prefix}_to')

        if from_date:
            parsed_from = parse_date(from_date)
            if parsed_from:
                query = query.filter(getattr(ApprenticeRecord, model_field) >= parsed_from)
                active_filters[f'{filter_prefix}_from'] = from_date

        if to_date:
            parsed_to = parse_date(to_date)
            if parsed_to:
                query = query.filter(getattr(ApprenticeRecord, model_field) <= parsed_to)
                active_filters[f'{filter_prefix}_to'] = to_date

    # Get page number from query params
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # Apply window filter requires fetching all and filtering in Python
    if window_filter:
        all_records = query.order_by(ApprenticeRecord.id.desc()).all()
        filtered_records = [r for r in all_records if r.within_epa_window == window_filter]
        total = len(filtered_records)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        records_list = filtered_records[start_idx:end_idx]
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None
        }
    else:
        pagination_obj = query.order_by(ApprenticeRecord.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        records_list = pagination_obj.items
        pagination = {
            'page': pagination_obj.page,
            'per_page': per_page,
            'total': pagination_obj.total,
            'pages': pagination_obj.pages,
            'has_prev': pagination_obj.has_prev,
            'has_next': pagination_obj.has_next,
            'prev_num': pagination_obj.prev_num,
            'next_num': pagination_obj.next_num
        }

    return render_template('index.html', records=records_list, active_filters=active_filters, pagination=pagination)


@app.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_record():
    """Add a new apprentice record."""
    if request.method == 'POST':
        record = ApprenticeRecord(
            ace360_id=int(request.form['ace360_id']),
            status=request.form.get('status') or None,
            gateway_submitted=parse_date(request.form.get('gateway_submitted')),
            approved_for_epa=parse_date(request.form.get('approved_for_epa')),
            project_start_date=parse_date(request.form.get('project_start_date')),
            project_deadline_date=parse_date(request.form.get('project_deadline_date')),
            first_attempt_date=parse_date(request.form.get('first_attempt_date')),
            second_attempt_date=parse_date(request.form.get('second_attempt_date')),
            overall_grade=request.form.get('overall_grade') or None,
            grade_date=parse_date(request.form.get('grade_date'))
        )
        db.session.add(record)
        db.session.commit()
        flash('Record added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('form.html', record=None, action='Add', status_options=STATUS_OPTIONS)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_record(id):
    """Edit an existing apprentice record."""
    record = ApprenticeRecord.query.get_or_404(id)

    if request.method == 'POST':
        record.ace360_id = int(request.form['ace360_id'])
        record.status = request.form.get('status') or None
        record.gateway_submitted = parse_date(request.form.get('gateway_submitted'))
        record.approved_for_epa = parse_date(request.form.get('approved_for_epa'))
        record.project_start_date = parse_date(request.form.get('project_start_date'))
        record.project_deadline_date = parse_date(request.form.get('project_deadline_date'))
        record.first_attempt_date = parse_date(request.form.get('first_attempt_date'))
        record.second_attempt_date = parse_date(request.form.get('second_attempt_date'))
        record.overall_grade = request.form.get('overall_grade') or None
        record.grade_date = parse_date(request.form.get('grade_date'))

        db.session.commit()
        flash('Record updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('form.html', record=record, action='Edit', status_options=STATUS_OPTIONS)


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_record(id):
    """Delete an apprentice record."""
    record = ApprenticeRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Record deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/view/<int:id>')
@login_required
def view_record(id):
    """View a single apprentice record with all details."""
    record = ApprenticeRecord.query.get_or_404(id)
    return render_template('view.html', record=record)


def get_export_data():
    """Get all records formatted for export."""
    records = ApprenticeRecord.query.order_by(ApprenticeRecord.id.desc()).all()
    headers = ['ACE360 ID', 'Status', 'Gateway Submitted', 'EPA Ready Date', 'Project Start Date',
               'Project Deadline', 'First Attempt', 'Second Attempt', 'Variance (Days)',
               'Overall Grade', 'Grade Date', 'Within EPA Window']
    rows = []
    for r in records:
        rows.append([
            r.ace360_id,
            r.status if r.status else '',
            str(r.gateway_submitted) if r.gateway_submitted else '',
            str(r.approved_for_epa) if r.approved_for_epa else '',
            str(r.project_start_date) if r.project_start_date else '',
            str(r.project_deadline_date) if r.project_deadline_date else '',
            str(r.first_attempt_date) if r.first_attempt_date else '',
            str(r.second_attempt_date) if r.second_attempt_date else '',
            r.variance_days if r.variance_days is not None else '',
            r.overall_grade if r.overall_grade else '',
            str(r.grade_date) if r.grade_date else '',
            r.within_epa_window if r.within_epa_window else ''
        ])
    return headers, rows


@app.route('/export/csv')
@login_required
def export_csv():
    """Export all records as CSV."""
    headers, rows = get_export_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=apprentice_records.csv'}
    )


@app.route('/export/xlsx')
@login_required
def export_xlsx():
    """Export all records as Excel file."""
    headers, rows = get_export_data()
    wb = Workbook()
    ws = wb.active
    ws.title = 'Apprentice Records'
    ws.append(headers)
    for row in rows:
        ws.append(row)
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=apprentice_records.xlsx'}
    )


@app.route('/export/pdf')
@login_required
def export_pdf():
    """Export all records as PDF."""
    headers, rows = get_export_data()
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph('Apprentice Records: Data Analyst', styles['Title']))
    table_data = [headers] + rows
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#512eab')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=apprentice_records.pdf'}
    )


@app.route('/upload', methods=['POST'])
@login_required
@admin_required
def upload_records():
    """Upload records from CSV or XLSX file."""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('records'))

    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('records'))

    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        flash('Invalid file type. Please upload a CSV or XLSX file.', 'error')
        return redirect(url_for('records'))

    try:
        # Read file into pandas DataFrame
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Column mapping from upload file to database fields
        column_mapping = {
            'ACE360 ID': 'ace360_id',
            'Status': 'status',
            'Gateway Submitted Date': 'gateway_submitted',
            'EPA Ready Date': 'approved_for_epa',
            'Project Start Date': 'project_start_date',
            'Project Deadline': 'project_deadline_date',
            'First Attempt Booking Date': 'first_attempt_date',
            'Second Attempt Booking Date': 'second_attempt_date',
            'Overall Grade': 'overall_grade',
            'Grade Date': 'grade_date'
        }

        imported = 0
        skipped = 0

        for _, row in df.iterrows():
            # Get ACE360 ID from row
            ace360_id = None
            if 'ACE360 ID' in df.columns:
                ace360_id = row.get('ACE360 ID')

            if pd.isna(ace360_id):
                skipped += 1
                continue

            ace360_id = int(ace360_id)

            # Check if record already exists
            existing = ApprenticeRecord.query.filter_by(ace360_id=ace360_id).first()
            if existing:
                skipped += 1
                continue

            # Create new record
            record = ApprenticeRecord(ace360_id=ace360_id)

            # Map fields from upload
            if 'Status' in df.columns and not pd.isna(row.get('Status')):
                record.status = str(row.get('Status'))

            if 'Gateway Submitted Date' in df.columns and not pd.isna(row.get('Gateway Submitted Date')):
                val = row.get('Gateway Submitted Date')
                record.gateway_submitted = pd.to_datetime(val).date() if val else None

            if 'EPA Ready Date' in df.columns and not pd.isna(row.get('EPA Ready Date')):
                val = row.get('EPA Ready Date')
                record.approved_for_epa = pd.to_datetime(val).date() if val else None

            if 'Project Start Date' in df.columns and not pd.isna(row.get('Project Start Date')):
                val = row.get('Project Start Date')
                record.project_start_date = pd.to_datetime(val).date() if val else None

            if 'Project Deadline' in df.columns and not pd.isna(row.get('Project Deadline')):
                val = row.get('Project Deadline')
                record.project_deadline_date = pd.to_datetime(val).date() if val else None

            if 'First Attempt Booking Date' in df.columns and not pd.isna(row.get('First Attempt Booking Date')):
                val = row.get('First Attempt Booking Date')
                record.first_attempt_date = pd.to_datetime(val).date() if val else None

            if 'Second Attempt Booking Date' in df.columns and not pd.isna(row.get('Second Attempt Booking Date')):
                val = row.get('Second Attempt Booking Date')
                record.second_attempt_date = pd.to_datetime(val).date() if val else None

            if 'Overall Grade' in df.columns and not pd.isna(row.get('Overall Grade')):
                record.overall_grade = str(row.get('Overall Grade'))

            if 'Grade Date' in df.columns and not pd.isna(row.get('Grade Date')):
                val = row.get('Grade Date')
                record.grade_date = pd.to_datetime(val).date() if val else None

            db.session.add(record)
            imported += 1

        db.session.commit()
        flash(f'Import complete: {imported} records imported, {skipped} skipped (existing or invalid).', 'success')

    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')

    return redirect(url_for('records'))


if __name__ == '__main__':
    app.run(debug=True)
