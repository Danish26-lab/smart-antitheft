# 🔧 Fix Supabase Connection for Vercel

## ⚠️ The Issue

You have Supabase linked, but Vercel can't connect because you're using the **direct connection** instead of the **connection pooler**.

## ✅ Quick Fix (2 minutes)

### Step 1: Get Pooler URL

1. Go to: https://supabase.com/dashboard
2. Select your project
3. **Settings** → **Database**
4. Scroll to **Connection Pooling**
5. Copy the **Connection string** (Session mode)
   - Should have `pooler.supabase.com` and port `6543`

### Step 2: Update Vercel

1. Go to: https://vercel.com/dashboard
2. Your project → **Settings** → **Environment Variables**
3. Find `DATABASE_URL`
4. **Replace** with the pooler URL
5. **Save**

### Step 3: Redeploy

```bash
vercel --prod
```

## 📋 Connection String Comparison

**Current (Direct - ❌ Doesn't work on Vercel):**
```
postgresql://postgres:[PASSWORD]@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres
```

**Needed (Pooler - ✅ Works on Vercel):**
```
postgresql://postgres.zrklexyowpkzzkrbbvto:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## 🎯 Why?

- Vercel serverless functions have connection limits
- Direct connections (5432) don't work well with serverless
- Connection pooler (6543) handles multiple connections efficiently

---

**After updating, your sign up will work!** 🎉
