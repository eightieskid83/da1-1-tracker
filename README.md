# DA1.1 Tracker

## Overview

DA1.1 Tracker is a web application for tracking apprentice EPA (End-Point Assessment) records and quality analysis. Built with Python/Flask and SQLite.

## Features

- **User Authentication** - Secure login system with password reset via email
- **CRUD Operations** - Create, read, update, and delete apprentice records
- **Auto-Calculated Fields**:
  - **Variance (Days)**: First Attempt Date - Project Deadline Date
  - **Within EPA Window**: "Yes" if Grade Date is within 84 days (12 weeks) of Approved for EPA date
- **Dashboard Metrics** - Visual analytics and key performance indicators
- **Data Export** - Export records to CSV, Excel (XLSX), and PDF formats
- **Data Import** - Bulk import from CSV/XLSX files
- **Bootstrap UI** - Clean, responsive interface with Pearson brand colors

## Setup Instructions

### 1. Create a Virtual Environment (Recommended)

```bash
cd "/Users/chrisoley/Documents/Generative AI/Claude Code/DA1.1 Tracker"
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Email (Optional - for password reset)

Edit `app.py` and update the email configuration:

```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-app-password'
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'
```

**For Gmail:** You'll need to generate an App Password:
1. Go to your Google Account settings
2. Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use this password in the configuration

### 4. Initialize the Database

```bash
python init_user.py
```

This will create the database tables and a default admin user:
- **Username:** admin
- **Password:** admin123

**IMPORTANT:** Change this password after your first login!

### 5. Run the Application

```bash
python app.py
```

### 6. Access the Application

Open your browser to: http://localhost:5000

You'll be redirected to the login page. Use the admin credentials to log in.

## Project Structure

```
DA1.1 Tracker/
├── README.md
├── app.py                      # Flask application with routes
├── models.py                   # SQLAlchemy models (User, ApprenticeRecord)
├── database.py                 # Database configuration
├── init_user.py                # Database initialization script
├── requirements.txt            # Python dependencies
├── templates/
│   ├── base.html               # Base template with navigation
│   ├── login.html              # Login page
│   ├── forgot_password.html    # Forgot password page
│   ├── reset_password.html     # Password reset page
│   ├── dashboard.html          # Dashboard with metrics
│   ├── index.html              # List all records (paginated)
│   ├── form.html               # Add/edit record form
│   └── view.html               # View single record
└── static/
    └── style.css               # Custom styles (Pearson brand colors)
```

## Database

The application uses SQLite (file: `da11_tracker.db`). The database is created automatically on first run.

### Fields Tracked

| Field | Description |
|-------|-------------|
| ACE360 ID | Unique apprentice identifier |
| Gateway Submitted | Date gateway was submitted |
| Approved for EPA | Date approved for EPA |
| Project Start Date | Project start date |
| Project Deadline Date | Project deadline |
| First Attempt Date | First assessment attempt |
| Second Attempt Date | Second attempt (optional) |
| Overall Grade | Distinction/Merit/Pass/Fail |
| Grade Date | Date grade was awarded |
| **Variance (Days)** | *Auto-calculated* |
| **Within EPA Window** | *Auto-calculated* |
