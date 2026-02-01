# Location Tracking Troubleshooting

If your device doesn't show on the map or tracking fails, follow this guide.

## Fixes Applied (Feb 2025)

### 1. KL Area Location Acceptance (Main Fix)
**Problem:** When testing in Kuala Lumpur (or indoors where GPS fails), the agent used IP geolocation. The system previously rejected KL-area IP locations assuming they were wrong (ISP routing issues for Melaka users).

**Fix:** The agent now **accepts** KL-area approximate locations by default. Your device will show on the map even when:
- You're indoors (no GPS lock)
- Windows Location Services fails
- IP geolocation returns KL coordinates

**Config:** In `device_agent/config.json`:
```json
"allow_kl_approximate_location": true
```
- `true` (default): Accept KL locations – use if you're in KL or testing
- `false`: Reject KL IP geolocation – use only if you're in Melaka and KL is wrong for your ISP

### 2. Backend Large Jump Rejection
**Problem:** Backend rejected location updates when device "jumped" 10km+ to KL area with `location_unchanged` flag.

**Fix:** Backend no longer rejects when `location_approximate` is true (agent explicitly accepts approximate location).

### 3. Windows Location Permissions
If GPS still fails and you want accurate tracking:

1. Press **Win+I** → **Privacy & Security** → **Location**
2. Turn ON **Location services**
3. Turn ON **Allow desktop apps to access your location**
4. Restart the device agent

### 4. Reset Stale Device Location (Database)
If the device had a wrong/old location and updates are rejected:

- Clear `last_lat` and `last_lng` for that device in your database, OR
- Delete and re-register the device

### 5. Coordinate Swapping
The system auto-detects and corrects swapped lat/lng (common with Windows Location API). No action needed.

## Testing Checklist

1. **Agent logs** (`device_agent/agent.log`): Check for "Using IP geolocation" or "Reporting approximate KL location"
2. **Windows Location**: Ensure it's enabled in Settings
3. **Test outdoors**: GPS works better outside for accurate fix
4. **Backend**: Verify `last_location_update` changes when agent reports
