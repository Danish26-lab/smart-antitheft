# 🚀 Prey-Style Automatic Installer

## Overview

This installer follows the **Prey Project approach** - **zero configuration, fully automatic setup**. Your friend just needs to double-click `INSTALL.bat` and everything is done automatically.

## How It Works (Like Prey)

### Prey Project Method:
1. ✅ User downloads installer
2. ✅ Double-clicks installer
3. ✅ Everything installs automatically
4. ✅ Agent auto-registers device
5. ✅ Agent auto-starts on boot
6. ✅ **No user configuration needed**

### Our Implementation:
1. ✅ Friend copies `device_agent` folder
2. ✅ Double-clicks `INSTALL.bat`
3. ✅ Installer checks Python (prompts if missing)
4. ✅ Auto-installs dependencies
5. ✅ Auto-creates configuration
6. ✅ Auto-sets up Windows scheduled task
7. ✅ Auto-starts agent
8. ✅ **No user configuration needed**

## Installation Steps

### For Your Friend (Super Simple):

1. **Copy the `device_agent` folder** to their laptop
2. **Double-click `INSTALL.bat`**
3. **Wait for installation to complete** (2-3 minutes)
4. **Done!** Agent is running and will auto-start on login

### What Happens Automatically:

1. **Python Check**: Verifies Python is installed (prompts if missing)
2. **Dependencies**: Installs all required packages automatically
3. **Configuration**: Creates `config.json` automatically
4. **Auto-Start**: Sets up Windows scheduled task for auto-start
5. **Agent Start**: Starts the agent immediately
6. **Registration**: Agent auto-registers device (no user input)

## Features (Like Prey)

### ✅ Automatic Registration
- Agent registers itself on first run
- Creates "unowned" device in database
- Links to user account when friend logs in
- **No manual registration needed**

### ✅ Auto-Start on Boot
- Windows scheduled task created automatically
- Agent starts on every login
- Runs in background (minimized)
- **No manual startup needed**

### ✅ Zero Configuration
- All settings auto-detected
- Hardware fingerprinting automatic
- Backend URL pre-configured
- **No config file editing needed**

### ✅ Background Operation
- Runs silently in background
- No console window needed
- Can check status via Task Manager
- **No user interaction needed**

## File Structure

```
device_agent/
├── INSTALL.bat          ← Double-click this (main installer)
├── UNINSTALL.bat        ← Remove agent (optional)
├── agent.py            ← Main agent (auto-started)
├── config.json         ← Auto-created (no editing needed)
├── requirements.txt    ← Dependencies (auto-installed)
└── README_INSTALLER.md ← This file
```

## Usage

### Installation:
```batch
Double-click: INSTALL.bat
```

### Uninstallation:
```batch
Double-click: UNINSTALL.bat
```

### Manual Start (if needed):
```batch
python agent.py
```

### Check Status:
- Open Task Manager
- Look for `python.exe` or `pythonw.exe`
- Or check `agent.log` file

## What Friend Needs to Do

### Minimum (Recommended):
1. Copy `device_agent` folder
2. Double-click `INSTALL.bat`
3. Wait for completion
4. **Done!**

### If Python Not Installed:
1. Installer will prompt
2. Click "Y" to open Python download page
3. Download and install Python
4. **Important**: Check "Add Python to PATH"
5. Run `INSTALL.bat` again

## After Installation

1. **Agent is running** (check Task Manager)
2. **Friend logs in** to frontend
3. **Device auto-appears** in dashboard
4. **Device auto-links** to friend's account
5. **Location updates** start within 1-2 minutes

## Troubleshooting

### Agent Not Starting:
- Check Task Manager for `python.exe`
- Check `agent.log` for errors
- Try running `python agent.py` manually

### Python Not Found:
- Reinstall Python
- Make sure "Add Python to PATH" is checked
- Restart computer after installation

### Dependencies Failed:
- Check internet connection
- Try: `pip install -r requirements.txt` manually

### Auto-Start Not Working:
- May need admin rights
- Check Task Scheduler for "AntiTheftAgent" task
- Can start manually: `python agent.py`

## Comparison with Prey

| Feature | Prey Project | Our System |
|---------|--------------|------------|
| Installation | One-click installer | One-click `INSTALL.bat` |
| Configuration | Automatic | Automatic |
| Registration | Auto-register | Auto-register |
| Auto-Start | Windows Service | Scheduled Task |
| Background | Yes | Yes |
| User Input | None | None (except Python if missing) |

## Advantages

1. **Zero Configuration**: Everything automatic
2. **User-Friendly**: Just double-click and done
3. **Prey-Style**: Follows proven Prey approach
4. **Reliable**: Auto-start ensures agent always runs
5. **Simple**: No technical knowledge needed

## Notes

- Agent must keep running for tracking to work
- Auto-start ensures it runs on every login
- Configuration is auto-created and managed
- No manual editing of config files needed
- Agent auto-registers on first run

---

**Just like Prey - install once, forget about it!** 🎉
