# 🛡️ Smart Anti-Theft System - Complete Project Analysis

## 📋 Project Overview

This is a **full-stack anti-theft and device security monitoring system** inspired by Prey Project. It provides real-time device tracking, remote control capabilities, and comprehensive security monitoring for Windows, Mac, Linux, and iOS devices.

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
│  Device Agents      │    │  Supabase (PostgreSQL)           │
│  (Python)           │    │  - Hosted PostgreSQL database   │
│  - agent.py         │    │  - users (email_verified,        │
│  - iOS agent        │    │    verification_code, etc.)      │
│  - Local discovery  │    │  - devices, activity_logs,       │
└─────────────────────┘    │    breach_reports, etc.          │
                           │  - Connection pooler for Vercel  │
                           └─────────────────────────────────┘
```

### Verified Account (Email Verification) Flow

```
┌─────────────┐     POST /api/register_user      ┌─────────────┐
│  User       │ ───────────────────────────────► │  Backend     │
│  (Sign Up)  │  email, password, name           │              │
└──────┬──────┘                                  └──────┬───────┘
       │                                                │
       │                                                │ Create user
       │                                                │ email_verified = false
       │                                                │ Send verification code (email)
       │                                                ▼
       │                                         ┌─────────────┐
       │                                         │  Supabase    │
       │                                         │  users row   │
       │                                         └──────┬───────┘
       │                                                │
       │  Redirect to /verify-email                     │
       │◄───────────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     POST /api/verify_email       ┌─────────────┐
│  Verify     │ ───────────────────────────────► │  Backend    │
│  Email page │  email, code                      │              │
└──────┬──────┘                                  └──────┬──────┘
       │                                                 │
       │                                                 │ Check code, set
       │                                                 │ email_verified = true
       │                                                 ▼
       │  JWT + redirect to dashboard            ┌─────────────┐
       │◄────────────────────────────────────────│  Verified   │
       │                                          │  Account    │
       │                                          └─────────────┘
       ▼
  Login allowed; full access to dashboard
