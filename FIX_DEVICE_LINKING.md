# 🔧 Fix: Device "Danish-windows" Not Accessible

## Problem

The device "Danish-windows" exists in the database but you can't access it because:
- It's linked to a different user account (probably `admin@antitheft.com`)
- When you log in with a different email, the device doesn't appear
- The frontend shows "Device not found"

## ✅ Solution: Link Device to Your Account

### Option 1: Log In with Same Email (Quick Fix)

If the device is linked to `admin@antitheft.com`:

1. **Log out** from the frontend
2. **Log in** with: `admin@antitheft.com` / `admin123`
3. Device "Danish-windows" should appear

### Option 2: Re-link Device via Login (Recommended)

The agent should make the device UNOWNED so it can link to any user. Here's how:

1. **Make sure agent is running** (it should be already)
2. **Log in** to: `https://frontend-wine-iota-46.vercel.app`
3. The frontend should **automatically discover** the agent
4. The device should **automatically link** to your account

**If this doesn't work**, the device might be hard-linked to another user. In that case:

### Option 3: Re-register Device as UNOWNED

1. **Stop the agent** (Task Manager → End `python.exe`)
2. **Delete or rename** `device_agent/config.json` (backup first)
3. **Restart the agent** - it will register as UNOWNED
4. **Log in** - device will link automatically

---

## 🎯 Quick Test

Check if you can access the device:

1. Go to: `https://frontend-wine-iota-46.vercel.app`
2. **Log in** with the email you use
3. Check if "Danish-windows" appears in the Devices list
4. If not, try logging in with `admin@antitheft.com`

---

## 🔍 Verify Device Status

The device exists and is active, but ownership might be the issue.

**Next step:** Try logging in with `admin@antitheft.com` first to see if the device appears.
