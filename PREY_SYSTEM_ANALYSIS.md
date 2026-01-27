# Prey Anti-Theft System - Complete System Analysis

## Overview

Prey is an anti-theft tracking and monitoring application for laptops, smartphones, and other devices. This document provides a comprehensive analysis of the Prey system installed at `C:\Windows\Prey`, including its architecture, core components, and all major functions.

**Version Analyzed:** 1.13.25  
**Installation Path:** `C:\Windows\Prey`  
**Control Panel:** `solid.preyproject.com` (HTTPS)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Prey Agent (Node.js)                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Commands   │  │   Actions    │  │  Providers   │      │
│  │   Handler    │  │   Executor   │  │  (Data Get)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Reports    │  │   Triggers   │  │   Hooks      │      │
│  │   Generator  │  │   Watcher    │  │   System     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Control Panel Communication Layer             │  │
│  │  - WebSocket Connection                                │  │
│  │  - HTTP API                                            │  │
│  │  - Long Polling (fallback)                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │ Actions │          │ System │          │ Storage │
    │ (Lock,  │          │ Info   │          │ (SQLite)│
    │ Alarm,  │          │        │          │         │
    │ Wipe)   │          │        │          │         │
    └─────────┘          └─────────┘          └─────────┘
```

---

## Core Components

### 1. Main Entry Point (`lib/common.js`)

**Purpose:** Initializes the system and provides common utilities.

**Key Exports:**
- `package` - Package information
- `exceptions` - Error handling
- `system` - OS-specific system utilities
- `config_path` - Configuration file path
- `pid_file` - Process ID file location
- `root_path` - Root installation directory

**Configuration File:** `prey.conf` located at system-specific config path

---

### 2. Agent Core (`lib/agent/index.js`)

**Purpose:** Main agent orchestrator that coordinates all subsystems.

**Key Functions:**

#### `run()`
- Main entry point for the agent
- Loads configuration
- Initializes storage
- Checks for updates
- Boots the system
- Sets process title to 'prx' (stealth mode)

#### `boot()`
- Initializes control panel connection
- Runs stored commands from database
- Starts command watching
- Enables auto-update checking (every 3 hours)
- Watches system triggers

#### `shutdown()`
- Stops all actions
- Unloads hooks
- Cancels all reports
- Unwatches triggers
- Cleans temporary files

#### `reload()`
- Reloads configuration without full restart

**State Management:**
- `running` - Boolean flag indicating if agent is active
- `startedAt` - Timestamp when agent started
- `runningAs` - User account running the agent

---

### 3. Commands System (`lib/agent/commands.js`)

**Purpose:** Handles remote commands from the control panel.

**Command Types:**
- `start` - Start an action (alarm, lock, wipe, etc.)
- `stop` - Stop a running action
- `watch` - Start watching a trigger
- `unwatch` - Stop watching a trigger
- `get` - Get data from providers (location, screenshot, etc.)
- `report` - Generate and send reports
- `cancel` - Cancel a report
- `upgrade` - Check for updates

**Key Functions:**

#### `parse(body)`
Parses text commands into structured command objects. Supports:
- `start <action> [with options]`
- `stop <action>`
- `get <provider>`
- `watch <trigger>`
- `report <type> [interval: X]`

#### `perform(command)`
Executes a command object:
- Validates command structure
- Generates UUID for command ID
- Routes to appropriate handler (actions, providers, reports, etc.)
- Stores command in database for persistence
- Handles special cases (missing/recovered device, full wipe)

#### `run_stored()`
Restores and re-executes commands stored in database after restart

#### `start_watching()`
Enables command persistence - stores commands to database

**Command Storage:**
- Commands stored in SQLite database (`commands.db`)
- Persists across restarts
- Tracks execution status (started/stopped timestamps)

---

### 4. Actions System (`lib/agent/actions.js`)

**Purpose:** Executes security actions on the device.

**Available Actions:**

#### Alarm (`actions/alarm/`)
- Plays alarm sound (alarm.mp3, siren.mp3, ring.mp3, modem.mp3)
- Raises system volume
- Configurable loops
- Platform-specific implementations (Windows, Mac, Linux)

#### Lock (`actions/lock/`)
- Locks device screen
- Requires unlock password
- Blocks escape mechanisms (Task Manager, etc. on Windows)
- Disables touchpad during lock
- Supports custom lock messages
- Auto-restarts if window loses focus

#### Wipe (`actions/wipe/`)
- Clears browser data (IE, Chrome, Firefox)
- Deletes Outlook profiles
- Removes Dropbox directories
- Kills specific processes
- Windows-specific implementation

#### Full Wipe (`actions/fullwipe/`)
- Complete disk wipe using `dskwipe.exe`
- Destructive action - cannot be undone

#### Factory Reset (`actions/factoryreset/`)
- Resets device to factory settings
- Uses PowerShell script on Windows
- Provides status feedback

#### File Retrieval (`actions/fileretrieval/`)
- Uploads files to control panel
- Checks for pending file uploads
- Handles file transfers

#### Disk Encryption (`actions/diskencryption/`)
- Checks encryption status
- Retrieves encryption keys (TPM module)

#### Alert (`actions/alert/`)
- Visual alerts (flash.exe on Windows)

#### Log Retrieval (`actions/logretrieval/`)
- Collects and uploads system logs

#### OSQuery (`actions/osquery/`)
- Executes OSQuery commands

**Action Lifecycle:**
1. `start(id, name, opts, cb)` - Starts action
2. Action runs and emits events
3. `stop(id, name, opts)` - Stops action
4. Events: `started`, `stopped`, `failed`

**Action Events:**
- Actions can emit custom events (e.g., `failed_unlock_attempt` from lock)
- Events are forwarded to hooks system

---

### 5. Providers System (`lib/agent/providers.js`)

**Purpose:** Retrieves device information and data.

**Available Providers:**

#### Location (`providers/geo/`)
- **Windows:** Uses Windows.Devices.Geolocation API
- **Strategies:**
  - WiFi-based location
  - GeoIP fallback
  - GPS (if available)
- Returns: latitude, longitude, accuracy, address

#### Screenshot (`providers/screenshot/`)
- **Windows:** Uses `preyshot.exe`
- Captures current screen
- Returns: Image file path

#### Webcam (`providers/webcam/`)
- **Windows:** Uses `prey-webcam.exe` or `snapshot.exe`
- Captures photo from webcam
- Returns: Image file path

#### Hardware (`providers/hardware/`)
- System specifications
- RAM modules
- Processor info
- Firmware info
- TPM module status
- OS edition
- Windows service version

#### Network (`providers/network/`)
- Connection status
- WiFi networks
- IP addresses
- Network interfaces

#### Users (`providers/users/`)
- Currently logged users
- User accounts

#### Processes (`providers/processes/`)
- Running processes list

#### Files (`providers/files/`)
- File tree structure
- File attributes
- File finder

#### LAN (`providers/lan/`)
- Active network nodes
- Network discovery

#### Bandwidth (`providers/bandwidth/`)
- Network usage statistics

#### Connections (`providers/connections/`)
- Active network connections

#### Indicators (`providers/indicators/`)
- System status indicators

#### System (`providers/system/`)
- General system information

**Provider Function Pattern:**
```javascript
exports.get_<name> = function(options, callback) {
  // Fetch data
  callback(null, result);
}
```

**Provider Usage:**
- Called via `providers.get(name, options, callback)`
- Results trigger `data` hook event
- Files are tracked for cleanup

---

### 6. Reports System (`lib/agent/reports.js`)

**Purpose:** Generates comprehensive device reports.

**Report Types:**

#### Stolen Report (`reports/stolen.js`)
- Comprehensive device information
- Location, screenshot, webcam photo
- Network information
- Hardware specs
- Can be scheduled at intervals

#### Status Report (`reports/status.js`)
- Current device status
- Battery info
- Logged user
- Connection status

#### Specs Report (`reports/specs.js`)
- Hardware specifications
- System information
- TPM module (if available)

#### Actions Report (`reports/actions.js`)
- History of executed actions

#### Load Report (`reports/load.js`)
- System load information

**Report Generation:**
1. `get(reportName, options, callback)` - Generates report
2. Gathers data from multiple providers
3. Combines into single report object
4. Sends to control panel via hooks

**Scheduled Reports:**
- Reports can be queued with intervals
- Automatically enables `auto_connect` when scheduled
- Interval specified in minutes (converted to milliseconds)

**Report Includes:**
Each report type defines what data to include:
- `stolen`: location, screenshot, picture, network, hardware, etc.
- `status`: battery, user, connection, etc.
- `specs`: hardware, system, tpm_module, etc.

---

### 7. Triggers System (`lib/agent/triggers.js`)

**Purpose:** Monitors system events and triggers actions.

**Available Triggers:**

#### Connection (`triggers/connection/`)
- Monitors network connection changes
- Triggers on connect/disconnect

#### Location (`triggers/location/`)
- Monitors location changes
- Triggers on significant location change

#### Network (`triggers/network/`)
- Monitors network interface changes
- WiFi connection changes

#### Power (`triggers/power/`)
- Monitors power state (AC/battery)
- Low battery events

#### Status (`triggers/status/`)
- Periodic status checks
- Device status updates

#### Hostname (`triggers/hostname/`)
- Monitors hostname changes

#### Auto-Connect (`triggers/auto-connect/`)
- Automatically connects to WiFi when offline
- Uses `wifion.exe` and `ManagedWifi.dll` on Windows

**Trigger Lifecycle:**
1. `add(triggerName, opts)` - Starts watching trigger
2. Trigger monitors system events
3. Emits events when conditions met
4. `remove(triggerName)` - Stops watching

**Trigger Events:**
- Triggers emit events that can be listened to
- Events forwarded to hooks system

---

### 8. Control Panel Communication (`lib/agent/control-panel/`)

**Purpose:** Manages communication with Prey control panel server.

#### WebSocket Connection (`control-panel/websockets/index.js`)

**Connection Management:**
- Establishes WebSocket connection to `wss://solid.preyproject.com/api/v2/devices/{device_key}.ws`
- Uses Basic Authentication (API key)
- Supports HTTP proxy
- Auto-reconnects on disconnect
- Heartbeat mechanism (ping/pong every 60 seconds)

