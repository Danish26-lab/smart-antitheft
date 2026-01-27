# 🚀 Complete Setup Guide: Agent-First Architecture on Vercel

## Current Status

✅ Your agent-first architecture is **already implemented**  
❌ You need to configure it to work with your **hosted Vercel backend**

## ⚡ Quick Fix (3 Steps)

### Step 1: Set Up PostgreSQL Database (REQUIRED)

**Vercel doesn't support SQLite** - you need PostgreSQL.

**Option A: Free PostgreSQL (Recommended)**
1. Go to: https://supabase.com
2. Create free account
3. Create new project
4. Go to: Settings → Database
5. Copy the connection string (format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`)

**Option B: Railway**
1. Go to: https://railway.app
2. Create free account
3. Create new PostgreSQL database
4. Copy connection string

### Step 2: Add Database URL to Vercel

1. Go to: **Vercel Dashboard** → Your Project → **Settings** → **Environment Variables**
2. Click **Add New**
3. **Key:** `DATABASE_URL`
4. **Value:** Your PostgreSQL connection string
5. Select **Production**, **Preview**, and **Development**
6. Click **Save**

### Step 3: Redeploy Backend

Vercel will auto-redeploy, or manually redeploy:
```bash
cd backend
vercel --prod --yes
```

## ✅ Verify It Works

### Test 1: Backend Health

```bash
python test_agent_hosted.py
```

Should show:
```
✅ Backend is accessible
   Database: connected
```

### Test 2: Run Agent

```bash
cd device_agent
python agent.py
```

Look for:
```
[AUTO-REG] Device registered: your-device-id
[AUTO-REG] Device status: UNOWNED (awaiting user link)
```

### Test 3: Link Device

1. Go to: `https://frontend-wine-iota-46.vercel.app`
2. Sign up or log in
3. Device should appear in dashboard automatically!

## 📋 Complete Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Agent Starts (Local Device)                         │
│    - Collects hardware fingerprint                      │
│    - Registers with backend (creates UNOWNED device)    │
│    - Starts local discovery server (port 9123)          │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ POST /api/agent/register
                 │ { fingerprint_hash, hardware_info }
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Backend (Vercel)                                     │
│    - Creates device with user_id = NULL                 │
│    - Returns device_id                                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ User logs in
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Frontend (Vercel)                                    │
│    - Discovers local agent: 127.0.0.1:9123/device-info │
│    - Gets device_id or fingerprint_hash                 │
│    - Sends to backend: POST /api/login                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ { email, password, device_id }
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Backend Links Device                                 │
│    - Finds device by device_id                          │
│    - Sets user_id = current_user.id                     │
│    - Device now belongs to user                         │
└─────────────────────────────────────────────────────────┘
```

## 🔍 Troubleshooting

### Error: "Database not connected"

**Fix:**
1. ✅ Set up PostgreSQL (Supabase/Railway)
2. ✅ Add `DATABASE_URL` to Vercel environment variables
3. ✅ Redeploy backend

### Error: "Cannot connect to backend"

**Check:**
1. Backend URL is correct: `https://antitheft-backend.vercel.app`
2. Backend is deployed (check Vercel Dashboard)
3. Internet connection works

### Error: "Agent registration failed"

**Check:**
1. Agent can reach backend: `curl https://antitheft-backend.vercel.app/api/health`
2. Backend database is connected
3. Agent logs: `device_agent/agent.log`

### Error: "Device not appearing after login"

**Check:**
1. Agent is running (`python agent.py`)
2. Agent registered successfully (check `config.json` has `device_id`)
3. Frontend discovered device (check browser console for `[DEVICE-LINK]`)
4. Backend linked device (check Vercel logs)

## 🎯 What You Should See

### When Agent Starts:
```
[AUTO-REG] Collecting hardware fingerprint...
[AUTO-REG] Hardware fingerprint: abc123...
[AUTO-REG] Sending registration request to backend...
[AUTO-REG] Device registered: Danish-windows
[AUTO-REG] Device status: UNOWNED (awaiting user link)
[LOCAL-SERVER] Started local discovery server on http://127.0.0.1:9123/device-info
```

### When User Logs In:
```
[DEVICE-LINK] Linking discovered device: Danish-windows
```

### In Dashboard:
- Device appears immediately
- All hardware info displayed
- Can lock/alarm/wipe device

## 📝 Summary

**What you need:**
1. ✅ PostgreSQL database (Supabase/Railway - FREE)
2. ✅ `DATABASE_URL` environment variable in Vercel
3. ✅ Agent running locally (`python agent.py`)
4. ✅ Frontend deployed (already done)

**What happens automatically:**
- ✅ Agent registers itself (no token needed)
- ✅ Frontend discovers agent
- ✅ Backend links device to user
- ✅ Device appears in dashboard

**No manual steps needed!**

---

**Need help?** Run `python test_agent_hosted.py` to diagnose issues.
