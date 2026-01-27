# 🚨 Quick Fix: Database Setup for Sign Up

## The Problem

Your sign up is failing because **Vercel doesn't support SQLite**. You need a **PostgreSQL database**.

## ⚡ Fastest Solution (5 minutes)

### Step 1: Get Free PostgreSQL Database

**Option A: Supabase (Recommended)**
1. Go to: https://supabase.com
2. Click **"Start your project"** → Sign up (free)
3. Click **"New Project"**
4. Wait 2 minutes for database to create
5. Go to **Settings** → **Database**
6. Copy the **Connection string** (URI format)
   - Looks like: `postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`

**Option B: Neon (Alternative)**
1. Go to: https://neon.tech
2. Sign up (free)
3. Create project
4. Copy connection string

### Step 2: Add to Vercel

1. Go to: https://vercel.com/dashboard
2. Click your **antitheft-backend** project
3. Go to **Settings** → **Environment Variables**
4. Click **Add New**
5. Enter:
   - **Key**: `DATABASE_URL`
   - **Value**: (paste your PostgreSQL connection string)
   - **Environment**: Select all (Production, Preview, Development)
6. Click **Save**

### Step 3: Redeploy

```bash
cd "c:\Users\danis\OneDrive\Desktop\New folder (3)"
vercel --prod
```

### Step 4: Test

1. Go to: https://antitheft-backend.vercel.app/api/health
2. Should show: `"database": { "status": "connected" }`
3. Try signing up again!

## ✅ Done!

Your sign up should work now!

---

**Need help?** Check the detailed guide: `SETUP_VERCEL_DATABASE.md`
