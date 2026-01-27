# 🔧 Fix: Device Not Found - "Danish-windows"

## Problem
You're seeing "Device not found" for "Danish-windows" because:
1. The device doesn't exist in the database, OR
2. The device exists but isn't linked to your user account

## ✅ Solution: Register Your Device with Agent-First Architecture

### Step 1: Run the Agent

Open a terminal and run:

```bash
cd device_agent
python agent.py
```

**What happens:**
- Agent detects your hardware fingerprint
- Registers with backend: `https://antitheft-backend.vercel.app/api/agent/register`
- Creates a NEW device (device_id will be auto-generated like `Danish-XXXX`)
- Device starts as **UNOWNED** (no user linked yet)

**Expected output:**
```
[AUTO-REG] Device registered: Danish-ABC12345
[AUTO-REG] Device status: UNOWNED (awaiting user link)
[LOCAL-SERVER] Started local discovery server on http://127.0.0.1:9123/device-info
```

### Step 2: Link Device to Your Account

1. **Keep the agent running** (don't close the terminal)
2. Go to: `https://frontend-wine-iota-46.vercel.app`
3. **Log in** (or sign up if you don't have an account)
4. Frontend will **automatically discover** the running agent
5. Device will be **automatically linked** to your account
6. Device will appear in your dashboard

### Step 3: Access Device Details

After linking:
- Go to **Devices** page
- Click on your device
- You'll see: Map, Location, Activity Logs, etc.

---

## 🔍 What Device ID Will You Get?

The agent generates device_id as: `{hostname}-{serial[:8]}`

**Example:**
- Hostname: `Danish`
- Serial: `ABC123456789`
- Device ID: `Danish-ABC12345`

**Note:** The device_id might not be exactly "Danish-windows", but you can:
- **Rename the device** in the dashboard to "Danish Windows"
- The device_id is just an identifier - the name is what you see

---

## 🆘 If "Danish-windows" Already Exists

If you have an existing device "Danish-windows" in the database but it's not linked:

### Option A: Link Existing Device (Manual)

1. Log in to dashboard
2. Check if "Danish-windows" appears in device list
3. If it does, click on it - it should work
4. If it doesn't appear, it's not linked to your account

### Option B: Use New Agent Registration (Recommended)

1. Run the agent (creates new device with fingerprint)
2. Log in (automatically links new device)
3. Delete old "Danish-windows" device if needed
4. Rename new device to "Danish Windows"

---

## ✅ Quick Checklist

- [ ] Agent is running (`python agent.py`)
- [ ] Agent shows: "Device registered: ..."
- [ ] Agent shows: "Local discovery server started"
- [ ] Logged in to frontend
- [ ] Device appears in dashboard
- [ ] Can click on device to see details

---

## 🎯 After Fixing

Once your device is registered and linked:
- ✅ Map view will work
- ✅ Location tracking will work
- ✅ All device functions will work
- ✅ Device will show in dashboard

The key is: **Run the agent FIRST, then log in** - the device will link automatically!