```

## 📁 Project Structure

```
smart-antitheft-system/
│
├── backend/                    # Flask Backend API
│   ├── app.py                 # Flask app initialization
│   ├── models.py              # SQLAlchemy database models
│   ├── routes/                # API route handlers
│   │   ├── device_routes.py  # Device CRUD operations
│   │   ├── user_routes.py    # Authentication & user management
│   │   ├── breach_routes.py  # Breach detection endpoints
│   │   ├── automation_routes.py  # Automation rules
│   │   └── wipe_routes.py    # Data wipe operations
│   └── utils/                 # Utility modules
│       ├── email_alert.py     # Email notifications
│       ├── geofence.py        # Geofencing logic
│       └── scheduler.py       # Background jobs
│
├── frontend/                  # React Frontend
│   ├── src/
│   │   ├── pages/            # Main pages
│   │   │   ├── Dashboard.jsx  # Main dashboard
│   │   │   ├── Devices.jsx   # Device list & management
│   │   │   ├── DeviceDetail.jsx  # Individual device view
│   │   │   ├── Login.jsx     # Authentication
│   │   │   ├── QRScanner.jsx # QR code scanner for iOS
│   │   │   └── BreachReport.jsx  # Security breach reports
│   │   ├── components/       # Reusable components
│   │   │   ├── DeviceCard.jsx
│   │   │   ├── MapView.jsx   # Google Maps integration
│   │   │   ├── FileBrowser.jsx
│   │   │   └── Navbar.jsx
│   │   ├── api/              # API client
│   │   │   └── axios.js     # Axios configuration
│   │   └── utils/            # Utility functions
│   │       ├── deviceDetection.js  # Browser device detection
│   │       ├── deviceDiscovery.js  # Agent discovery
│   │       └── geolocation.js     # Location utilities
│   └── package.json
│
├── device_agent/              # Device Agents
│   ├── agent.py              # Main Windows/Mac/Linux agent
│   ├── ios_agent.py          # iOS agent (Pythonista)
│   ├── register_device.py    # Device registration script
│   ├── hardware_detection.py # Hardware detection (no fingerprinting)
│   ├── wifi_monitor.py       # WiFi monitoring
│   ├── lock_screen.py        # Screen lock implementation
│   ├── config.json           # Agent configuration
│   └── requirements.txt
│
├── database/                 # SQLite (local dev only)
│   └── antitheft.db          # Production uses Supabase (PostgreSQL)
│
├── docs/                     # Documentation
│   ├── PREY_SYSTEM_ANALYSIS.md  # Prey Project analysis
│   └── PROJECT_ANALYSIS.md     # This file
│
├── start_all.bat            # Windows startup script
├── start_all.ps1             # PowerShell startup script
├── start_all.py              # Cross-platform startup
└── README.md                 # Main documentation
```

## 🔑 Core Components

### 1. Backend (Flask)

#### Database Models (`backend/models.py`)

**User Model:**
- Email, password (hashed), name
- Admin flag
- Relationships: devices, breach_reports

**Device Model:**
- Comprehensive device information:
  - OS details (name, version, architecture)
  - Hardware (CPU, RAM, GPU, motherboard, BIOS)
  - Browser information
  - Location data (lat/lng, WiFi SSID)
  - Geofencing settings
  - Status (active, missing, locked, wiped)
  - Fingerprint hash for device identification
  - Connection key (for device linking)

**ActivityLog Model:**
- Tracks all device activities
- Action types, descriptions, timestamps

**BreachReport Model:**
- Security breach detection results
- Integration with HaveIBeenPwned API

**AutomationTask Model:**
- Automated rules (geofencing, breach alerts, etc.)

**WipeTask Model:**
- Data wipe operations tracking

#### API Routes

**Authentication (`user_routes.py`):**
- `POST /api/register_user` - User registration
- `POST /api/login` - JWT authentication
- `GET /api/me` - Current user info

**Devices (`device_routes.py`):**
- `POST /api/register_device` - Register new device
- `POST /api/update_location` - Update device location (agent)
- `GET /api/get_devices` - Get user's devices
- `GET /api/get_device_status/:id` - Device details
- `POST /api/trigger_action` - Remote actions (lock/alarm/wipe)
- `POST /api/mark_as_missing` - Mark device as missing
- `GET /api/get_activity_logs` - Activity history

**Breach Detection (`breach_routes.py`):**
- `GET /api/detect_breach` - Check for breaches
- `GET /api/get_breach_reports` - Get breach reports

**Automation (`automation_routes.py`):**
- CRUD operations for automation rules

**Wipe Operations (`wipe_routes.py`):**
- Data wipe task management

#### Background Jobs (`utils/scheduler.py`)

- **Daily Status Update**: Marks inactive devices (>24h)
- **Weekly Breach Check**: Scans all users for breaches
- **Weekly Summary**: Email summary to all users
- **Geofence Check**: Monitors geofence rules every 5 minutes

### 2. Frontend (React + Vite)

#### Key Pages

**Dashboard (`Dashboard.jsx`):**
- Overview of all devices
- Quick stats and status
- Recent activity

**Devices (`Devices.jsx`):**
- List of all user devices
- Device cards with status
- Quick actions (lock, alarm, wipe)
- Device discovery (for agent-first registration)

**DeviceDetail (`DeviceDetail.jsx`):**
- Comprehensive device view
- Real-time location on map
- Activity logs
- Remote actions
- Geofencing configuration
- File browser
- Settings management

**QRScanner (`QRScanner.jsx`):**
- QR code scanning for iOS device connection
- Manual connection key entry

**Login/SignUp:**
- JWT-based authentication
- Token stored in localStorage

#### Key Features

- **Google Maps Integration**: Real-time location tracking
- **Device Discovery**: Automatic agent detection via local HTTP server
- **Real-time Updates**: Polling for device status
- **Responsive Design**: Tailwind CSS styling

### 3. Device Agent (`device_agent/agent.py`)

#### Core Functionality

**Agent-First Registration:**
- Device registers itself BEFORE user account exists
- Creates "unowned" device in database
- Frontend automatically links device when user logs in

**Status Reporting:**
- Periodic status updates to backend
- Location tracking (GPS, WiFi, GeoIP)
- Hardware information
- Battery status
- WiFi SSID monitoring

**Command Execution:**
- Polls backend for pending commands
- Executes remote actions:
  - **Lock**: Screen lock with password
  - **Alarm**: Sound alert loop
  - **Wipe**: Delete specified files/folders
  - **Screenshot**: Capture screen
  - **Location**: Force location update

**Local HTTP Server:**
- Runs on `http://localhost:5001` (or configurable)
- Allows browser to discover agent
- Enables automatic device linking

