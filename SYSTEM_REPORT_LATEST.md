# 🛡️ Smart Anti-Theft System - Complete System Report (Latest Version)

## 📋 Executive Summary

A full-stack anti-theft and device security monitoring system inspired by Prey Project. Provides real-time device tracking, remote control capabilities, and comprehensive security monitoring for Windows, Mac, Linux, and iOS devices.

**Latest Updates:**
- ✅ **Fingerprinting removed** - System now uses `device_id` only for device identification
- ✅ **Supabase Database** - Production uses Supabase (PostgreSQL) hosted database
- ✅ **Email Verification** - Verified account flow with email verification codes

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  - Dashboard, Device Management, Maps, QR Scanner          │
│  - Login / Sign Up / Verify Email (verified account flow)   │
│  - Deployed on Vercel                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS
                       │ REST API + JWT Auth
┌──────────────────────▼──────────────────────────────────────┐
│              Backend (Flask + SQLAlchemy)                    │
│  - REST API endpoints                                        │
│  - JWT authentication                                        │
│  - Email verification (verification code, verify_email)      │
│  - Background job scheduler                                  │
│  - Deployed on Vercel                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │ HTTP/HTTPS                │ DATABASE_URL
         ▼                           ▼
┌─────────────────────┐    ┌─────────────────────────────────┐
│  Device Agents       │    │  Supabase (PostgreSQL)           │
│  (Python)            │    │  - Hosted PostgreSQL database   │
│  - agent.py          │    │  - users (email_verified,        │
│  - iOS agent         │    │    verification_code, etc.)     │
│  - Local discovery   │    │  - devices, activity_logs,       │
│    (device_id only)  │    │    breach_reports, etc.           │
└─────────────────────┘    │  - Connection pooler for Vercel  │
                           └─────────────────────────────────┘
```

### Technology Stack

- **Backend:** Flask, SQLAlchemy, Flask-JWT-Extended, APScheduler
- **Frontend:** React, Vite, Tailwind CSS, Google Maps API
- **Database:** 
  - **Production:** Supabase (PostgreSQL) - set via `DATABASE_URL` environment variable
  - **Local Development:** SQLite (automatic fallback)
- **Agent:** Python 3.8+, requests, platform-specific libraries
- **Deployment:** Vercel (serverless functions)

---

## 🔄 Complete System Flows

### 1. User Registration & Email Verification Flow

```
┌─────────────┐     POST /api/register_user      ┌─────────────┐
│  User       │ ───────────────────────────────► │  Backend     │
│  (Sign Up)  │  email, password, name           │              │
└──────┬──────┘                                  └──────┬───────┘
       │                                                │
       │                                                │ Create user
       │                                                │ email_verified = false
       │                                                │ Generate 6-digit code
       │                                                │ Send verification email
       │                                                ▼
       │                                         ┌─────────────┐
       │                                         │  Supabase    │
       │                                         │  users row   │
       │                                         │  (unverified) │
       │                                         └──────┬───────┘
       │                                                │
       │  Response: verification_required = true       │
       │  Redirect to /verify-email                     │
       │◄───────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     POST /api/verify_email       ┌─────────────┐
│  Verify     │ ───────────────────────────────► │  Backend    │
│  Email page │  email, code (6 digits)          │              │
└──────┬──────┘                                  └──────┬──────┘
       │                                                 │
       │                                                 │ Check code
       │                                                 │ Set email_verified = true
       │                                                 │ Clear verification_code
       │                                                 ▼
       │  JWT token + redirect to dashboard      ┌─────────────┐
       │◄────────────────────────────────────────│  Verified   │
       │                                          │  Account    │
       │                                          └─────────────┘
       ▼
  ✅ Full access to dashboard
  ✅ Can link devices
  ✅ All features enabled
```

**Key Points:**
- User registers → receives 6-digit verification code via email
- Code expires in 15 minutes
- User enters code on Verify Email page
- Once verified, account is fully activated
- Unverified accounts cannot access dashboard features

---

### 2. Device Registration Flow (Agent-First, No Fingerprinting)

```
┌─────────────┐
│ Agent Starts│
│  (agent.py) │
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│ Check config.json        │
│ - Has device_id?          │
│   Yes → Verify with backend│
│   No → Register new device│
└──────┬──────────────────┘
       │
       ├──► Device ID exists?
       │    ├─ Yes → Verify with backend
       │    │   ├─ Found? → Continue
       │    │   └─ Not found? → Re-register
       │    │
       │    └─ No → Register new device
       │
       ▼
