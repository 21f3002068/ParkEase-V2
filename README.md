# ParkEase - Smart Parking Management System

A full-stack parking management application with real-time booking, notifications, and analytics.

### Overview

This is a Vehicle Parking web application specialized in four-wheelers. It is an academic project of Modern Application Development-1 under IITM BS Data Science and Applications offered by IIT Madras.

## Project Demo

[ytvideo link]

## Tech Stack

### Backend
- Flask (Python web framework)
- Flask-Security (Authentication)
- Flask-RESTX (REST API)
- SQLAlchemy (ORM)
- Celery (Async tasks)
- Redis (Caching & message broker)

### Frontend
- Vue.js 3
- Vue Router
- Axios (HTTP client)
- Chart.js (Analytics)

### Database (Development Only)
- SQLite 

---
### Installation

```bash
# 1. Clone and setup
git clone <repository>
cd ParkEase_V2_21F3002068

# 2. Backend setup
python -m venv ParkEnv
ParkEnv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Frontend setup
cd frontend
npm install

# 4. Configure email (optional)
# Edit backend/.env with your Gmail credentials
```

### Running the Application

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
python -m backend.run

# Terminal 3: Celery Worker (for async tasks)
celery -A backend.celery_app worker --pool=solo --loglevel=info

# Terminal 4: Celery Beat (for scheduled tasks)
celery -A backend.celery_app beat --loglevel=info

# Terminal 5: Frontend
cd frontend
npm run serve
```

---

## Features

### User Features
- ✅ User registration and authentication
- ✅ Browse available parking lots
- ✅ Real-time booking system
- ✅ Park in/out functionality
- ✅ Vehicle management
- ✅ Booking history and analytics
- ✅ Favorite parking lots
- ✅ CSV export of parking history
- ✅ Google Chat/Email notifications

### Admin Features
- ✅ Dashboard with statistics
- ✅ Manage parking lots and spots
- ✅ View all reservations
- ✅ User management
- ✅ Analytics and reports
- ✅ Redis caching for performance

### Backend Jobs
- ✅ **Daily Reminders**: Notify inactive users (Google Chat/Email)
- ✅ **Monthly Reports**: HTML email reports with statistics
- ✅ **CSV Export**: User-triggered async export
- ✅ **Auto-cleanup**: Remove old files and expired reservations

---

## 📁 Project Structure

```
ParkEase_V2_21F3002068/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routes/          # API endpoints
│   │   ├── tasks/           # Celery tasks
│   │   ├── utils/           # Utilities (email, cache, etc.)
│   │   └── config.py        # Configuration
│   ├── migrations/          # Database migrations
│   ├── static/              # Static files (CSV exports)
│   ├── celery_app.py        # Celery configuration
│   └── .env                 # Environment variables
│
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── views/           # Page views
│   │   ├── router/          # Vue router
│   │   ├── utils/           # API utilities
│   │   └── assets/          # CSS and images
│   └── package.json
│
└── README.md                # This file
```

---

## Screenshots 


---

## Configuration

### Email Setup (Optional)

Edit `backend/.env`:

```bash
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
ADMIN_EMAILS=admin@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Get Gmail App Password:**
1. Go to: https://myaccount.google.com/apppasswords
2. Enable 2-Factor Authentication
3. Generate app password for "Mail"
4. Copy the 16-character password

### Google Chat Notifications (Optional)

Users can add Google Chat webhooks in their profile:
1. Login → Profile → Edit Profile
2. Scroll to "Notification Preferences"
3. Add webhook URL
4. Save

---

## ⚡ Redis Caching

### Cache Strategy
ParkEase uses Redis (Database 1) for API response caching to improve performance.

**Cache Expiry Policies:**
- Real-time data: 1-2 minutes (availability, admin dashboard)
- Semi-static data: 3-5 minutes (lots list, user dashboard)
- Analytics data: 10+ minutes (user analytics, reports)

**Performance Benefits:**
- 90%+ cache hit rate for frequently accessed data
- 50-80% faster response times
- Reduced database load by 60-90%

**Cache Invalidation:**
- Automatic: When related data changes (bookings, spot updates)
- Manual: Via `/api/cache/clear` or `/api/cache/invalidate`
- Time-based: All entries have TTL (Time To Live)