**Hardware Fingerprinting:**
- Unique device identification
- Prevents duplicate registrations
- Hardware-based device matching

**WiFi Monitoring:**
- Current WiFi SSID tracking
- WiFi-based geofencing support
- Signal strength monitoring

#### Configuration (`config.json`)

```json
{
  "device_id": "unique-device-id",
  "user_email": null,  // null for unowned devices
  "report_interval": 300,  // Status update interval (seconds)
  "check_commands_interval": 60,  // Command polling interval
  "api_base_url": "https://antitheft-backend.vercel.app/api",
  "local_server_port": 5001
}
```

### 4. iOS Agent (`device_agent/ios_agent.py`)

- Runs in Pythonista app on iPhone/iPad
- Similar functionality to main agent
- iOS-specific location APIs
- QR code connection workflow

## 🔄 System Workflows

### Device Registration Flow

#### Agent-First Registration (Current Implementation)

1. **Agent Starts:**
   - Agent runs `agent.py` on device
   - Checks for existing `config.json`
   - If no config, registers with backend using device_id (hostname-based or from config)
   - Registers device as "unowned" (user_id = null)

2. **Device Registration:**
   - Agent sends registration request to backend
   - Backend creates device record with:
     - Unique device_id
     - Fingerprint hash
     - Hardware information
     - user_id = null (unowned)

3. **User Login:**
   - User logs in to frontend
   - Frontend checks for local agent (via HTTP server)
   - If agent found, automatically links device to user
   - Device becomes "owned" by logged-in user

4. **Manual Linking (Alternative):**
   - User can manually link device via QR code
   - Or enter connection key manually

#### Browser-Based Registration (Legacy)

1. User opens frontend in browser
2. Browser detects device via JavaScript
3. Device registered with browser metadata
4. Agent can later connect via connection key

### Remote Action Flow

1. **User Triggers Action:**
   - User clicks "Lock" or "Alarm" in frontend
   - Frontend sends POST to `/api/trigger_action`

2. **Backend Stores Command:**
   - Command stored in database
   - Activity log created

3. **Agent Polls for Commands:**
   - Agent periodically checks `/api/get_commands`
   - Retrieves pending commands

4. **Agent Executes:**
   - Agent executes command locally
   - Sends status update back to backend

5. **Frontend Updates:**
   - Frontend polls for status updates
   - Shows action result to user

### Location Tracking Flow

1. **Agent Collects Location:**
   - Tries GPS first (Windows Location Services)
   - Falls back to WiFi-based location
   - Last resort: GeoIP

2. **Agent Reports Location:**
   - Sends location update to backend
   - Updates device record

3. **Frontend Displays:**
   - Fetches latest location
   - Displays on Google Maps
   - Updates every 5 seconds

### Geofencing Flow

1. **User Sets Geofence:**
   - User selects location on map
   - Sets radius or WiFi SSID
   - Enables geofencing

2. **Background Job Monitors:**
   - Scheduler checks geofence rules every 5 minutes
   - Compares device location to geofence
   - Detects entry/exit events

3. **Alert Triggered:**
   - Email alert sent
   - Activity log created
   - Frontend notification

## 🔐 Security Features

### Authentication
- JWT tokens for API authentication
- Password hashing (Werkzeug)
- Token expiration (24 hours)

### Device Security
- Hardware detection (vendor, model, CPU, RAM, etc.)
- Unique device IDs
- Connection keys for linking (optional)

### Data Protection
- Remote wipe capabilities
- File deletion with confirmation
- Secure command execution