┌─────────────────────────┐
│ Detect Hardware Info     │
│ (Optional - for display) │
│ - CPU, RAM, Motherboard  │
│ - BIOS, Serial numbers   │
│ - Network interfaces     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ POST /api/devices/       │
│ agent/register           │
│ - device_id (generated)   │
│ - user_email (if set)    │
│ - hardware_info          │
│ - os_info                │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend Creates Device   │
│ - device_id (unique)     │
│ - user_id = NULL         │
│   (unowned)              │
│ - device_type =          │
│   "agent_device"         │
│ - Stores hardware info   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Agent Saves device_id    │
│ to config.json           │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Start Local Server       │
│ http://127.0.0.1:9123/   │
│ device-info              │
│ Returns: device_id only  │
└──────┬──────────────────┘
       │
       │ Agent Running (Background)
       │
       ▼
┌─────────────────────────┐
│ User Logs In to Frontend│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend Discovers       │
│ Local Agent             │
│ GET localhost:9123/     │
│ device-info             │
│ Response: {device_id}   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend Sends device_id │
│ to Backend on Login     │
│ POST /api/login          │
│ {device_id: "..."}      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend Links Device    │
│ to User Account         │
│ - Sets user_id          │
│ - Device now "owned"    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Device Appears in       │
│ Dashboard               │
│ ✅ Full Features Enabled│
└─────────────────────────┘
```

**Key Changes:**
- ❌ **No fingerprinting** - Uses `device_id` only (hostname-based or from config)
- ✅ **Device ID-based linking** - Browser discovers `device_id` from local agent
- ✅ **Hardware detection** - Still collects hardware info for display (not for identification)

---

### 3. Location Tracking Flow

```
┌─────────────────────────┐
│ Agent Location Loop     │
│ (Every 15-60 seconds)   │
└──────┬──────────────────┘
       │
       ├──► Try GPS First
       │    ├─ Success? → Use GPS coordinates
       │    └─ Failed? → Try WiFi
       │
       ├──► Try WiFi Geolocation
       │    ├─ Scan WiFi networks
       │    ├─ Query Google Geolocation API
       │    ├─ Success? → Use WiFi coordinates
       │    └─ Failed? → Try GeoIP
       │
       └──► Try GeoIP (Last Resort)
            ├─ Get public IP address
            ├─ Query GeoIP service
            └─ Use IP-based location
       │
       ▼
┌─────────────────────────┐
│ POST /api/update_location│
│ - device_id             │
│ - lat, lng              │
│ - accuracy              │
│ - method (gps/wifi/ip)  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend Updates Device  │
│ (Supabase)              │
│ - last_lat, last_lng    │
│ - last_location_update   │
│ - Creates ActivityLog    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend Polls Status   │
│ GET /api/get_device_    │
│ status/:id              │
│ (Every 5 seconds)       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Update Google Map       │
│ - Move marker           │
│ - Show "Last seen"      │
│ - Display accuracy      │
└─────────────────────────┘
```

---

### 4. Remote Action Flow (Lock/Alarm/Wipe)

```
┌─────────────────────────┐
│ User Clicks Action       │
│ Button in Dashboard     │
│ (Lock/Alarm/Wipe)       │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ POST /api/trigger_action│
│ - device_id             │
│ - action: "lock"        │
│ - password: "..."       │
│ - message: "..."        │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend Stores Command  │
│ (Supabase)              │
│ - Save to database      │
│ - Create ActivityLog    │
│ - Set status: "pending" │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Agent Polls for Commands│
│ GET /api/get_commands   │
│ ?device_id=...          │
│ (Every 60 seconds)      │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Agent Receives Command  │
│ - Finds pending "lock"  │
│ - Executes locally      │
│   • lock_screen.py      │
│   • Block Task Manager  │
│   • Show lock message   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Agent Reports Status    │
│ POST /api/update_status │
│ - action: "lock"        │
│ - status: "executed"    │
│ - timestamp             │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Frontend Updates UI     │
│ - Show "Device Locked"  │
│ - Update activity log   │
│ - Refresh device status │
└─────────────────────────┘
```

---

### 5. Geofencing Flow

```
┌─────────────────────────┐
│ User Sets Geofence      │
│ - Select location on map│
│ - Set radius (meters)   │
│ - Choose type (GPS/WiFi)│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ POST /api/set_geofence   │
│ - device_id             │
│ - center_lat, center_lng│
│ - radius_m              │
│ - geofence_type         │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Backend Saves Geofence  │
│ Settings to Device       │
│ (Supabase)              │
│ - geofence_enabled=true │
│ - Stores center & radius│
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Background Scheduler     │
│ Checks Every 5 Minutes  │
│ - Get device location   │
│ - Calculate distance     │
│ - Check if outside zone  │
└──────┬──────────────────┘
       │
       ├──► Inside Zone? → Continue monitoring
       │
       └──► Outside Zone? → Breach Detected
            │
            ▼
