# 📱 Device Agent Setup Guide

## Overview

The **Device Agent** runs **locally** on each device you want to track. It does **NOT** need to be hosted - it just connects to your Vercel backend.

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Device Agent   │  ────>  │  Vercel Backend  │  <───   │  Vercel         │
│  (Local)        │         │  (Hosted)        │         │  Frontend       │
│                 │         │                  │         │  (Hosted)       │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

- **Agent**: Runs on your device (laptop, phone, etc.) - **NO hosting needed**
- **Backend**: Hosted on Vercel (`https://antitheft-backend.vercel.app`)
- **Frontend**: Hosted on Vercel (`https://frontend-wine-iota-46.vercel.app`)

## Quick Setup

### 1. Install Python Dependencies

```bash
cd device_agent
pip install -r requirements.txt
```

### 2. Run the Agent

The agent will automatically:
- ✅ Detect your hardware
- ✅ Generate a unique fingerprint
- ✅ Register with the backend
- ✅ Start reporting location and status

```bash
python agent.py
```

### 3. First Time Setup

**On first run, the agent will:**
1. Generate a hardware fingerprint (unique to your device)
2. Auto-register with the backend (creates an "unowned" device)
3. Wait for you to link it to your user account

**To link the device to your account:**
1. Open the frontend: `https://frontend-wine-iota-46.vercel.app`
2. Log in or sign up
3. The frontend will automatically discover and link the local agent

## Configuration

### Backend URL

The agent is configured to use the Vercel backend by default:

**Production (Vercel):**
- Backend URL: `https://antitheft-backend.vercel.app/api`

**Local Development:**
If you want to use a local backend, set an environment variable:

**Windows:**
```cmd
set API_BASE_URL=http://localhost:5000/api
python agent.py
```

**Mac/Linux:**
```bash
export API_BASE_URL=http://localhost:5000/api
python agent.py
```

### Config File

Edit `config.json` to customize:

```json
{
  "device_id": "your-device-name",
  "user_email": "your@email.com",
  "report_interval": 15,
  "check_commands_interval": 0.2
}
```

## Running on Multiple Devices

**To track multiple devices:**

1. **Copy the agent folder** to each device
2. **Run the agent** on each device
3. **Each device** will automatically register itself
4. **Link devices** to your account when you log in

## Running as a Service (Background)

### Windows (Task Scheduler)

1. Create a scheduled task that runs `agent.py` on startup
2. Or use `pythonw agent.py` to run without a console window

### Mac/Linux (systemd)

Create a service file: `/etc/systemd/system/antitheft-agent.service`

```ini
[Unit]
Description=Anti-Theft Agent
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/device_agent
ExecStart=/usr/bin/python3 agent.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable antitheft-agent
sudo systemctl start antitheft-agent
```

## Troubleshooting

### Agent can't connect to backend

**Check:**
1. ✅ Internet connection
2. ✅ Backend URL is correct: `https://antitheft-backend.vercel.app`
3. ✅ No firewall blocking Python

### Device not showing in dashboard

**Check:**
1. ✅ Agent is running
2. ✅ Agent successfully registered (check `agent.log`)
3. ✅ Logged in with the correct account
4. ✅ Frontend discovered the agent (check browser console)

### Test Connection

Test if agent can reach the backend:

```bash
# Windows
curl https://antitheft-backend.vercel.app/api/health

# Mac/Linux
curl https://antitheft-backend.vercel.app/api/health
```

Should return: `{"status":"running",...}`

## Summary

✅ **Agent runs locally** - No hosting needed  
✅ **Automatically connects** to Vercel backend  
✅ **Works offline** - Caches data and syncs when online  
✅ **Secure** - Uses HTTPS to communicate with backend  

Just run `python agent.py` on each device you want to track!
