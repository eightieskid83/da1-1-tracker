# Quick Start Guide - DA1.1 Tracker Authentication

## 🚀 Getting Started (5 Minutes)

### Step 1: Install Dependencies
```bash
cd "/Users/chrisoley/Documents/Generative AI/Claude Code/DA1.1 Tracker"
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Initialize Database
```bash
python init_user.py
```

### Step 3: Start the Application
```bash
python app.py
```

### Step 4: Login
Open http://localhost:5000 in your browser

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

## 🎨 What You Get

✅ **Login Page** with Pearson colors (#0D004D and #FFCE00)
✅ **Password Reset** via email
✅ **Secure Authentication** with password hashing
✅ **Protected Routes** - all pages require login
✅ **Modern UI** - responsive and professional

## 📧 Email Configuration (Optional)

To enable password reset emails, edit `app.py` (lines 31-36):

```python
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
```

**Gmail Setup:**
1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Generate an app password for "Mail"
3. Use this password in the configuration above

## 👤 Create Additional Users

### Method 1: Quick Script

Create `add_user.py`:
```python
from app import app, db
from models import User

with app.app_context():
    user = User(username='john', email='john@example.com')
    user.set_password('secure_password')
    db.session.add(user)
    db.session.commit()
    print("User created!")
```

Run it:
```bash
python add_user.py
```

### Method 2: Python Shell

```bash
python
```
```python
from app import app, db
from models import User

with app.app_context():
    user = User(username='jane', email='jane@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
```

## 🎯 Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| Login Page | ✅ | Custom design with brand colors |
| User Authentication | ✅ | Secure password hashing |
| Session Management | ✅ | Flask-Login integration |
| Password Reset | ✅ | Email-based reset flow |
| Protected Routes | ✅ | All dashboard pages require login |
| Responsive Design | ✅ | Works on desktop, tablet, mobile |

## 🎨 Brand Colors Used

- **Pearson Purple (#0D004D):** Navbar, headings, primary elements
- **Pearson Yellow (#FFCE00):** Login button, call-to-action
- **Light Purple (#EDECF6):** Background
- **Secondary Purple (#512EAB):** Links, accents

## 📁 New Files

| File | Purpose |
|------|---------|
| `templates/login.html` | Login landing page |
| `templates/forgot_password.html` | Password reset request |
| `templates/reset_password.html` | Password reset form |
| `init_user.py` | Database initialization |
| `SETUP_GUIDE.md` | Detailed setup instructions |
| `LOGIN_DESIGN.md` | Design specifications |

## 🔒 Security Notes

- ✅ Passwords are hashed (never stored in plain text)
- ✅ Reset tokens expire after 1 hour
- ✅ All sensitive routes require authentication
- ⚠️ Change the default admin password immediately
- ⚠️ Change `app.secret_key` in production

## 🆘 Troubleshooting

**Can't log in?**
```bash
# Reset database
rm instance/da11_tracker.db
python init_user.py
```

**Import errors?**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Email not working?**
- Check MAIL_USERNAME and MAIL_PASSWORD in `app.py`
- For Gmail, use an App Password (not your regular password)
- Check spam folder

## 📚 Documentation

- **SETUP_GUIDE.md** - Complete setup instructions
- **LOGIN_DESIGN.md** - Design specs and colors
- **IMPLEMENTATION_SUMMARY.md** - What was built
- **README.md** - General application docs

## ✨ You're All Set!

The authentication system is ready to use. Start the app with `python app.py` and visit http://localhost:5000 to see your new login page!

**Need help?** Check the documentation files or inspect console output for errors.