┌─────────────────────────┐
│ Trigger Alert           │
│ - Send email alert      │
│ - Create ActivityLog    │
│ - Update device status  │
└─────────────────────────┘
```

---

## 📊 Database Schema (Supabase PostgreSQL)

### Core Tables

**users:**
- `id` (Primary Key)
- `email` (Unique, Indexed)
- `password_hash`
- `name`
- `is_admin` (Boolean)
- `email_verified` (Boolean) - **Verified account flag**
- `verification_code` (6 digits) - **Email verification code**
- `verification_code_expires` (DateTime) - **Code expiration**
- `created_at`

**devices:**
- `id` (Primary Key)
- `device_id` (Unique, Indexed) - **Primary identifier (no fingerprint_hash)**
- `name`
- `device_type` (os_device, agent_device, etc.)
- `user_id` (Foreign Key, Nullable for unowned devices)
- `status` (active, missing, locked, wiped)
- `os_name`, `os_version`, `architecture`
- `hardware_info` (CPU, RAM, GPU, motherboard, BIOS, serial numbers)
- `last_lat`, `last_lng`
- `last_location_update`
- `last_seen`
- `battery_percentage`
- `geofence_center_lat`, `geofence_center_lng`
- `geofence_radius_m`
- `geofence_enabled`
- `geofence_type` (gps, wifi)
- `geofence_wifi_ssid`
- `current_wifi_ssid`
- `created_at`, `registered_at`

**activity_logs:**
- `id` (Primary Key)
- `device_id` (Foreign Key)
- `action` (location_update, lock, alarm, wipe, screenshot)
- `description`
- `lat`, `lng`
- `screenshot_path`
- `created_at`

**breach_reports:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `email`
- `breach_name`
- `severity` (low, medium, high, critical)
- `date_detected`
- `description`
- `is_resolved`

**automation_rules:**
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `device_id` (Foreign Key, Nullable)
- `rule_type` (geofence, inactivity, breach_check)
- `is_enabled`
- `config` (JSON)
- `created_at`

**wipe_operations:**
- `id` (Primary Key)
- `device_id` (Foreign Key)
- `user_id` (Foreign Key)
- `folders_to_wipe` (JSON array)
- `status` (pending, in_progress, completed, failed)
- `progress_percentage` (0-100)
- `files_deleted`, `total_files`
- `error_message`
- `started_at`, `completed_at`, `created_at`

---

## 🔑 Core Features

### 1. **Device Registration & Management**

**Agent-First Registration:**
- Devices register before user accounts exist (unowned devices)
- Uses `device_id` for identification (hostname-based or from config)
- Hardware detection for display (not for identification)
- Automatic device linking when users log in
- Support for multiple device types (laptop, desktop, mobile, tablet)

**Device Types:**
- `os_device`: Browser-detected device (limited functionality)
- `agent_device`: Full-featured agent-installed device
- Hardware-detected devices with full system information

**Device Linking:**
- Browser discovers local agent via `http://127.0.0.1:9123/device-info`
- Returns `device_id` only (no fingerprint)
- Frontend sends `device_id` to backend on login/registration
- Backend links unowned device to user account

---

### 2. **Email Verification (Verified Account)**

**Flow:**
1. User registers → receives 6-digit verification code via email
2. Code expires in 15 minutes
3. User enters code on Verify Email page
4. Backend verifies code and sets `email_verified = true`
5. User gets JWT token and full access

