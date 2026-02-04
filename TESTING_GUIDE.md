# Testing Guide - Enhanced Authentication System

## Quick Start

### 1. Configure Email (Required for Testing)

Edit `app.py` lines 35-40:

```python
app.config['MAIL_USERNAME'] = 'your-gmail@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'  # Use App Password, not regular password
app.config['MAIL_DEFAULT_SENDER'] = 'your-gmail@gmail.com'
```

**To create a Gmail App Password:**
1. Go to Google Account Settings
2. Security → 2-Step Verification
3. App passwords → Generate new password
4. Copy the 16-character password to `MAIL_PASSWORD`

### 2. Start the Application

```bash
source venv/bin/activate
python app.py
```

Open browser to: http://localhost:5000/login

### 3. Test Admin Login (Baseline)

**Credentials:**
- Username: `admin`
- Password: `admin123`

**Expected:** Successful login, redirects to dashboard

## Test Plan

### Test 1: Login Page UI Changes

**Steps:**
1. Navigate to http://localhost:5000/login
2. Verify "Sign in to access your dashboard" subtitle is REMOVED
3. Verify "Forgot your password?" link is REPLACED with "Need help?" button
4. Click "Need help?"
5. Verify collapsible menu appears with two options:
   - "Forgotten password?"
   - "Don't have an account? Sign up"

**Expected Result:** ✅ UI matches new design

---

### Test 2: Password Reset Modal