**Message Types:**

1. **Device Status** (`device_status`)
   - Sent every 5 minutes
   - Includes: battery, user, connection, etc.

2. **Action Response** (`response`)
   - Notifies action start/stop/failure
   - Includes action details and results

3. **Commands** (received)
   - Array of command objects
   - Processed with delays to prevent overload

4. **Acknowledgments** (`ack`)
   - Confirms command receipt
   - Tracks command processing

**Features:**
- Queues responses if connection lost
- Retries failed messages (max 10 retries)
- Stores responses in database for persistence
- Groups commands by structure to prevent duplicates
- Sends location on connect (if configured)

#### HTTP API (`control-panel/api/`)

**Endpoints:**
- `devices.get.status()` - Get device status from server
- `devices.post_missing()` - Mark device as missing/recovered
- `devices.unlink()` - Unlink device from account

**Request Handling:**
- Uses `needle` library for HTTP requests
- Supports proxy configuration
- Handles authentication
- Error handling and retries

#### Setup (`control-panel/setup.js`)
- Device registration
- API key validation
- Device key generation

#### Sender (`control-panel/sender.js`)
- Sends reports to control panel
- Handles data transmission
- Error handling

#### Secure (`control-panel/secure.js`)
- Key generation and management
- Encryption utilities

---

