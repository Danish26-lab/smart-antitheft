# 📥 How to Download Agent Folder

## Option 1: GitHub (Recommended - If Your Project is on GitHub)

### If your project is on GitHub:

1. **Go to your GitHub repository**
2. **Navigate to the `device_agent` folder**
3. **Click "Download ZIP"** or use the green "Code" button
4. **Extract the ZIP file**
5. **Double-click `INSTALL.bat`**

### Direct Download Link Format:
```
https://github.com/YOUR_USERNAME/YOUR_REPO/archive/refs/heads/main.zip
```

Then extract and navigate to `YOUR_REPO-main/device_agent/`

---

## Option 2: Google Drive / OneDrive / Dropbox

### Steps:
1. **Upload the `device_agent` folder** to Google Drive/OneDrive/Dropbox
2. **Right-click the folder** → "Share" or "Get link"
3. **Set permissions** to "Anyone with the link can view"
4. **Send the link** to your friend
5. **Friend downloads** the folder
6. **Friend extracts** and runs `INSTALL.bat`

### Google Drive:
- Upload folder to Google Drive
- Right-click → Share → "Anyone with the link"
- Copy link and send to friend
- Friend clicks link → Download button

### OneDrive:
- Upload folder to OneDrive
- Right-click → Share → "Anyone with the link"
- Copy link and send to friend
- Friend clicks link → Download

### Dropbox:
- Upload folder to Dropbox
- Right-click → Share → "Create link"
- Copy link and send to friend
- Friend clicks link → Download

---

## Option 3: Create Download ZIP

### Create a ZIP file:
1. **Right-click the `device_agent` folder**
2. **Select "Send to" → "Compressed (zipped) folder"**
3. **Name it:** `antitheft-agent-installer.zip`
4. **Upload to any file sharing service**
5. **Send download link to friend**

### Friend's Steps:
1. Click download link
2. Download `antitheft-agent-installer.zip`
3. Extract the ZIP file
4. Double-click `INSTALL.bat`

---

## Option 4: Direct File Hosting

### Use Free File Hosting Services:
- **WeTransfer**: https://wetransfer.com
- **SendAnywhere**: https://send-anywhere.com
- **File.io**: https://www.file.io
- **Temporary File Hosting**: https://tmpfiles.org

### Steps:
1. **Create ZIP** of `device_agent` folder
2. **Upload to file hosting service**
3. **Get download link**
4. **Send link to friend**
5. **Friend downloads and extracts**

---

## Option 5: Create a Simple Download Page

Create a simple HTML page that provides download link:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Download Anti-Theft Agent</title>
</head>
<body>
    <h1>Download Anti-Theft Agent</h1>
    <p>Click the button below to download the agent installer:</p>
    <a href="antitheft-agent-installer.zip" download>
        <button>Download Agent Installer</button>
    </a>
    <h2>Installation Instructions:</h2>
    <ol>
        <li>Download the ZIP file</li>
        <li>Extract the ZIP file</li>
        <li>Double-click INSTALL.bat</li>
        <li>Wait for installation to complete</li>
        <li>Done!</li>
    </ol>
</body>
</html>
```

Host this on your Vercel frontend or any web hosting.

---

## Option 6: GitHub Releases (Best for Distribution)

### If using GitHub:

1. **Create a Release:**
   - Go to your GitHub repo
   - Click "Releases" → "Create a new release"
   - Tag: `v1.0.0`
   - Title: "Agent Installer v1.0.0"
   - Upload `device_agent.zip` as release asset
   - Publish release

2. **Friend Downloads:**
   - Go to: `https://github.com/YOUR_USERNAME/YOUR_REPO/releases`
   - Download `device_agent.zip` from latest release
   - Extract and run `INSTALL.bat`

---

## Quick Setup Script for You

Create a script to package the agent for distribution:

### `CREATE_DISTRIBUTION.bat`:
```batch
@echo off
echo Creating distribution package...
cd device_agent
powershell Compress-Archive -Path * -DestinationPath ..\antitheft-agent-installer.zip -Force
cd ..
echo.
echo [OK] Distribution package created: antitheft-agent-installer.zip
echo.
echo Upload this file to:
echo   - Google Drive / OneDrive / Dropbox
echo   - GitHub Releases
echo   - File hosting service
echo   - Your website
echo.
pause
```

---

## Recommended Approach

**Best Option: GitHub Releases**
- Professional
- Version control
- Easy updates
- Direct download links
- No expiration

**Alternative: Google Drive**
- Easy to set up
- Free
- Good for one-time sharing
- Simple for non-technical users

---

## Instructions to Send to Friend

Copy and send this to your friend:

```
Hi! To install the anti-theft agent on your laptop:

1. Download the agent folder from this link: [YOUR_LINK_HERE]
2. Extract the ZIP file (right-click → Extract All)
3. Open the device_agent folder
4. Double-click INSTALL.bat
5. Wait for installation to complete (2-3 minutes)
6. Done! The agent is now running.

That's it! No configuration needed - everything is automatic.
```

---

## Security Note

If sharing via public links:
- The agent code is safe to share (it only connects to your backend)
- No sensitive credentials in the agent
- Agent auto-registers securely
- All communication is HTTPS

---

**Choose the method that works best for you!** 🚀