**Steps:**
1. Click "Need help?" → "Forgotten password?"
2. Verify modal opens (does NOT navigate to new page)
3. Modal should have:
   - Dark purple header (#0D004D) with "Reset Password"
   - Email field with purple label (#512eab)
   - Yellow OK/Cancel buttons (#FFCE00)
4. Enter: `admin@example.com`
5. Click "Send Reset Link"
6. Check email inbox for reset link

**Expected Result:** ✅ Reset email received, modal shows success message

---

### Test 3: Registration Flow (Basic)

**Steps:**
1. Click "Need help?" → "Don't have an account? Sign up"
2. Verify registration modal opens with fields:
   - Forename, Surname, Email, Job Title, Telephone (optional), Password
   - Dark purple header (#0D004D)
   - Purple field labels (#512eab)
   - Yellow OK/Cancel buttons

3. Fill form:
   - Forename: `John`
   - Surname: `Doe`
   - Email: `john.doe@example.com`
   - Job Title: `Test User`
   - Telephone: (leave blank)
   - Password: `Test1234!`

4. Watch password requirements change from red to green as you type
5. Click OK
6. Verify terms modal appears
7. Check the "I agree" checkbox
8. Click OK

**Expected Result:** ✅ Success message appears, activation email sent

---

### Test 4: Password Validation

**Test weak passwords in registration modal:**

| Password | Should Show Error |
|----------|-------------------|
| `test` | ❌ Too short |
| `testtest` | ❌ No uppercase |
| `TestTest` | ❌ No number |
| `Test1234` | ❌ No special char |
| `Test1234!` | ✅ Valid |

**Expected Result:** ✅ Real-time validation shows red/green indicators

---

### Test 5: Account Activation

**Steps:**
1. Check email inbox for activation email
2. Click activation link
3. Verify redirect to "Account Activated!" page
4. Click "Go to Login"
5. Log in with:
   - Username: `john.doe` (from email)
   - Password: `Test1234!`

**Expected Result:** ✅ Login successful, redirects to dashboard

**Database Check:**
```bash
source venv/bin/activate
python -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(email='john.doe@example.com').first()
    print(f'Is Active: {user.is_active}')
    print(f'Activation Token: {user.activation_token}')
"
```
Should show: `is_active=True`, `activation_token=None`

---

### Test 6: Login Timestamp

**Steps:**
1. Log out
2. Log in as admin
3. Check database:

```bash
python -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print(f'Last Login: {user.date_last_logged_in}')
"
```

**Expected Result:** ✅ Timestamp updated to current time

---

### Test 7: Inactive Account Login

**Steps:**
1. Register a new account (e.g., `jane@example.com`)
2. DO NOT click activation link
3. Try to log in with username `jane`
4. Verify error message: "Account not activated. Please check your email or use 'Forgot password' to reactivate."

**Expected Result:** ✅ Login blocked, appropriate message shown

---

### Test 8: Activation Link Expiration

**Manual database test:**

```bash
python -c "
from app import app, db
from models import User
from datetime import datetime, timedelta

with app.app_context():
    # Find unactivated user
    user = User.query.filter_by(is_active=False).first()
    if user:
        # Set expiration to past
        user.activation_token_expires = datetime.now() - timedelta(hours=49)
        db.session.commit()
        print(f'Set expiration to past for: {user.email}')
        print(f'Token: {user.activation_token}')
    else:
        print('No inactive users found. Register a new account first.')
"
```

**Steps:**
1. Click the expired activation link
2. Verify redirect to "Activation Link Expired" page
3. Follow instructions to use "Forgot password"
4. Complete password reset
5. Verify account is now active

**Expected Result:** ✅ Expired link handled gracefully, reactivation works

---

### Test 9: Password Reset Timestamps

**Steps:**
1. Request password reset for admin
2. Check database:

```bash
python -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print(f'Reset Requested: {user.password_reset_requested_date}')
    print(f'Reset Completed: {user.password_reset_completed_date}')
"
```

3. Complete password reset
4. Check database again

**Expected Result:** ✅ Both timestamps populated correctly

---

### Test 10: Duplicate Email Registration

**Steps:**
1. Try to register with email: `admin@example.com`
2. Fill out form correctly
3. Accept terms

**Expected Result:** ✅ Error message: "Email address already registered."

---

## Database Inspection Commands

### View all users:
```bash
python -c "
from app import app, db
from models import User
with app.app_context():
    users = User.query.all()
    for u in users:
        print(f'{u.username} | {u.email} | Active: {u.is_active} | Created: {u.user_created_date}')
"
```

### Check user details:
```bash
python -c "
from app import app, db
from models import User
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    print(f'ID: {user.id}')
    print(f'Username: {user.username}')
    print(f'Email: {user.email}')
    print(f'Forename: {user.forename}')
    print(f'Surname: {user.surname}')
    print(f'Job Title: {user.job_title}')
    print(f'Telephone: {user.telephone}')
    print(f'Active: {user.is_active}')
    print(f'Created: {user.user_created_date}')
    print(f'Last Login: {user.date_last_logged_in}')
    print(f'Terms Consent: {user.terms_consent_date}')
"
```

## Troubleshooting

### Email not sending:
- Verify Gmail App Password is correct
- Check `app.py` MAIL_USERNAME and MAIL_PASSWORD
- Check terminal for error messages
- Try test email:
```bash
python -c "
from app import app, mail
from flask_mail import Message
with app.app_context():
    msg = Message('Test', recipients=['your-email@gmail.com'])
    msg.body = 'Test email'
    mail.send(msg)
    print('Test email sent!')
"
```

### Modal not opening:
- Check browser console for JavaScript errors
- Ensure Bootstrap 5.3.2 is loading
- Clear browser cache

### Database errors:
- Delete and recreate: `rm instance/da11_tracker.db && python init_user.py`
- Check all new fields are added in models.py

## Success Criteria

All tests should pass with:
- ✅ No server errors in terminal
- ✅ No JavaScript errors in browser console
- ✅ Emails delivered successfully
- ✅ Database timestamps recorded correctly
- ✅ Account activation works
- ✅ Expired links handled properly
- ✅ Password reset reactivates accounts
- ✅ Login blocked for inactive accounts
- ✅ UI matches design specifications

## Report Issues

If any test fails, note:
1. Which test failed
2. Error messages (terminal and browser console)
3. Expected vs actual behavior
4. Database state (use inspection commands above)
