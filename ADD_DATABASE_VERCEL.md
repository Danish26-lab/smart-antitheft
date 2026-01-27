# 🔗 Add Database to Vercel - Quick Steps

## Your Connection String

You have:
```
postgresql://postgres.xxxxx:mBA4hbMf2Nz8yH8d@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Important:** If `xxxxx` is a placeholder, you need to replace it with your actual Supabase project reference.

## Step 1: Get Complete Connection String from Supabase

1. Go to: https://supabase.com/dashboard
2. Click on your project
3. Go to: **Settings** (⚙️) → **Database**
4. Scroll to **"Connection string"** section
5. Click on **"URI"** tab (or "Connection Pooling")
6. You should see something like:
   ```
   postgresql://postgres.abc123def456:mBA4hbMf2Nz8yH8d@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
   (The `abc123def456` part is your project reference - it's unique)

7. **Copy the ENTIRE string** (make sure password is already in it)

## Step 2: Add to Vercel

1. **Go to Vercel Dashboard:**
   - https://vercel.com/dashboard

2. **Click on your project:** `antitheft-backend`

3. **Go to Settings:**
   - Click **"Settings"** tab at the top

4. **Open Environment Variables:**
   - Click **"Environment Variables"** in the left sidebar

5. **Add New Variable:**
   - Click **"Add New"** button
   - **Key:** `DATABASE_URL`
   - **Value:** Paste your complete connection string
   - **Environment:** Check all three boxes:
     - ☑ Production
     - ☑ Preview  
     - ☑ Development
   - Click **"Save"**

## Step 3: Verify It's Added

You should see:
```
DATABASE_URL    •••••••••••••••••••••••••••••••••••••••••    Production, Preview, Development
```

## Step 4: Redeploy Backend

Vercel will automatically redeploy when you add environment variables.

**To verify:**
1. Go to **"Deployments"** tab
2. You should see a new deployment starting
3. Wait for it to complete (status: "Ready")

**OR manually redeploy:**
```bash
cd backend
vercel --prod --yes
```

## Step 5: Test Connection

Run the diagnostic:
```bash
python test_agent_hosted.py
```

Should show:
```
[OK] Backend is accessible
   Database: connected
```

If it shows "Database: error" or "Database: unknown", check:
- Connection string format is correct
- Password doesn't have unencoded special characters
- Database is not paused (free tier databases can sleep)

## 🎯 Quick Checklist

- [ ] Got complete connection string from Supabase (with project reference, not xxxxx)
- [ ] Added `DATABASE_URL` to Vercel environment variables
- [ ] Selected all environments (Production, Preview, Development)
- [ ] Saved the variable
- [ ] Backend redeployed
- [ ] Test shows database connected

## ✅ After Database is Connected

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