**Monitoring:**
- Check cache stats: `GET /api/cache/stats`
- View cache keys: `GET /api/cache/keys`
- Clear cache: `POST /api/cache/clear` (admin only)

---

## 🔑 Default Credentials

### Admin
- Email: `admin@parkease.com`
- Password: `admin123`

### User
- Email: `user@parkease.com`
- Password: `user123`

---

## 📊 API Endpoints

### User Endpoints (`/api/user/`)
**Authentication & Profile**
- `GET /profile` - User profile with completion tracking
- `PUT /profile` - Update user profile
- `DELETE /delete-account` - Delete user account

**Parking & Booking**
- `GET /parking_lots` - List all parking lots
- `GET /parking_lots/<id>` - Get specific lot details
- `POST /book/<lot_id>` - Book a parking spot
- `POST /park/<reservation_id>` - Park vehicle
- `POST /park_out/<reservation_id>` - Park out vehicle
- `POST /cancel_booking/<reservation_id>` - Cancel booking

**Reservations & Vehicles**
- `GET /my_reservations` - User's reservations
- `GET /my_vehicles` - User's vehicles
- `POST /add_vehicle` - Add vehicle
- `DELETE /remove_vehicle/<id>` - Remove vehicle

**Favorites & Export**
- `GET /favorites` - User's favorite lots
- `POST /favorites/<lot_id>` - Add to favorites
- `GET /export` - Start CSV export (async)
- `GET /csv_result/<task_id>` - Download CSV

### Admin Endpoints (`/api/admin/`)
**User & Lot Management**
- `GET /users` - List all users
- `POST /users` - Create user
- `DELETE /users/<id>` - Delete user
- `GET /parking_lots` - List all lots
- `POST /parking_lots` - Create lot
- `PUT /parking_lots/<id>` - Update lot

**Analytics & Tasks**
- `GET /dashboard` - Admin statistics
- `GET /analytics/dashboard` - Admin analytics
- `POST /tasks/trigger/<task_name>` - Trigger background tasks
- `GET /tasks/status/<task_id>` - Check task status

### Cached Endpoints (Performance Optimized)
**User Cached** (`/api/cached_user/`)
- `GET /lots` - Available lots (3min cache)
- `GET /dashboard` - User dashboard (5min cache)
- `GET /analytics` - User analytics (10min cache)

**Admin Cached** (`/api/cached_admin/`)
- `GET /dashboard` - Admin overview (2min cache)
- `GET /analytics` - Admin analytics (5min cache)

**Cache Management** (`/api/cache/`)
- `GET /stats` - Cache statistics
- `POST /clear` - Clear all cache (admin only)
- `POST /invalidate` - Invalidate by pattern

---

## 🔄 Background Tasks & Scheduling

### Automated Tasks (Celery Beat)

**Daily Reminders** (Every 2 minutes - Testing Mode)
- Notify inactive users via Google Chat/Email
- TODO: Change to `crontab(hour=18, minute=0)` for production

**Monthly Reports** (Every 2 minutes - Testing Mode)
- Send HTML email reports with statistics
- Includes revenue analysis, user engagement, lot performance
- TODO: Change to `crontab(day_of_month=1, hour=9, minute=0)` for production

**CSV Cleanup** (Daily at 2:00 AM)
- Remove CSV files older than 7 days
- Keeps `static/` directory clean

**Auto-release Expired Reservations** (Every hour)
- Releases reservations without checkout after 24 hours
- Calculates final costs and frees up spots

### User-Triggered Tasks

**CSV Export**
- Async export of user's parking history
- Triggered via: `GET /api/user/export`
- Check status: `GET /api/user/export/status/<task_id>`
- Download: `GET /api/user/csv_result/<task_id>`

### Task Configuration
Edit `backend/celery_app.py` to modify schedules:
```python
beat_schedule = {
    'daily-reminders': {
        'task': 'send_daily_reminders',
        'schedule': 120.0,  # Every 2 minutes (testing)
        # 'schedule': crontab(hour=18, minute=0),  # Production
    }
}
```

---

## Contact

For questions and support, please contact:

- Project Maintainer: Vaibhav Satish
- Email: 21f3002068@ds.study.iitm.ac.in