**Features:**
- 6-digit numeric codes
- 15-minute expiration
- Resend verification code option
- Unverified accounts cannot access dashboard
- Admin accounts auto-verified

---

### 3. **Real-Time Location Tracking**

**Location Methods (Priority Order):**
1. GPS (Windows Location Services, iOS CoreLocation)
2. WiFi-based geolocation (Google Geolocation API)
3. GeoIP fallback (IP-based location)

**Features:**
- Updates every 15-60 seconds (configurable)
- Accuracy tracking (GPS > WiFi > GeoIP)
- Location history in activity logs
- Google Maps integration for visualization
- Stores in Supabase database

---

### 4. **Remote Actions**

**Lock:**
- Screen lock with custom password
- Task Manager blocking
- Custom lock message display
- Persistent lock until unlock command

**Alarm:**
- Sound alert loop
- Visual notifications
- Configurable duration
- Remote stop capability

**Wipe:**
- Selective folder deletion
- User-approved folders only
- Progress tracking
- File count reporting
- Safe wipe with confirmation

**Screenshot:**
- Screen capture capability
- Automatic upload to backend
- Activity log integration

---

### 5. **Geofencing**

**GPS Geofencing:**
- Circular boundaries (center + radius)
- Entry/exit detection
- Real-time monitoring (every 5 minutes)
- Email alerts on breach

**WiFi Geofencing:**
- SSID-based boundaries
- Automatic detection when device connects/disconnects
- Works indoors where GPS may fail

---

### 6. **Security Breach Detection**

**Integration with HaveIBeenPwned API:**
- Email breach checking
- Severity classification (low, medium, high, critical)
- Automatic weekly scans
- Email alerts for new breaches
- Breach resolution tracking

---

### 7. **Activity Logging**

**Comprehensive Audit Trail:**
- All device actions logged
- Location updates tracked
- Remote commands recorded
- Timestamp and user attribution
- Searchable history
- Stored in Supabase

---

### 8. **Automation Rules**

**Automated Security Responses:**
- Geofence breach alerts
- Inactivity detection
- Scheduled breach checks
- Custom automation rules
- Email notifications

---

## 🔐 Security Features

### Authentication Security

- JWT tokens with 24-hour expiration
- Password hashing using Werkzeug
- **Email verification** (6-digit codes, 15-minute expiration)
- Google OAuth integration
- Token refresh mechanism

### Device Security

- **Device ID-based identification** (no fingerprinting)
- Unique device IDs (hostname-based or config)
- Device ownership verification
- One device per user enforcement

### Data Protection

- Remote wipe with user approval
- Secure command execution
- Activity logging for audit trail
- HTTPS communication (production)
- **Supabase database** (encrypted at rest)

---

## 🚀 Deployment Architecture

### Production Deployment

**Backend (Vercel):**
- Serverless functions
- **Supabase PostgreSQL database** (via `DATABASE_URL`)
- Environment variables for configuration
- Automatic scaling

**Frontend (Vercel):**
- Static site hosting
- Environment variables for API URLs
- Google Maps API integration
- CDN distribution

**Agent:**
- Runs locally on devices
- Can be installed as Windows service
- Background process
- Auto-start on login

### Local Development

- SQLite database for local testing
- Flask development server
- Vite dev server with hot reload
- Agent runs in foreground for debugging

---

## 📝 API Endpoints Summary

### Authentication Endpoints

- `POST /api/register_user` - Register new user (creates unverified account)
- `POST /api/login` - Authenticate and get JWT token
- `POST /api/verify_email` - Verify email with 6-digit code
- `POST /api/resend_verification` - Resend verification code
- `POST /api/google_login` - Google OAuth authentication
- `GET /api/me` - Get current user info

### Device Endpoints

- `POST /api/devices/agent/register` - Agent-first device registration
- `POST /api/update_location` - Update device location (agent)
- `GET /api/get_devices` - Get all user devices
- `GET /api/get_device_status/:id` - Get device details
- `POST /api/trigger_action` - Execute remote action
- `POST /api/mark_as_missing` - Mark device as missing
- `GET /api/get_activity_logs/:id` - Get device activity history
- `POST /api/set_geofence` - Configure geofence

### Breach Detection Endpoints

