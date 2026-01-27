# ✅ Add Database to Vercel - RIGHT NOW

## Your Connection String (Keep This Secret!)
```
postgresql://postgres:mBA4hbMf2Nz8yH8d@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres
```

## 🚀 Add to Vercel (2 Minutes)

### Step 1: Open Vercel Dashboard
1. Go to: **https://vercel.com/dashboard**
2. Click on your project: **antitheft-backend**

### Step 2: Go to Environment Variables
1. Click **"Settings"** tab (at the top)
2. Click **"Environment Variables"** (in left sidebar)

### Step 3: Add DATABASE_URL
1. Click **"Add New"** button
2. **Key:** Type: `DATABASE_URL`
3. **Value:** Paste this:
   ```
   postgresql://postgres:mBA4hbMf2Nz8yH8d@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres
   ```
4. **Environment:** Check ALL three boxes:
   - ☑ Production
   - ☑ Preview
   - ☑ Development
5. Click **"Save"**

### Step 4: Wait for Redeploy
- Vercel will automatically start a new deployment
- Go to **"Deployments"** tab to watch it build
- Wait 1-2 minutes for "Ready" status

### Step 5: Test!
Run this command:
```bash
python test_agent_hosted.py
```

Should show:
```
[OK] Backend is accessible
   Database: connected
```

## ✅ Done! Next Steps

1. **Run agent:**
   ```bash
   cd device_agent
   python agent.py
   ```

2. **Open frontend:**
   ```
   https://frontend-wine-iota-46.vercel.app
   ```

3. **Sign up or log in** - your device will appear automatically!

---

**That's it! Your agent-first architecture is now fully functional! 🎉**