### 9. Hooks System (`lib/agent/hooks.js`)

**Purpose:** Event-driven communication between components.

**Hook Events:**
- `action` - Action lifecycle events (started, stopped, failed)
- `event` - Generic events from actions/triggers
- `data` - Data from providers
- `report` - Report generation events
- `error` - Error events
- `command` - Command processing events
- `connected` - WebSocket connected
- `device_unseen` - Device not seen by server
- `disconnected` - Network disconnected
- `get_location` - Request location
- `new_location` - Location obtained

**Usage:**
```javascript
hooks.on('action', (event, id, name, opts, err, out) => {
  // Handle action event
});

hooks.trigger('data', 'location', locationData);
```

---

### 10. Storage System (`lib/agent/utils/storage/`)

**Purpose:** Persistent data storage using SQLite.

**Storage Types:**
- `commands` - Stored commands
- `responses` - Action responses
- `keys` - Key-value storage
- `triggers` - Trigger configurations

**Operations:**
- `set` - Store data
- `get` - Retrieve data
- `query` - Query with conditions
- `update` - Update existing data
- `del` - Delete data
- `all` - Get all records

**Database:** `commands.db` in config directory

---

### 11. Updater System (`lib/agent/updater.js`)

**Purpose:** Handles automatic updates.

**Features:**
- Checks for updates every 3 hours (if enabled)
- Downloads and installs updates
- Supports edge releases
- Version comparison
- Update notifications

