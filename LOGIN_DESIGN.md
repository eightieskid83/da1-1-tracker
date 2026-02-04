# Login Page Design Specifications

## Overview

The DA1.1 Tracker login page features a clean, modern design using Pearson brand colors and the Plus Jakarta Sans font family.

## Color Scheme

| Color | Hex Code | Usage |
|-------|----------|-------|
| Pearson Purple | `#0D004D` | Primary headings, navbar, focus states |
| Pearson Yellow | `#FFCE00` | Login button, primary call-to-action |
| Light Purple | `#EDECF6` | Page background |
| Secondary Purple | `#512EAB` | Links, hover states |
| White | `#FFFFFF` | Card background, text on dark backgrounds |
| Dark Text | `#0D004D` | Form labels, headings |
| Secondary Text | `#6C757D` | Helper text, descriptions |

## Typography

- **Font Family:** Plus Jakarta Sans (Google Fonts)
- **Main Heading:** 2rem, weight 700, color #0D004D
- **Body Text:** 0.95rem, weight 400
- **Labels:** 0.9rem, weight 600, color #0D004D
- **Links:** 0.9rem, weight 600, color #512EAB

## Components

### Login Card

- **Background:** White (#FFFFFF)
- **Border Radius:** 12px
- **Box Shadow:** `0 10px 40px rgba(13, 0, 77, 0.15)`
- **Padding:** 3rem 2.5rem
- **Max Width:** 450px
- **Centered:** Vertically and horizontally on page

### Input Fields

- **Border:** 2px solid #E0E0E0
- **Border Radius:** 8px
- **Padding:** 0.75rem 1rem
- **Font Size:** 0.95rem
- **Focus Border:** #0D004D
- **Focus Shadow:** `0 0 0 0.2rem rgba(13, 0, 77, 0.15)`

### Login Button

- **Background:** #FFCE00 (Pearson Yellow)
- **Color:** #0D004D
- **Font Weight:** 700
- **Font Size:** 1rem
- **Padding:** 0.85rem
- **Border Radius:** 8px
- **Width:** 100%
- **Hover Background:** #E6B800
- **Hover Effect:** `translateY(-2px)` with shadow `0 6px 20px rgba(255, 206, 0, 0.4)`

### Forgot Password Link

- **Color:** #512EAB (Secondary Purple)
- **Font Weight:** 600
- **Font Size:** 0.9rem
- **Text Decoration:** None (underline on hover)
- **Hover Color:** #0D004D

## Page Layout

```
┌─────────────────────────────────────────┐
│         (Background: #EDECF6)           │
│                                         │
│    ┌─────────────────────────────┐     │
│    │                             │     │
│    │       DA1.1 Tracker         │     │ ← Heading (2rem, #0D004D)
│    │  Sign in to access your     │     │ ← Subtitle (0.95rem, #6C757D)
│    │       dashboard             │     │
│    │                             │     │
│    │  ┌───────────────────────┐  │     │
│    │  │ Username              │  │     │ ← Label (#0D004D)
│    │  │ [Enter username...]   │  │     │ ← Input field
│    │  └───────────────────────┘  │     │
│    │                             │     │
│    │  ┌───────────────────────┐  │     │
│    │  │ Password              │  │     │ ← Label (#0D004D)
│    │  │ [Enter password...]   │  │     │ ← Input field
│    │  └───────────────────────┘  │     │
│    │                             │     │
│    │  ┌───────────────────────┐  │     │
│    │  │       Login           │  │     │ ← Button (#FFCE00)
│    │  └───────────────────────┘  │     │
│    │                             │     │
│    │    Forgot your password?    │     │ ← Link (#512EAB)
│    │                             │     │
│    └─────────────────────────────┘     │
│                                         │
└─────────────────────────────────────────┘
```

## Interactions

### Hover States

1. **Input Fields:**
   - No background change
   - Border remains #E0E0E0

2. **Login Button:**
   - Background: #E6B800 (darker yellow)
   - Transform: translateY(-2px)
   - Box Shadow: `0 6px 20px rgba(255, 206, 0, 0.4)`

3. **Forgot Password Link:**
   - Color changes to #0D004D
   - Underline appears

### Focus States

1. **Input Fields:**
   - Border: #0D004D
   - Box Shadow: `0 0 0 0.2rem rgba(13, 0, 77, 0.15)`
   - Outline: None

2. **Login Button:**
   - Background: #E6B800
   - Transform: translateY(0) (pressed effect)

## Responsive Design

The login page is fully responsive:

- **Desktop (>768px):** Card max-width 450px, centered
- **Tablet (768px):** Card fills width with 2rem padding
- **Mobile (<768px):** Card fills width with 1rem padding

## Accessibility

- All form fields have proper labels
- Focus states are clearly visible
- Color contrast meets WCAG AA standards
- Keyboard navigation is fully supported
- Form inputs have appropriate `type` attributes
- Required fields are marked with `required` attribute

## Additional Pages

### Forgot Password Page

- Same design structure as login page
- Heading: "Forgot Password?"
- Description: "Enter your email address and we'll send you a link to reset your password."
- Single email input field
- Button: "Send Reset Link" (same #FFCE00 styling)
- Link: "Back to Login" (#512EAB)

### Reset Password Page

- Same design structure
- Heading: "Reset Password"
- Two password input fields:
  - New Password
  - Confirm Password
- Password requirements box (light gray background, #512EAB left border)
- Button: "Reset Password" (#FFCE00)

## Implementation Files

- `templates/login.html` - Login page
- `templates/forgot_password.html` - Forgot password page
- `templates/reset_password.html` - Reset password page

All pages include inline styles for consistency and independence from the main application styling.
