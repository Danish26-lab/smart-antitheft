# 🔧 Troubleshoot Database Connection

## Current Status
- ✅ Backend is accessible
- ❌ Database is NOT connected
- Error: `psycopg2.OperationalError) connection to server a`

## Possible Issues

### Issue 1: Vercel Not Redeployed Yet
**Fix:** 
1. Go to Vercel Dashboard → Your Project → Deployments
2. Check if there's a new deployment running
3. Wait for it to complete (status: "Ready")
4. This can take 1-3 minutes

### Issue 2: Environment Variable Not Saved Correctly
**Check:**
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Verify `DATABASE_URL` exists
3. Make sure it shows: `Production, Preview, Development`
4. Click on it to verify the value is correct

### Issue 3: Connection String Format
**Your connection string should be:**
```
postgresql://postgres:mBA4hbMf2Nz8yH8d@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres
```

**Common mistakes:**
- ❌ Extra spaces before/after
- ❌ Missing parts
- ❌ Wrong password
- ❌ Special characters not URL-encoded

### Issue 4: Database Sleeping (Free Tier)
**Supabase free tier databases can sleep after inactivity.**

**Fix:**
1. Go to Supabase Dashboard
2. Click on your project
3. If database is paused, click "Resume" or "Wake up"
4. Wait 30 seconds
5. Test again

### Issue 5: Connection Pooling vs Direct Connection
**You're using direct connection (port 5432).**

**Try connection pooling instead:**
1. Go to Supabase → Settings → Database
2. Find "Connection string" section
3. Look for "Connection Pooling" tab
4. Copy the pooled connection string (port 6543)
5. It should look like:
   ```
   postgresql://postgres.zrklexyowpkzzkrbbvto:mBA4hbMf2Nz8yH8d@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
6. Update `DATABASE_URL` in Vercel with this pooled version

## 🔍 Step-by-Step Verification

### Step 1: Verify Environment Variable in Vercel
1. Go to: https://vercel.com/dashboard
2. Click: `antitheft-backend`
3. Go to: Settings → Environment Variables
4. **Check:** Does `DATABASE_URL` exist?
5. **Check:** Is the value correct? (click to view)
6. **Check:** Are all environments selected?

### Step 2: Check Latest Deployment
1. Go to: Deployments tab
2. Check latest deployment:
   - Status should be "Ready"
   - Should have been deployed AFTER you added DATABASE_URL
   - If it's old, manually redeploy

### Step 3: Check Vercel Logs
1. Go to: Deployments → Latest deployment
2. Click: "Functions" tab
3. Look for errors related to database connection
4. Common errors:
   - "connection refused"
   - "authentication failed"
   - "database does not exist"

### Step 4: Test Connection String Directly
You can test if the connection string works:

**Using Python:**
```python
import psycopg2

conn_string = "postgresql://postgres:mBA4hbMf2Nz8yH8d@db.zrklexyowpkzzkrbbvto.supabase.co:5432/postgres"
try:
    conn = psycopg2.connect(conn_string)
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

## 🚀 Quick Fix: Use Connection Pooling

**Supabase connection pooling is more reliable for serverless:**

1. Go to Supabase Dashboard → Your Project
2. Settings → Database
3. Scroll to "Connection string" section
4. Click "Connection Pooling" tab (or "URI" tab with pooler)
5. Copy the connection string (should have `pooler.supabase.com:6543`)
6. Update `DATABASE_URL` in Vercel
7. Redeploy

**Pooled connection string format:**
```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## ✅ After Fixing

Run test again:
```bash
python test_agent_hosted.py
```

Should show:
```
[OK] Backend is accessible
   Database: connected
```

Then you can:
1. Run agent: `cd device_agent && python agent.py`
2. Open frontend and sign up/login
3. Device will appear automatically!
