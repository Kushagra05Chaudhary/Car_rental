# aSk.ren — Car Rental Platform

A full-featured car rental web application built with **Django 5**, **MySQL**, **Tailwind CSS**, and **ReportLab**. The platform supports three user roles — **Admin**, **Owner**, and **User** — each with a dedicated dashboard and feature set.

---

## Features

### Users
- Register / Login with OTP email verification
- Browse and filter available cars (by type, location, seats, price, sort)
- View detailed car pages with reviews and ratings
- Book cars with a date picker (only confirmed bookings block dates)
- 15-minute booking hold to complete payment
- Checkout with live total calculation
- View transaction history with payment status
- Download PDF invoices for completed payments
- Submit reviews for completed bookings

### Car Owners
- Register as an owner (requires admin approval)
- Add, edit, delete, and toggle availability of cars
- Car listings pending admin approval before going live
- View own bookings and accept / reject booking requests
- Owner dashboard with earnings and booking stats

### Admins
- Platform-wide analytics dashboard
- Approve / reject car listings and owner requests
- Manage all users, cars, and bookings
- View all transactions with refund tracking
- Net revenue = gross revenue − refunds
- Monthly revenue and booking charts
- Generate and download reports as PDF
- Platform commission tracking (10%)

---

## Tech Stack

| Layer       | Technology                              |
|-------------|-----------------------------------------|
| Backend     | Django 5.2, Python 3.10                 |
| Database    | MySQL (`mysqlclient`)                   |
| Frontend    | Tailwind CSS (CDN), Alpine.js (CDN)     |
| Charts      | Chart.js (CDN)                          |
| Date Picker | Flatpickr (CDN)                         |
| PDF Reports | ReportLab                               |
| Email       | Gmail SMTP (OTP + notifications)        |
| Auth        | Custom User Model (`accounts.CustomUser`) |
| Media       | Pillow (image uploads)                  |
| Env Config  | python-dotenv                           |

---

## Project Structure

```
Car_rental/
├── requirements.txt
├── README.md
└── car_rental/                  # Django project root
    ├── manage.py
    ├── car_rental/              # Project settings & URLs
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    ├── apps/
    │   ├── accounts/            # Auth, OTP, custom user, roles
    │   ├── cars/                # Car model, owner car management
    │   ├── bookings/            # Booking model, hold system, services
    │   ├── payments/            # Payment model, checkout, PDF invoices
    │   ├── dashboard/           # Admin & owner dashboards, analytics
    │   ├── notifications/       # In-app notifications
    │   ├── reports/             # Owner earnings reports
    │   └── reviews/             # Car reviews & ratings
    ├── templates/               # All HTML templates
    ├── static/                  # CSS, JS, images, vendor assets
    └── media/                   # Uploaded car images & documents
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/car-rental.git
cd car-rental
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `car_rental/` directory (same folder as `manage.py`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# MySQL
DATABASE_NAME=car_rental
DATABASE_USER=root
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=3306

# Gmail SMTP (for OTP & notifications)
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

> For Gmail, use an **App Password** — not your regular password. Enable 2FA on your Google account, then generate one at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).

### 5. Create the MySQL Database

```sql
CREATE DATABASE car_rental CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Run Migrations

```bash
cd car_rental
python manage.py migrate
```

### 7. Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

Then log in and set `role = 'admin'` for that user from the Django admin panel at `/admin/`.

### 8. Start the Development Server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

---

## User Roles

| Role  | How to Get It                                            |
|-------|----------------------------------------------------------|
| User  | Register normally at `/accounts/register/`               |
| Owner | Register → apply for owner role → admin approves request |
| Admin | Created via `createsuperuser`, then assign role in admin |

---

## Key URLs

| URL                              | Description                      |
|----------------------------------|----------------------------------|
| `/`                              | Home / landing page              |
| `/cars/`                         | Browse all available cars        |
| `/cars/<id>/`                    | Car detail page                  |
| `/bookings/create/<car_id>/`     | Start a booking                  |
| `/payments/checkout/<id>/`       | Checkout & confirm payment       |
| `/payments/my-transactions/`     | User transaction history         |
| `/dashboard/`                    | Role-based dashboard redirect    |
| `/dashboard/owner/`              | Owner dashboard                  |
| `/dashboard/admin/`              | Admin overview                   |
| `/dashboard/admin/all-cars/`     | Admin: manage all cars           |
| `/dashboard/admin/bookings/`     | Admin: view all bookings         |
| `/dashboard/admin/transactions/` | Admin: all transactions          |
| `/dashboard/admin/reports/`      | Admin: analytics & PDF report    |
| `/accounts/login/`               | Login                            |
| `/accounts/register/`            | Register                         |

---

## Configuration Reference

| Setting                    | File           | Default               | Description                        |
|----------------------------|----------------|-----------------------|------------------------------------|
| `BOOKING_HOLD_MINUTES`     | `settings.py`  | `15`                  | Minutes a booking hold is reserved |
| `PLATFORM_COMMISSION_RATE` | `settings.py`  | `0.10`                | Platform fee (10% of booking)      |
| `AUTH_USER_MODEL`          | `settings.py`  | `accounts.CustomUser` | Custom user model                  |
| `MEDIA_ROOT`               | `settings.py`  | `car_rental/media/`   | Uploaded files storage path        |
| `DEBUG`                    | `.env`         | `True`                | Set to `False` in production       |

---

## PDF Reports

PDF invoice generation and admin reports are powered by **ReportLab**.

- User invoices: `/payments/invoice/<payment_id>/pdf/`
- Admin report: available from the Reports & Analytics page in the admin dashboard

---

## License

This project is for educational and portfolio purposes.
