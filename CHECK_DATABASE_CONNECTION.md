# 🔍 Check Your Database Connection

## Current Status

From your logs, I can see:
- ✅ You have a Supabase database: `db.zrklexyowpkzzkrbbvto.supabase.co`
- ❌ Connection is failing: "Cannot assign requested address"

## The Problem

Vercel serverless functions need a **connection pooler URL**, not the direct database URL.

## ✅ Solution: Use Supabase Connection Pooler

### Step 1: Get the Pooler URL from Supabase

1. Go to your Supabase project: https://supabase.com/dashboard
2. Click on your project
3. Go to **Settings** → **Database**
4. Scroll down to **Connection Pooling**
5. Copy the **Connection string** under **Session mode** or **Transaction mode**
   - It should look like: `postgresql://postgres.zrklexyowpkzzkrbbvto:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres`
   - **NOT** the direct connection: `postgresql://postgres:[PASSWORD]@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres`

### Step 2: Update Vercel Environment Variable

1. Go to: https://vercel.com/dashboard
2. Select your **antitheft-backend** project
3. Go to **Settings** → **Environment Variables**
4. Find `DATABASE_URL`
5. **Update it** with the **pooler connection string** (port 6543, not 5432)
6. Make sure it's set for **Production**, **Preview**, and **Development**
7. **Save**

### Step 3: Redeploy

```bash
cd "c:\Users\danis\OneDrive\Desktop\New folder (3)"
vercel --prod
```

## 🔍 Verify Connection

After redeploying, check:
```
https://antitheft-backend.vercel.app/api/health
```

Should show: `"database": { "status": "connected" }`

## 📝 Connection String Format

**❌ Wrong (Direct connection - doesn't work on Vercel):**
```
postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

**✅ Correct (Connection pooler - works on Vercel):**
```
postgresql://postgres.xxxxx:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

**Key differences:**
- Port: `6543` (pooler) instead of `5432` (direct)
- Host: `pooler.supabase.com` instead of `db.xxxxx.supabase.co`
- Username: `postgres.xxxxx` instead of `postgres`

---

**Still having issues?** Check Vercel function logs for detailed error messages.
