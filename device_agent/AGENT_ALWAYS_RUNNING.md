# 🔄 Make Agent Always Running

## Overview

For an anti-theft system, the agent **must run continuously** to:
- Track device location
- Respond to lock/alarm commands
- Report device status
- Monitor for security events

---

## ✅ Method 1: Windows Startup (Easiest - Recommended)

### Step 1: Install Startup Script

**Option A: Automatic Installation**
1. Double-click: `install_agent_service.bat`
2. It will create a startup shortcut automatically
3. Agent will start when Windows boots

**Option B: Manual Installation**
1. Press `Win + R`
2. Type: `shell:startup`
3. Press Enter (opens Startup folder)
4. Create a shortcut to: `run_agent_silent.vbs`
5. Done! Agent will start on boot

### Step 2: Test It

1. Restart your computer
2. Agent should start automatically (no window visible)
3. Check if agent is running:
   - Open Task Manager (`Ctrl + Shift + Esc`)
   - Look for `python.exe` running `agent.py`
   - Or check `device_agent/agent.log` for activity

---

## ✅ Method 2: Run Silently (No Window)

### Double-Click to Start
- **File:** `run_agent_silent.vbs`
- **What it does:** Starts agent in background (no visible window)
- **Use case:** Start agent manually without showing a window

### Run from Command Line
```bash
cd device_agent
pythonw agent.py
```
(`pythonw` runs Python without a window)

---

## ✅ Method 3: Windows Task Scheduler (Most Reliable)

### Step 1: Open Task Scheduler
1. Press `Win + R`
2. Type: `taskschd.msc`
3. Press Enter

### Step 2: Create New Task
1. Click **"Create Basic Task"** (right panel)
2. **Name:** `Anti-Theft Agent`
3. **Description:** `Runs device agent on startup`
4. Click **Next**

### Step 3: Set Trigger
1. Select **"When the computer starts"**
2. Click **Next**

### Step 4: Set Action
1. Select **"Start a program"**
2. **Program/script:** `pythonw` (or full path: `C:\Python\pythonw.exe`)
3. **Add arguments:** `agent.py`
4. **Start in:** `C:\Users\danis\OneDrive\Desktop\New folder (3)\device_agent`
5. Click **Next**

### Step 5: Finish
1. Check **"Open the Properties dialog..."**
2. Click **Finish**
3. In Properties:
   - Check **"Run whether user is logged on or not"**
   - Check **"Run with highest privileges"** (if needed)
   - Click **OK**

---

## ✅ Method 4: Windows Service (Advanced)

For production use, you can install the agent as a Windows Service using `NSSM` (Non-Sucking Service Manager):

### Step 1: Download NSSM
1. Download from: https://nssm.cc/download
2. Extract to a folder (e.g., `C:\nssm`)

### Step 2: Install Service
```bash
# Open Command Prompt as Administrator
cd C:\nssm\win64
nssm install AntiTheftAgent
```

### Step 3: Configure Service
- **Path:** `C:\Python\python.exe` (or your Python path)
- **Startup directory:** `C:\Users\danis\OneDrive\Desktop\New folder (3)\device_agent`
- **Arguments:** `agent.py`

### Step 4: Start Service
```bash
nssm start AntiTheftAgent
```

---

## 🔍 Verify Agent is Running

### Check 1: Task Manager
1. Press `Ctrl + Shift + Esc`
2. Look for `python.exe` or `pythonw.exe`
3. Check if it's running `agent.py`

### Check 2: Log File
1. Open: `device_agent/agent.log`
2. Should see recent activity:
   ```
   [AUTO-REG] Device registered: ...
   [LOCAL-SERVER] Started local discovery server...
   ```

### Check 3: Local Discovery Endpoint
1. Open browser
2. Go to: `http://127.0.0.1:9123/device-info`
3. Should return JSON with `device_id` and `fingerprint_hash`

### Check 4: Dashboard
1. Log in to: `https://frontend-wine-iota-46.vercel.app`
2. Device should appear in dashboard
3. Location should update

---

## 🛠️ Troubleshooting

### Agent Not Starting on Boot

**Check:**
1. Startup folder shortcut exists
2. Python path is correct
3. Agent directory path is correct
4. Check Windows Event Viewer for errors

**Fix:**
- Re-run `install_agent_service.bat`
- Or manually create shortcut in Startup folder

### Agent Stops Running

**Possible causes:**
- Python error (check `agent.log`)
- Network connection lost
- Backend unreachable

**Fix:**
- Check `device_agent/agent.log` for errors
- Verify backend is accessible: `https://antitheft-backend.vercel.app/api/health`
- Restart agent manually

### Agent Window Keeps Appearing

**Fix:**
- Use `run_agent_silent.vbs` instead of `agent.py`
- Or use `pythonw agent.py` instead of `python agent.py`

---

## 📋 Quick Reference

| Method | Difficulty | Reliability | Auto-Start |
|--------|-----------|------------|------------|
| Startup Folder | ⭐ Easy | ⭐⭐ Good | ✅ Yes |
| Task Scheduler | ⭐⭐ Medium | ⭐⭐⭐ Excellent | ✅ Yes |
| Windows Service | ⭐⭐⭐ Hard | ⭐⭐⭐ Excellent | ✅ Yes |
| Manual Start | ⭐ Easy | ⭐ Poor | ❌ No |

**Recommended:** Use **Method 1 (Startup Folder)** for simplicity, or **Method 3 (Task Scheduler)** for reliability.

---

## ✅ After Setup

Once agent is always running:
- ✅ Device location updates automatically
- ✅ Lock/alarm commands work immediately
- ✅ Device appears in dashboard
- ✅ All anti-theft features active

**Remember:** The agent must be running for the anti-theft system to work!
