# 🗄️ Setup Database for Vercel Deployment

## ⚠️ Problem

Vercel serverless functions have a **read-only filesystem**, so SQLite won't work. You need a **PostgreSQL database** hosted in the cloud.

## ✅ Solution: Free PostgreSQL Database Options

### Option 1: Supabase (Recommended - Easiest)

1. **Sign up**: Go to https://supabase.com
2. **Create project**: Click "New Project"
3. **Get connection string**:
   - Go to Project Settings → Database
   - Copy the "Connection string" (URI format)
   - It looks like: `postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

### Option 2: Neon (Free Tier)

1. **Sign up**: Go to https://neon.tech
2. **Create project**: Click "Create Project"
3. **Get connection string**:
   - Go to Connection Details
   - Copy the connection string
   - Format: `postgresql://user:password@host.neon.tech/dbname`

### Option 3: Railway (Free Tier)

1. **Sign up**: Go to https://railway.app
2. **Create PostgreSQL**: New → Database → PostgreSQL
3. **Get connection string**:
   - Click on PostgreSQL service
   - Go to Variables tab
   - Copy `DATABASE_URL`

## 🔧 Configure Vercel Environment Variable

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Select your project**: `antitheft-backend`
3. **Settings** → **Environment Variables**
4. **Add new variable**:
   - **Name**: `DATABASE_URL`
   - **Value**: Your PostgreSQL connection string (from above)
   - **Environment**: Production, Preview, Development (select all)
5. **Save** and **Redeploy**

## 🚀 Quick Setup Commands

After setting up the database, redeploy:

```bash
cd "c:\Users\danis\OneDrive\Desktop\New folder (3)"
vercel --prod
```

## ✅ Verify Database Connection

Test the health endpoint:
```
https://antitheft-backend.vercel.app/api/health
```

Should show: `"database": "connected"`

## 📝 Database Schema

The backend will automatically create all tables on first request:
- `users` - User accounts
- `devices` - Registered devices
- `activity_logs` - Device activity history
- `breach_reports` - Security breach reports
- And more...

## 🔄 Migration from Local SQLite

If you have existing data in local SQLite:
1. Export data from SQLite
2. Import to PostgreSQL
3. Or start fresh (recommended for testing)

---

**Need help?** Check the backend logs in Vercel Dashboard → Deployments → View Function Logs
