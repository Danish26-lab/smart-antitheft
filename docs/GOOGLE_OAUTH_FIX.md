# 🔐 Fix Google Sign-In "origin_mismatch" Error

## Problem
You're getting this error when trying to sign in with Google:
- **Error 400: origin_mismatch**
- "You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy"

This happens because your Vercel frontend domain is not registered in Google Cloud Console.

## Solution: Add Authorized JavaScript Origins

### Step 1: Go to Google Cloud Console

1. Visit: **https://console.cloud.google.com/**
2. Select your project (or create one if needed)
3. Go to **APIs & Services** → **Credentials**

### Step 2: Find Your OAuth 2.0 Client ID

Your current Client ID: `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`

1. In the **Credentials** page, find your OAuth 2.0 Client ID
2. Click on it to edit

### Step 3: Add Authorized JavaScript Origins

In the **Authorized JavaScript origins** section, click **+ ADD URI** and add:

#### ✅ Production (Vercel):
```
https://frontend-wine-iota-46.vercel.app
```

#### ✅ Development (Local):
```
http://localhost:3000
http://localhost:5173
http://127.0.0.1:3000
http://127.0.0.1:5173
```

**Note:** Vercel may assign different URLs. If you have a custom domain, add that too!

### Step 4: Add Authorized Redirect URIs

In the **Authorized redirect URIs** section, add:

#### ✅ Production:
```
https://frontend-wine-iota-46.vercel.app
https://frontend-wine-iota-46.vercel.app/login
```

#### ✅ Development:
```
http://localhost:3000
http://localhost:3000/login
http://127.0.0.1:3000
http://127.0.0.1:3000/login
```

### Step 5: Save Changes

1. Click **SAVE** at the bottom
2. Wait 1-2 minutes for changes to propagate

### Step 6: Test

1. Go to: `https://frontend-wine-iota-46.vercel.app`
2. Try "Sign in with Google" again
3. It should work now! ✅

## Quick Visual Guide

```
Google Cloud Console
└── APIs & Services
    └── Credentials
        └── OAuth 2.0 Client IDs
            └── [Your Client ID]
                ├── Authorized JavaScript origins
                │   ├── https://frontend-wine-iota-46.vercel.app
                │   └── http://localhost:3000
                └── Authorized redirect URIs
                    ├── https://frontend-wine-iota-46.vercel.app
                    └── http://localhost:3000
```

## Troubleshooting

### Still getting the error?

1. **Check your exact Vercel URL:**
   - Go to Vercel Dashboard → Your Project
   - Copy the exact production URL
   - Make sure it matches exactly (including `https://`)

2. **Wait a few minutes:**
   - Google changes can take 1-5 minutes to propagate

3. **Clear browser cache:**
   - Clear cookies/cache for Google and your site
   - Try in incognito/private mode

4. **Check for typos:**
   - URLs must be exact (no trailing slashes unless needed)
   - Must use `https://` for production, `http://` for localhost

### If you have a custom domain:

If you set up a custom domain on Vercel (e.g., `antitheft.yourdomain.com`), add that too:

```
https://antitheft.yourdomain.com
```

## Summary

✅ Your Client ID: `913466167374-2t1no6si29f0phe28pef83oaolv836pm.apps.googleusercontent.com`  
✅ Add: `https://frontend-wine-iota-46.vercel.app` to JavaScript origins  
✅ Add: `http://localhost:3000` for local development  
✅ Save and wait 1-2 minutes  
✅ Test again!

---

**Need Help?**
- Google OAuth Docs: https://developers.google.com/identity/protocols/oauth2
- Error Details: The error page should have a "see error details" link