## 📊 Database Schema

### Key Tables

**users:**
- id, email, password_hash, name, is_admin
- email_verified (boolean), verification_code, verification_code_expires (verified account flow)

**devices:**
- id, device_id, name, device_type
- os_name, os_version, architecture
- hardware fields (CPU, RAM, GPU, etc.)
- location fields (lat, lng, WiFi SSID)
- geofence settings
- user_id (nullable for unowned devices)
- status, last_seen, battery_percentage

**activity_logs:**
- id, device_id, action, description, timestamp

**breach_reports:**
- id, user_id, email, breach_name, severity

**automation_tasks:**
- id, user_id, task_type, conditions, actions

**wipe_tasks:**
- id, device_id, paths, status, created_at

## 🚀 Deployment

### Backend (Vercel)
- Serverless functions
- **Supabase** (PostgreSQL) for production (Vercel); set `DATABASE_URL` to Supabase connection string
- SQLite for local development

### Frontend (Vercel)
- Static site hosting
- Environment variables for API URLs
- Google Maps API key

### Agent
- Runs locally on device
- Can be installed as Windows service
- Background process

## 🔧 Configuration

### Environment Variables

**Backend:**
- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `SMTP_*` - Email configuration

**Frontend:**
- `VITE_GOOGLE_MAPS_API_KEY` - Google Maps API key
- `VITE_API_BASE_URL` - Backend API URL

**Agent:**
- `API_BASE_URL` - Backend API URL (defaults to Vercel)

## 📝 Current Issues & Solutions

### Device Linking Issue (FIX_DEVICE_LINKING.md)

**Problem:**
- Device exists but not accessible
- Linked to different user account
- Frontend shows "Device not found"

**Solutions:**
1. Log in with correct email (admin@antitheft.com)
2. Re-link device via login (agent makes device unowned)
3. Re-register device as unowned

### Location Accuracy

- Agent prioritizes GPS over WiFi/GeoIP
- Clears cached wrong locations on startup
- Windows Location Services integration

## 🎯 Key Features

1. **Real-time Tracking**: GPS, WiFi, and IP-based location
2. **Remote Control**: Lock, alarm, wipe devices
3. **Geofencing**: GPS and WiFi-based boundaries
4. **Breach Detection**: HaveIBeenPwned integration
5. **Activity Logging**: Comprehensive audit trail
6. **Multi-Platform**: Windows, Mac, Linux, iOS
7. **Agent-First**: Devices register before user accounts
8. **Automatic Discovery**: Browser finds local agent
9. **Hardware Fingerprinting**: Unique device identification
10. **Background Monitoring**: Continuous status reporting

## 🔄 Integration with Prey Project

The system is inspired by Prey Project and can coexist with it:
- Prey runs at `C:\Windows\Prey\`
- This system runs independently
- Both can track the same device
- Different APIs and control panels

## 📚 Documentation Files

- `README.md` - Main project documentation
- `FIX_DEVICE_LINKING.md` - Device linking troubleshooting
- `docs/PREY_SYSTEM_ANALYSIS.md` - Prey Project analysis
- `docs/PROJECT_ANALYSIS.md` - This file
- Various setup and deployment guides

## 🛠️ Development Workflow

1. **Start Services:**
   ```bash
   # Windows
   start_all.bat
   
   # Or manually
   cd backend && python app.py
   cd frontend && npm run dev
   cd device_agent && python agent.py
   ```

2. **Access Points:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000
   - Agent: Runs in background

3. **Default Credentials:**
   - Email: admin@antitheft.com
   - Password: admin123

## 🎓 Learning Points

- **Agent-First Architecture**: Devices register independently
- **Device Discovery**: Local HTTP server for browser-agent communication
- **Hardware Fingerprinting**: Unique device identification
- **Geofencing**: Multiple strategies (GPS, WiFi)
- **Remote Actions**: Command queue pattern
- **Real-time Updates**: Polling-based status updates
- **Multi-Platform Support**: Cross-platform agent implementation

---

**Last Updated:** Based on current codebase analysis
**Status:** Active development, deployed on Vercel
