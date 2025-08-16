# 🏠 Short Term Landlord - Local Access Guide

## 🚀 Application is Running!

The Short Term Landlord application is now running locally on port 5001.

---

## 🔐 Login Credentials

Use these credentials to access the application:

| Role | Email | Password |
|------|-------|----------|
| **Admin** | admin@landlord.com | admin123 |
| **Cleaner** | cleaner@example.com | password123 |
| **Owner** | owner@example.com | password123 |
| **Maintenance** | maintenance@example.com | password123 |

---

## 📍 Main Application URLs

### 🏠 Core Pages
- **Homepage**: http://localhost:5001/
- **Login Page**: http://localhost:5001/auth/login
- **Dashboard**: http://localhost:5001/dashboard
- **Logout**: http://localhost:5001/auth/logout

### 📅 Calendar Management
- **Combined Calendar View**: http://localhost:5001/combined-calendar
- **Calendar Sync**: http://localhost:5001/calendar
- **Property Calendars**: http://localhost:5001/property-calendars

### 🏘️ Property Management
- **Properties List**: http://localhost:5001/properties
- **Add New Property**: http://localhost:5001/properties/new
- **Property Details**: http://localhost:5001/properties/{id}
- **Property Images**: http://localhost:5001/properties/{id}/images

### ✅ Task Management
- **Tasks Dashboard**: http://localhost:5001/tasks
- **Create Task**: http://localhost:5001/tasks/new
- **Task Templates**: http://localhost:5001/task-templates
- **Task Assignment**: http://localhost:5001/tasks/assign
- **My Tasks**: http://localhost:5001/tasks/my

### 📦 Inventory Management
- **Inventory Dashboard**: http://localhost:5001/inventory
- **Add Inventory Item**: http://localhost:5001/inventory/new
- **Inventory Transactions**: http://localhost:5001/inventory/transactions
- **Low Stock Alerts**: http://localhost:5001/inventory/alerts

### 💰 Financial Management
- **Invoices List**: http://localhost:5001/invoices
- **Create Invoice**: http://localhost:5001/invoices/new
- **Invoice Details**: http://localhost:5001/invoices/{id}
- **Service Pricing**: http://localhost:5001/service-prices

### 🧹 Cleaning Management
- **Cleaning Sessions**: http://localhost:5001/cleaning
- **Quality Control**: http://localhost:5001/cleaning/quality
- **Cleaning Reports**: http://localhost:5001/cleaning/reports

### 🔧 Maintenance & Repairs
- **Repair Requests**: http://localhost:5001/repairs
- **Submit Repair Request**: http://localhost:5001/repairs/new
- **Maintenance Schedule**: http://localhost:5001/maintenance/schedule

### 💬 Communication
- **Messages**: http://localhost:5001/messages
- **SMS Conversations**: http://localhost:5001/sms
- **Notifications**: http://localhost:5001/notifications

---

## 👤 Admin-Only URLs

### 🎛️ Admin Panel
- **Admin Dashboard**: http://localhost:5001/admin
- **User Management**: http://localhost:5001/admin/users
- **Site Settings**: http://localhost:5001/admin/settings
- **System Health**: http://localhost:5001/admin/health
- **Activity Logs**: http://localhost:5001/admin/logs

### 🔧 Admin Tools
- **Database Admin**: http://localhost:5001/admin/database
- **Cache Management**: http://localhost:5001/admin/cache
- **Task Queue**: http://localhost:5001/admin/queue
- **Error Logs**: http://localhost:5001/admin/errors

---

## 🔑 Guest Portal URLs

### 👥 Guest Access
- **Guest Portal**: http://localhost:5001/guest
- **Guest Registration**: http://localhost:5001/guest/register
- **Property Access**: http://localhost:5001/guest/property/{code}
- **Guest Guidebook**: http://localhost:5001/guest/guidebook
- **Guest Reviews**: http://localhost:5001/guest/reviews

### 📖 Guest Resources
- **Local Recommendations**: http://localhost:5001/recommendations
- **House Rules**: http://localhost:5001/guest/rules
- **Emergency Contacts**: http://localhost:5001/guest/emergency
- **Check-out Instructions**: http://localhost:5001/guest/checkout

---

## 🛠️ API Endpoints

### 📊 RESTful API
- **API Documentation**: http://localhost:5001/api/docs
- **Properties API**: http://localhost:5001/api/properties
- **Tasks API**: http://localhost:5001/api/tasks
- **Calendar API**: http://localhost:5001/api/calendar
- **Users API**: http://localhost:5001/api/users

### 📈 Webhooks
- **Calendar Sync Webhook**: http://localhost:5001/webhooks/calendar-sync
- **SMS Webhook**: http://localhost:5001/webhooks/sms
- **Payment Webhook**: http://localhost:5001/webhooks/payment

---

## 🔍 Debug & Development URLs

### 🐛 Debug Routes
- **Debug Info**: http://localhost:5001/debug
- **Route List**: http://localhost:5001/debug/routes
- **Database Status**: http://localhost:5001/debug/db
- **Session Info**: http://localhost:5001/debug/session
- **Admin Debug**: http://localhost:5001/debug-admin

### 📊 Health Checks
- **Health Status**: http://localhost:5001/health
- **Database Health**: http://localhost:5001/health/db
- **Redis Health**: http://localhost:5001/health/redis
- **Ready Check**: http://localhost:5001/health/ready

---

## 🎨 Special Features

### 📱 Mobile-Optimized Views
All pages are mobile-responsive and optimized for:
- Smartphones (iOS/Android)
- Tablets (iPad/Android tablets)
- Touch-friendly interfaces

### 🌐 Calendar Integration
- **Airbnb iCal Sync**: Automatic synchronization
- **VRBO Calendar**: Real-time updates
- **Booking.com**: Bidirectional sync
- **Google Calendar**: OAuth integration

### 🔔 Real-Time Features
- Live task updates
- Instant notifications
- Real-time calendar sync
- SMS messaging

---

## 📝 Quick Start Guide

1. **First Login**:
   - Navigate to http://localhost:5001/auth/login
   - Use admin@landlord.com / admin123
   - You'll be redirected to the dashboard

2. **Add a Property**:
   - Go to http://localhost:5001/properties/new
   - Fill in property details
   - Add calendar sync URLs

3. **Create Tasks**:
   - Visit http://localhost:5001/tasks/new
   - Assign to cleaners/maintenance
   - Set due dates and priorities

4. **View Calendar**:
   - Open http://localhost:5001/combined-calendar
   - See all bookings and tasks
   - Sync with external platforms

---

## 🚨 Troubleshooting

If you encounter issues:

1. **Cannot Access**: Make sure the server is running on port 5001
2. **Login Issues**: Check credentials are exactly as shown above
3. **Database Errors**: The app uses SQLite by default (instance/app.db)
4. **Port Conflict**: If port 5001 is busy, restart with `flask run --port 5002`

---

## 🛑 Stop the Server

To stop the server, press `Ctrl+C` in the terminal where it's running.

---

**Application Status**: ✅ Running on http://localhost:5001