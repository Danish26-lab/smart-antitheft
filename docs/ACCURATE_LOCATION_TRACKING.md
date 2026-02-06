# Getting Exact / Accurate Device Location

If the device shows the **wrong location** on the map (e.g. far from where the laptop actually is), use these steps so the agent can report the **exact location** for real tracking (e.g. if the device is stolen).

## 1. Enable Windows Location Services (best accuracy)

- **Settings** → **Privacy & Security** → **Location**
- Turn **Location** **On**
- Under "Allow access to location on this device", ensure it's **On**
- Under "Let apps access your location", turn **On**
- Under **"Let desktop apps access your location"**, turn **On** (this allows the agent to get GPS/WiFi location)

## 2. Allow the agent to use location

When the agent runs, Windows may prompt: **"Allow Python to access your location?"** or **"Allow PowerShell to access your location?"**  
→ Choose **Yes**.

If you already denied it:

- **Settings** → **Privacy & Security** → **Location**
- Scroll to **"Choose which apps can access your location"**
- Enable **Python** and/or **Microsoft Edge** (if the agent runs from a shortcut) or the app you use to run the agent

## 3. Optional: Google Maps API key (WiFi-based fallback)

If GPS is slow or unavailable (e.g. indoors), the agent can use **WiFi-based** location (Google Geolocation API), which is more accurate than IP-only.

- In the agent folder, edit **config.json**
- Set **"google_maps_api_key"** to your API key (create one in Google Cloud Console with Geolocation API enabled)
- Restart the agent

Then the agent will try, in order:

1. **Windows Location (GPS/WiFi)** – best accuracy when Location is on  
2. **Google Geolocation (WiFi scan)** – good when GPS is slow or off  
3. **IP geolocation** – last resort, often wrong (e.g. ISP location)

## 4. Restart the agent

After changing location settings:

- Restart the device agent (or reboot the PC)
- Wait 1–2 minutes; the first fix can take a bit longer
- In the dashboard, use **Refresh Location** to see the updated position

## Summary

| Setting | Result |
|--------|--------|
| Location **Off** or desktop apps **blocked** | Only IP or approximate location → **wrong** for tracking |
| Location **On** + desktop apps **allowed** | GPS/WiFi from Windows → **exact** or near-exact location |
| + Google API key | Faster WiFi-based location when GPS is slow → **better** tracking |

For **stolen device** tracking, enable **Location** and **desktop app access** so the agent can report the real position.
