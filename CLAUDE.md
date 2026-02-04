# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Deployment

**Live URL**: https://da1-1-tracker.onrender.com

**GitHub**: https://github.com/eightieskid83/da1-1-tracker

**Hosting**: Render (Free tier)
- Web Service: `da1-1-tracker`
- PostgreSQL Database: `da1-1-tracker-db`

Auto-deploy is enabled: every `git push` to `main` triggers a new deployment.

## Commands

```bash
# Local Development (macOS)
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Access at http://localhost:5000

# Local Development (Windows)
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Production | PostgreSQL connection URL (Render provides this) |
| `SECRET_KEY` | Production | Flask secret key for sessions |
| `MAIL_SERVER` | Optional | SMTP server (default: smtp.gmail.com) |
| `MAIL_PORT` | Optional | SMTP port (default: 587) |
| `MAIL_USERNAME` | Optional | SMTP username |
| `MAIL_PASSWORD` | Optional | SMTP password/app password |
| `MAIL_DEFAULT_SENDER` | Optional | Default email sender address |

Local development uses SQLite automatically (no env vars needed).

## Architecture

Flask web application for tracking apprentice EPA (End-Point Assessment) records.

**Database**:
- Production: PostgreSQL on Render
- Local: SQLite (`sqlite:///da11_tracker.db`)

### Key Files

- **app.py** - Flask routes and business logic. Contains dashboard metrics, export endpoints (CSV, XLSX, PDF), CSV/XLSX upload import, and user profile management
- **models.py** - SQLAlchemy models:
  - `ApprenticeRecord` model with auto-calculated properties:
    - `variance_days`: first_attempt_date - project_deadline_date
    - `within_epa_window`: "Yes" if grade_date within 84 days (12 weeks) of approved_for_epa
  - `User` model with authentication and profile fields:
    - `deleted_account_date`: Timestamp for soft-deleted accounts
    - `approval_status`: `'pending'` | `'approved'` | `'rejected'` — controls whether new registrations require admin sign-off before activation
    - `is_admin()`, `is_viewer()`, `is_deleted()` methods for role checking
- **database.py** - SQLAlchemy initialization with dual-mode storage:
  - Uses `DATABASE_URL` environment variable for PostgreSQL (production)
  - Falls back to `sqlite:///da11_tracker.db` for local development
  - Handles Render's `postgres://` to `postgresql://` URL conversion
  - Auto-creates default admin user on first run if no users exist
- **migrate_add_approval_status.py** - Adds `approval_status` column and backfills existing users to `'approved'`. Run once: `python migrate_add_approval_status.py`

### Routes

#### Authentication Routes
| Route | Description |
|-------|-------------|
| `/login` | User login |
| `/logout` | User logout |
| `/register` | User registration — sets `approval_status='pending'`, no email sent |
| `/activate/<token>` | Account activation via email link |
| `/forgot-password` | Request password reset |
| `/reset-password/<token>` | Reset password via email link |

#### Record Management Routes
| Route | Access | Description |
|-------|--------|-------------|
| `/` | All Users | Dashboard with metrics |
| `/records` | All Users | List all records (paginated, 20 per page, filterable) |
| `/add` | Admin Only | Add new record (form) |
| `/edit/<id>` | Admin Only | Edit existing record |
| `/view/<id>` | All Users | View record details |
| `/delete/<id>` | Admin Only | Delete record (POST) |
| `/upload` | Admin Only | Import records from CSV/XLSX (POST) |
| `/export/csv` | All Users | Export as CSV |
| `/export/xlsx` | All Users | Export as Excel |
| `/export/pdf` | All Users | Export as PDF |

#### User Profile Routes
| Route | Description |
|-------|-------------|
| `/profile/update` | Update user profile (POST) - forename, surname, email, job_title, telephone |
| `/profile/change-password` | Change password (POST) - requires current password, new password must be 8+ chars |
| `/profile/delete` | Delete account (soft delete with email confirmation) (POST) |

#### Admin Notification Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/admin/notifications` | GET | Returns JSON array of users with `approval_status='pending'` |
| `/admin/notifications/approve/<id>` | POST | Sets `approval_status='approved'`, regenerates token if expired, sends activation email |
| `/admin/notifications/reject/<id>` | POST | Sets `approval_status='rejected'`, sends rejection email |

### Filtering

