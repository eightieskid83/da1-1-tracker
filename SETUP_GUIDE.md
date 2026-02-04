# DA1.1 Tracker - Setup Guide

## Authentication System Overview

The DA1.1 Tracker now includes a complete authentication system with the following features:

- **Secure Login Page** - Custom-designed landing page with Pearson brand colors (#0D004D and #FFCE00)
- **User Authentication** - Session-based authentication using Flask-Login
- **Password Security** - Passwords are securely hashed using Werkzeug
- **Password Reset** - Users can request password reset links via email
- **Protected Routes** - All dashboard and record management pages require authentication

## Brand Colors

The login page and authentication system use the Pearson brand colors:
- **Primary Color (Pearson Purple):** #0D004D - Used for headings, navbar, and primary text
- **Accent Color (Pearson Yellow):** #FFCE00 - Used for login button and call-to-action elements
- **Background:** #EDECF6 - Light purple background
- **Secondary Purple:** #512EAB - Used for links and secondary elements

## Quick Start

### 1. Install Dependencies

```bash
cd "/Users/chrisoley/Documents/Generative AI/Claude Code/DA1.1 Tracker"
source venv/bin/activate
pip install -r requirements.txt
```

The new dependencies include:
- `Flask-Login` - User session management
- `Flask-Mail` - Email functionality for password reset
- `itsdangerous` - Secure token generation

### 2. Configure Email (Optional)

If you want to enable password reset functionality, edit `app.py` (lines 31-36):

```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
```

**For Gmail Users:**
1. Enable 2-Factor Authentication on your Google account
2. Go to Google Account → Security → App Passwords
3. Generate an app password for "Mail"
4. Use this 16-character password (not your regular Gmail password)

**Note:** If you skip email configuration, users won't be able to reset passwords via email, but the login system will still work.

### 3. Initialize Database

Run the initialization script to create database tables and the default admin user:

```bash
python init_user.py
```

Output:
```
Database tables created successfully.

Default admin user created:
  Username: admin
  Password: admin123

IMPORTANT: Change this password after your first login!
```

### 4. Start the Application

```bash
python app.py
```

The application will start on http://localhost:5000

### 5. First Login

1. Open your browser to http://localhost:5000
2. You'll be automatically redirected to the login page
3. Enter the default credentials:
   - **Username:** admin
   - **Password:** admin123
4. Click "Login"

**SECURITY NOTE:** You should create a new user with a secure password and delete or change the admin account password immediately.

## Creating Additional Users

Currently, new users must be created programmatically. Here's how to create additional users:

### Method 1: Python Script

Create a file called `create_user.py`:

```python
from app import app, db
from models import User

def create_user(username, email, password):
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print(f"Error: Username '{username}' already exists.")
            return

        if User.query.filter_by(email=email).first():
            print(f"Error: Email '{email}' already exists.")
            return

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        print(f"User '{username}' created successfully!")

if __name__ == '__main__':
    # Change these values
    create_user('newuser', 'user@example.com', 'securepassword123')
```

Run it:
```bash
python create_user.py
```

### Method 2: Python Interactive Shell

```bash
python
```

```python
from app import app, db
from models import User

with app.app_context():
    user = User(username='john.smith', email='john.smith@example.com')
    user.set_password('YourSecurePassword123')
    db.session.add(user)
    db.session.commit()
    print("User created!")
```

## Using the Password Reset Feature

### For Users:

1. Click "Forgot your password?" on the login page
2. Enter your email address
3. Check your email for the reset link
4. Click the link (valid for 1 hour)
5. Enter your new password twice
6. Log in with your new password

### For Administrators:

If email is not configured, you can manually reset passwords using Python:

```python
from app import app, db
from models import User

with app.app_context():
    user = User.query.filter_by(username='username').first()
    if user:
        user.set_password('newpassword')
        db.session.commit()
        print("Password updated!")
```

## Security Best Practices

1. **Change Default Password:** Immediately change or delete the default admin account
2. **Secure Secret Key:** In production, change `app.secret_key` in `app.py` to a random, secure value
3. **HTTPS:** Use HTTPS in production to protect login credentials
4. **Strong Passwords:** Enforce minimum password requirements (current minimum: 8 characters)
5. **Email Configuration:** Keep email credentials secure and use app passwords, not account passwords
6. **Regular Backups:** Backup the `da11_tracker.db` file regularly

## Troubleshooting

### Can't Log In

- Verify the username and password are correct
- Check if the database was initialized properly
- Run `python init_user.py` again if needed

### Password Reset Not Working

- Verify email configuration in `app.py`
- Check email credentials are correct
- For Gmail, ensure you're using an app password, not your regular password
- Check spam folder for reset emails

### Database Errors

- Delete the `da11_tracker.db` file
- Run `python init_user.py` again
- This will create a fresh database

### Import Errors

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Activate the virtual environment: `source venv/bin/activate`

## File Structure

```
DA1.1 Tracker/
├── app.py                      # Main Flask application
│                               # - Authentication routes (lines 50-145)
│                               # - Email configuration (lines 31-36)
│                               # - Protected routes with @login_required
│
├── models.py                   # Database models
│                               # - User model with password hashing
│                               # - ApprenticeRecord model
│
├── init_user.py                # Database initialization script
│
├── templates/
│   ├── login.html              # Login page (#0D004D, #FFCE00)
│   ├── forgot_password.html    # Password reset request page
│   ├── reset_password.html     # Password reset form
│   └── base.html               # Base template with logout button
│
└── instance/
    └── da11_tracker.db         # SQLite database (auto-created)
```

## Next Steps

After setting up authentication, you can:

1. Create additional user accounts for your team
2. Start adding apprentice records via the dashboard
3. Use the bulk import feature to upload existing records
4. Customize the email templates for password reset
5. Add user management features (admin panel to create/edit users)

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the main README.md file
- Inspect the console output for error messages
