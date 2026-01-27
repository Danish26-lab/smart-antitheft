# 🔄 Restart Agent to Fix Registration

## Current Status

✅ Agent is running  
⚠️ But it's using OLD code (before our fixes)  
❌ Device "Danish-windows" not registered on Vercel backend  

## ✅ Solution: Restart Agent

The agent is currently running with old code. We need to restart it to use the NEW code that will:
1. Register "Danish-windows" with Vercel backend
2. Use agent-first architecture
3. Verify device exists before skipping registration

### Step 1: Stop Current Agent

1. Open **Task Manager** (`Ctrl + Shift + Esc`)
2. Find `python.exe` or `pythonw.exe` process
3. Right-click → **End Task**
4. Or close the terminal window if agent is running there

### Step 2: Start Agent Again

Run:
```bash
cd device_agent
python agent.py
```

**Expected output with NEW code:**
```
[AUTO-REG] Starting agent-first registration (Prey Project style)...
[AUTO-REG] Device Danish-windows not found on server, re-registering...
[AUTO-REG] Using preferred device_id: Danish-windows
[AUTO-REG] Device registered: Danish-windows
[AUTO-REG] Device status: UNOWNED (awaiting user link)
[LOCAL-SERVER] Started local discovery server on http://127.0.0.1:9123/device-info
```

### Step 3: Link Device

1. **Keep agent running**
2. Go to: `https://frontend-wine-iota-46.vercel.app`
3. **Log in** (or sign up)
4. Device "Danish-windows" will be automatically linked
5. Access device details - map will work!

---

## 🎯 Quick Command

Stop old agent and start new one:
```bash
# Stop Python processes (or use Task Manager)
taskkill /F /IM python.exe

# Start agent
cd device_agent
python agent.py
```
