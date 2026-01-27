# Frontend API URL Update Guide

## Status

I've created a centralized API client (`src/api/axios.js`) and updated some files, but there are still many hardcoded `http://localhost:5000` URLs that need updating.

## Quick Fix: Use Search & Replace

You can quickly update all remaining files by:

1. **Search for:** `http://localhost:5000`
2. **Replace with:** Use `apiClient` from `../api/axios` instead

## Files Already Updated
- ✅ `src/pages/Login.jsx` - Partially updated
- ✅ `src/pages/SignUp.jsx` - Partially updated  
- ✅ `src/App.jsx` - Updated
- ✅ `src/pages/Dashboard.jsx` - Updated
- ✅ `src/pages/Devices.jsx` - Partially updated

## Files Still Need Updates
- ⚠️ `src/pages/DeviceDetail.jsx` - Many API calls
- ⚠️ `src/pages/BreachReport.jsx` - API calls
- ⚠️ `src/pages/MissingMode.jsx` - API calls
- ⚠️ `src/components/FileBrowser.jsx` - API calls

## Pattern to Use

**Before:**
```javascript
import axios from 'axios'
...
await axios.get('http://localhost:5000/api/endpoint')
```

**After:**
```javascript
import apiClient from '../api/axios'
...
await apiClient.get('/api/endpoint')
```

The `apiClient` automatically:
- Adds base URL (Vercel backend in production, localhost in dev)
- Adds auth token from localStorage
- Handles errors

## Alternative: Global Find & Replace

If you want to do it all at once:
1. Find: `'http://localhost:5000`
2. Replace: (empty - remove it)
3. Change `axios.get('...` to `apiClient.get('...`
4. Change `axios.post('...` to `apiClient.post('...`

But be careful - some files might need special handling!