---

### 12. Windows-Specific Components

#### Windows Service (`wpxsvc.exe`)
- Runs as Windows service
- Provides elevated privileges
- Handles system-level operations

#### Windows System Utilities (`lib/system/windows/`)
- `get_os_edition()` - Windows edition (Pro, Enterprise, etc.)
- `get_winsvc_version()` - Windows service version
- `get_running_user()` - Current user
- `run_as_logged_user()` - Execute as logged user
- `spawn_as_logged_user()` - Spawn process as logged user
- `spawn_as_admin_user()` - Spawn with admin privileges

#### Windows Binaries (`lib/system/windows/bin/`)
- `wpxsvc.exe` - Windows service
- `autowc.exe` - Auto WiFi connect
- `safexec.exe` - Safe execution
- `wlanscan.exe` - WiFi scanning
- `wapi.dll` - Windows API library
- `wzcapis.dll` - WiFi APIs

---

## Configuration System

### Configuration File (`prey.conf`)

**Location:** System-specific config directory (Windows: `C:\Windows\Prey\`)

**Key Settings:**
```ini
# Connection
auto_connect = true/false          # Auto-connect to WiFi
try_proxy = http://proxy:port     # HTTP proxy

# Updates
auto_update = true/false          # Enable auto-updates
download_edge = true/false        # Download edge releases

# Control Panel
[control-panel]
host = solid.preyproject.com
protocol = https
api_key = <your-api-key>
device_key = <your-device-key>
send_status_info = true
location_aware = true
scan_hardware = true/false

# Reporting
send_crash_reports = true/false
```

**Configuration Management:**
- Loaded via `configfile.js`
- Can be updated via control panel
- Settings synced from server
- Supports nested keys (e.g., `control-panel.api_key`)

---

## Communication Flow

### 1. Initialization Flow

```
1. Agent starts (lib/agent/index.js::run())
   ↓
2. Load configuration (prey.conf)
   ↓
3. Initialize storage (SQLite database)
   ↓
4. Check for updates
   ↓
5. Initialize control panel connection
   ↓
6. Load stored commands from database
   ↓
7. Start watching triggers
   ↓
8. Establish WebSocket connection
   ↓
9. Send initial status
   ↓
10. Ready to receive commands
```

### 2. Command Execution Flow

```
1. Control panel sends command via WebSocket
   ↓
2. WebSocket receives message
   ↓
3. Commands.perform() processes command
   ↓
4. Command stored in database
   ↓
5. Route to appropriate handler:
   - actions.start() for actions
   - providers.get() for data
   - reports.get() for reports
   ↓
6. Execute action/get data
   ↓
7. Emit hooks events
   ↓
8. Send response via WebSocket
   ↓
9. Update command status in database
```

### 3. Report Generation Flow

```
1. Command: report stolen [interval: 20]
   ↓
2. Reports.get('stolen', {interval: 20})
   ↓
3. Determine report includes (location, screenshot, etc.)
   ↓
4. Queue report (if interval specified)
   ↓
5. Gather data from providers:
   - providers.get('location')
   - providers.get('screenshot')
   - providers.get('picture')
   - providers.get('network')
   - etc.
   ↓
6. Combine data into report object
   ↓
7. Trigger 'report' hook
   ↓
8. Sender sends to control panel
   ↓
9. Repeat at interval (if scheduled)
```

---

## Security Features

### 1. Stealth Mode
- Process title changed to 'prx' (not 'prey')
- Runs as Windows service (hidden)

### 2. Persistence
- Commands stored in database
- Auto-restart on system boot
- Survives process termination

### 3. Privilege Escalation
- Runs with elevated privileges when needed
- Can execute as logged user or admin
- Windows service provides system-level access

### 4. Lock Action Security
- Blocks Task Manager
- Blocks escape routes
- Requires password to unlock
- Auto-restarts if window closed

### 5. Communication Security
- HTTPS/WSS connections
- Basic Authentication
- Encrypted data transmission

---

## Key Files and Directories

```
C:\Windows\Prey\
├── prey.conf              # Main configuration file
├── commands.db            # SQLite database
├── prey.log               # Main log file
├── wpxsvc.exe             # Windows service executable
├── Uninstall.exe          # Uninstaller
├── versions/              # Version directories
│   └── 1.13.25/          # Current version
│       ├── bin/          # Executables
│       ├── lib/          # Source code
│       │   ├── agent/   # Agent code
│       │   ├── system/  # System utilities
│       │   └── utils/   # Utilities
│       └── node_modules/ # Dependencies
└── updater.log            # Update log
```

---

## Logging System

**Log Files:**
- `prey.log` - Main application log
- `prey.log.1.gz` - Compressed old logs
- `winsvc.log` - Windows service log
- `updater.log` - Update log
- `prey_restarts.log` - Restart tracking

**Log Levels:**
- `info` - Informational messages
- `warn` - Warnings
- `error` - Errors
- `debug` - Debug messages (if DEBUG=true)

**Recent Log Activity:**
- WebSocket status updates every 5 minutes
- Location checks periodically
- Connection status monitoring

---

## Dependencies

**Key Node.js Modules:**
- `ws` - WebSocket client
- `needle` - HTTP client
- `sqlite3` - SQLite database
- `commander` - CLI parsing
- `systeminformation` - System info
- `node-schedule` - Task scheduling
- `async` - Async utilities
- `underscore` - Utility functions

**Custom Modules:**
- `buckle` - Custom utilities
- `linus` - Custom utilities
- `petit` - Logging
- `satan` - Daemon management
- `ocelot` - Custom utilities

---

## API Reference

### Control Panel API

**Base URL:** `https://solid.preyproject.com`

**Endpoints:**
- `GET /api/v2/devices/{device_key}/status` - Get device status
- `POST /api/v2/devices/{device_key}/missing` - Mark as missing
- `WS /api/v2/devices/{device_key}.ws` - WebSocket connection

**Authentication:**
- Basic Auth: `{api_key}:x` encoded in base64

---

## Error Handling

**Error Types:**
- Network errors (ENETDOWN, ENETUNREACH, etc.)
- Configuration errors
- Action execution errors
- Provider errors

**Error Flow:**
1. Error occurs in component
2. Emitted via hooks.trigger('error', err)
3. Logged to prey.log
4. Sent to control panel (if send_crash_reports enabled)
5. Retried if applicable

---

## Performance Considerations

**Optimizations:**
- Commands grouped by structure to prevent duplicates
- Delayed command execution (7 second intervals)
- Cached provider results
- Efficient database queries
- Connection pooling

**Resource Usage:**
- Low CPU usage when idle
- Periodic status updates (every 5 minutes)
- WebSocket heartbeat (every 60 seconds)
- Trigger monitoring (event-driven)

---

## Troubleshooting

**Common Issues:**

1. **Connection Problems**
   - Check network connectivity
   - Verify proxy settings
   - Check firewall rules

2. **Commands Not Executing**
   - Check command database
   - Verify WebSocket connection
   - Review logs for errors

3. **Location Not Updating**
   - Check location permissions
   - Verify WiFi is enabled
   - Review location provider errors

4. **Actions Failing**
   - Check permissions
   - Verify binaries exist
   - Review action-specific logs

---

## Development Notes

**Entry Points:**
- Main: `lib/agent/index.js::run()`
- CLI: `bin/prey`
- Service: `wpxsvc.exe`

**Testing:**
- Mocha test framework
- Test files in `test/` directory
- Coverage via nyc

**Code Style:**
- ESLint with Airbnb config
- Prettier formatting
- JSDoc comments

---

## Conclusion

The Prey system is a comprehensive anti-theft solution with:
- **Modular architecture** - Separated concerns (actions, providers, reports)
- **Event-driven design** - Hooks system for loose coupling
- **Persistent storage** - SQLite for command/response persistence
- **Real-time communication** - WebSocket for instant commands
- **Cross-platform support** - Windows, Mac, Linux implementations
- **Extensible design** - Easy to add new actions/providers

The system is designed to be resilient, stealthy, and feature-rich, providing comprehensive device tracking and security capabilities.

---

**Document Generated:** 2026-01-22  
**System Version:** 1.13.25  
**Analysis Path:** C:\Windows\Prey