The `/records` route supports filtering via query parameters:
- `status` - Filter by status value
- `grade` - Filter by overall grade
- `window` - Filter by within EPA window (Yes/No)
- Date range filters: `gateway_from/to`, `approved_from/to`, `project_start_from/to`, `deadline_from/to`, `first_attempt_from/to`, `second_attempt_from/to`, `grade_date_from/to`

### User Roles & Permissions

- **Admin** (`role='admin'`): Full access to create, edit, delete records and upload files
- **Viewer** (`role='viewer'`): Can view dashboard, records, and export data. Cannot create/edit/delete records or upload files
- **Deleted Accounts**: Users with `deleted_account_date` set cannot log in

**Non-Admin UI**: Upload and "Add New Record" buttons are visible but disabled for non-admin users, with tooltips: "Admin access required to access these features, please contact local administrator."

### Templates

All templates extend `base.html` which includes Bootstrap 5.3, Plus Jakarta Sans font, and navbar with user dropdown menu. Custom styling in `static/style.css` uses brand colors: navbar `#0d004d`, table headers `#512eab`, background `#edecf6`, filter modal header `#0d004d`, date range filter band `#512eab`, warning buttons `#FFCE00`.

**Navbar**: Displays "Welcome, [forename]" dropdown with Edit Profile, Change Password, Delete Account, and Logout options. Admin users also see a bell icon with a red badge showing the count of pending registrations. Clicking the bell fetches `/admin/notifications` and populates a dropdown; clicking an item opens the Approval modal.

**Profile Modals**: Edit Profile modal allows users to update their details. Change Password modal requires current password validation and new password confirmation (minimum 8 characters). Delete Account modal includes confirmation and sends email notification upon deletion.

**Approval Modal** (admin only): Opens from a notification dropdown item. Displays the pending user's name, email, and registration date. Accept sends the activation email and sets `approval_status='approved'`; Reject sends a rejection email and sets `approval_status='rejected'`. The notification disappears from the dropdown on either outcome.

**Email Templates**: `emails/activation.html` and `.txt` are used for both the original (now removed) auto-send and the admin-approve flow. `emails/rejection.html` and `.txt` mirror the activation template structure but contain no button or link.

### Data Values

**Grade values**: `Distinction`, `Merit`, `Pass`, `Fail` (case-sensitive)

**Status values**: `In Training`, `Gateway in Progress`, `Gateway Evidence Complete`, `Gateway Submitted`, `Denied EPA`, `Approved for EPA`, `EPA in Progress`, `EPA Evidence Complete`, `EPA Failed`, `EPA Passed`

### CSV/XLSX Upload Column Mapping

| Upload Column | Database Field |
|--------------|----------------|
| ACE360 ID | ace360_id |
| Status | status |
| Gateway Submitted Date | gateway_submitted |
| EPA Ready Date | approved_for_epa |
| Project Start Date | project_start_date |
| Project Deadline | project_deadline_date |
| First Attempt Booking Date | first_attempt_date |
| Second Attempt Booking Date | second_attempt_date |
| Overall Grade | overall_grade |
| Grade Date | grade_date |

Upload skips records where ACE360 ID already exists in the database.

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately – don't keep pushing.
- Use plan mode for verification steps, not just building.
- Write detailed specs upfront to reduce ambiguity.

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean.
- Offload research, exploration, and parallel analysis to subagents.
- For complex problems, throw more compute at it via subagents.
- One task per subagent for focused execution.

### 3. Self-Improvement Loop
- After ANY correction from the user: update tasks/lessons.md with the pattern.
- Write rules for yourself that prevent the same mistake.
- Ruthlessly iterate on these lessons until mistake rate drops.
- Review lessons at session start for relevant project.

### 4. Verification Before Done
- Never mark a task complete without proving it works.
- Diff behaviour between main and your changes when relevant.
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness.

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution."
- Skip this for simple, obvious fixes – don't over-engineer.
- Challenge your own work before presenting it.

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests – then resolve them.
- Zero context switching required from the user.
- Go fix failing CI tests without being told how.

## Task Management

**Plan First**: Write plan to tasks/todo.md with checkable items.

**Verify Plan**: Check in before starting implementation.

**Track Progress**: Mark items complete as you go.

**Explain Changes**: High-level summary at each step.

**Document Results**: Add review section to tasks/todo.md.

**Capture Lessons**: Update tasks/lessons.md after corrections.

## Core Principles

**Simplicity First**: Make every change as simple as possible. Impact minimal code.

**No Laziness**: Find root causes. No temporary fixes. Senior developer standards.

**Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.
