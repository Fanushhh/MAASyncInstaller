# OAuth Troubleshooting Guide

## ❌ "Invalid redirect_uri" Error

This error occurs when the redirect URI is not properly configured in your Dropbox app settings.

### 🔧 Solution:

1. **Go to Dropbox Developers Console:**
   - Visit: https://www.dropbox.com/developers/apps
   - Click on your app name

2. **Configure Redirect URIs:**
   - Go to the **"Settings"** tab
   - Scroll down to **"OAuth 2"** section
   - Under **"Redirect URIs"**, add BOTH of these:
     ```
     http://localhost:8080/oauth/callback
     http://127.0.0.1:8080/oauth/callback
     ```
   - Click **"Add"** for each URI
   - Make sure both URIs are saved

3. **Verify Configuration:**
   - You should see both URIs listed under "Redirect URIs"
   - If they're not there, add them again

4. **Try Authorization Again:**
   - Return to the installer
   - Click "Authorize with Dropbox" again

## 🔥 Other Common Issues:

### "Could not start OAuth server"
- **Cause:** Port 8080 is already in use
- **Solution:** Close other applications using port 8080, or restart your computer

### "OAuth timeout"
- **Cause:** Browser didn't complete authorization in 5 minutes
- **Solution:** Try again, complete authorization faster

### "No response received"
- **Cause:** Firewall blocking localhost connections
- **Solution:** Temporarily disable firewall or allow Python through firewall

### "App Key/Secret incorrect"
- **Cause:** Copy/paste error from Dropbox console
- **Solution:** Double-check App Key and App Secret from your Dropbox app settings

## ✅ Verification Steps:

1. **Check Dropbox App Settings:**
   - App created with "Scoped access"
   - Permissions enabled: files.metadata.read, files.metadata.write, files.content.read, files.content.write
   - Both redirect URIs added and saved

2. **Check Network:**
   - Internet connection working
   - No corporate firewall blocking localhost
   - No VPN interfering with local connections

3. **Check Installer:**
   - App Key and App Secret entered correctly
   - No extra spaces or characters

## 🆘 Still Having Issues?

If you're still having problems:

1. **Copy the exact error message** from the installer
2. **Screenshot your Dropbox app settings** (OAuth 2 section)
3. **Check the installer logs** for more details

The most common issue is forgetting to add BOTH redirect URIs to your Dropbox app settings!