- `GET /api/detect_breach` - Check for email breaches
- `GET /api/get_breach_reports` - Get all breach reports
- `POST /api/mark_breach_resolved` - Mark breach as resolved

### Automation Endpoints

- `POST /api/automation_task` - Create automation rule
- `GET /api/automation_tasks` - Get all automation rules
- `PUT /api/automation_task/:id` - Update automation rule
- `DELETE /api/automation_task/:id` - Delete automation rule

---

## 🔄 Background Jobs & Automation

### Scheduled Tasks

**Daily Status Update (00:00 UTC):**
- Marks devices inactive if not seen for >24 hours
- Updates device status in Supabase

**Weekly Breach Check (Saturday 09:00 UTC):**
- Scans all user emails against HaveIBeenPwned
- Creates breach reports for new breaches
- Sends email alerts

**Weekly Summary (Sunday 09:00 UTC):**
- Sends email summary to all users
- Includes device stats, missing devices, breach alerts

**Geofence Check (Every 5 minutes):**
- Monitors all enabled geofence rules
- Detects entry/exit events
- Triggers email alerts on breach

---

## 📱 Frontend Pages & Components

### Main Pages

- **Dashboard:** Overview of all devices, quick stats, recent activity
- **Devices:** List of all devices, device cards, quick actions
- **DeviceDetail:** Detailed device view, map, activity logs, remote actions, geofencing, file browser
- **Login/SignUp:** Authentication pages with Google OAuth
- **VerifyEmail:** Email verification page (6-digit code entry)
- **QRScanner:** QR code scanner for iOS device connection
- **BreachReport:** Security breach reports and management
- **MissingMode:** Special mode when device is marked missing

### Key Components

- **DeviceCard:** Device status card with quick actions
- **MapView:** Google Maps integration for location display
- **FileBrowser:** Browse device filesystem (for wipe operations)
- **Navbar:** Navigation bar with user menu

---

## 🎯 Key Differences from Previous Version

### Removed Features

- ❌ **Hardware Fingerprinting** - Completely removed from system
- ❌ **fingerprint_hash** - No longer used for device identification
- ❌ **fingerprint.py** - File deleted from codebase

### New/Updated Features

- ✅ **Device ID Only** - Uses `device_id` for all device identification
- ✅ **Supabase Database** - Production uses Supabase PostgreSQL
- ✅ **Email Verification** - Verified account flow with 6-digit codes
- ✅ **Simplified Linking** - Browser discovers `device_id` from local agent

---

## 🔧 Configuration

### Environment Variables

**Backend (Vercel):**
- `DATABASE_URL` - Supabase PostgreSQL connection string (required for production)
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `SMTP_*` - Email configuration (for verification codes)

**Frontend:**
- `VITE_GOOGLE_MAPS_API_KEY` - Google Maps API key
- `VITE_API_BASE_URL` - Backend API URL

**Agent:**
- `API_BASE_URL` - Backend API URL (defaults to Vercel)
- `device_id` - Stored in `config.json` (auto-generated)
- `user_email` - User email for registration

---

## 📊 System Statistics

- **Database:** Supabase (PostgreSQL) for production
- **Device Identification:** `device_id` only (no fingerprinting)
- **Account Verification:** Email verification with 6-digit codes
- **Location Methods:** GPS → WiFi → GeoIP (priority order)
- **Update Intervals:** Location (15-60s), Commands (60s), Geofence (5min)
- **Supported Platforms:** Windows, Mac, Linux, iOS

---

## ✅ Summary

This system provides a complete anti-theft solution with:

1. **Simplified Device Identification** - Uses `device_id` only (no fingerprinting)
2. **Verified Accounts** - Email verification ensures account security
3. **Supabase Database** - Reliable PostgreSQL hosting for production
4. **Real-Time Tracking** - GPS, WiFi, and IP-based location tracking
5. **Remote Control** - Lock, alarm, and wipe capabilities
6. **Security Monitoring** - Breach detection and geofencing
7. **Comprehensive Logging** - Full audit trail of all activities

The system is production-ready, deployed on Vercel with Supabase, and provides enterprise-grade device security monitoring.

---

**Last Updated:** Latest version with fingerprinting removed, Supabase database, and email verification
**Status:** Production-ready, deployed on Vercel
