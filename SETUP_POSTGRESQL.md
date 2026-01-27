# 🗄️ Setup PostgreSQL Database - Step by Step

## Choose One Provider (I recommend Supabase - it's easier)

### Option A: Supabase (Recommended - Easier) ⭐

#### Step 1: Create New Project
1. Go to: https://supabase.com/dashboard
2. Click **"New Project"**
3. Fill in:
   - **Project Name:** `antitheft-database` (or any name)
   - **Database Password:** Create a strong password (save it!)
   - **Region:** Choose closest to you
   - **Pricing Plan:** Free tier (selected by default)
4. Click **"Create new project"**
5. Wait 2-3 minutes for database to be created

#### Step 2: Get Connection String
1. Once project is ready, go to: **Settings** (gear icon in left sidebar)
2. Click **"Database"** in settings menu
3. Scroll down to **"Connection string"** section
4. Find **"URI"** tab (or "Connection Pooling" if URI isn't visible)
5. Copy the connection string (looks like):
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
   
   **OR** if you see "Connection string" tab, copy from there:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

6. **Replace `[YOUR-PASSWORD]`** with the password you created in Step 1
7. **Copy the complete string**

#### Step 3: Add to Vercel
1. Go to: https://vercel.com/dashboard
2. Click on your project: **antitheft-backend**
3. Go to: **Settings** tab
4. Click: **Environment Variables** in left menu
5. Click: **Add New**
6. **Key:** `DATABASE_URL`
7. **Value:** Paste the connection string you copied
8. Check boxes: **Production**, **Preview**, **Development**
9. Click **Save**

#### Step 4: Redeploy
1. Vercel will auto-redeploy when you save environment variable
2. OR manually: Go to **Deployments** tab → Click **"..."** on latest deployment → **Redeploy**

---

### Option B: Railway (Alternative)

#### Step 1: Create Database
1. Go to: https://railway.app/dashboard
2. Click **"New Project"**
3. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
4. Wait for database to be created

#### Step 2: Get Connection String
1. Click on the PostgreSQL service
2. Go to **"Variables"** tab
3. Copy the value of **`DATABASE_URL`** variable
   - Format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/railway`

#### Step 3: Add to Vercel
Same as Supabase Step 3 above - add `DATABASE_URL` to Vercel

---

## ✅ Verify Database Connection

### Test 1: Check Backend Health
```bash
python test_agent_hosted.py
```

Should show:
```
[OK] Backend is accessible
   Database: connected
```

### Test 2: Check Vercel Deployment
1. Go to Vercel Dashboard → Your Project
2. Check latest deployment status
3. Should show **"Ready"** status

---

## 🎯 Quick Checklist

- [ ] Created Supabase project (or Railway database)
- [ ] Copied connection string (with password replaced)
- [ ] Added `DATABASE_URL` to Vercel environment variables
- [ ] Selected all environments (Production, Preview, Development)
- [ ] Saved environment variable
- [ ] Backend redeployed
- [ ] Health check shows database connected

---

## 📝 Next Steps After Database is Connected

1. **Run agent:**
   ```bash
   cd device_agent
   python agent.py
   ```

2. **Open frontend:**
   ```
   https://frontend-wine-iota-46.vercel.app
   ```

3. **Sign up or log in** - device will link automatically!

---

## 🆘 Troubleshooting

### Connection String Format
Make sure your connection string looks like:
```
postgresql://username:password@host:port/database
```

### Password with Special Characters
If your password has special characters (like `@`, `#`, `%`), you need to URL-encode them:
- `@` becomes `%40`
- `#` becomes `%23`
- `%` becomes `%25`
- etc.

### Still Not Working?
- Check Vercel logs: Dashboard → Project → Deployments → Latest → Functions tab
- Verify connection string format
- Make sure database is accessible (not paused/sleeping on free tier)
