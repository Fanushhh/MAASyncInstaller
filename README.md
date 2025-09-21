# MAA Redux Save Sync - One-Click Installer

A cross-platform GUI installer that sets up automatic save file synchronization for MAA Redux using Dropbox. Keep your game progress synchronized across all your devices with zero manual intervention.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OAuth](https://img.shields.io/badge/OAuth-2.0-green.svg)

## 🆕 **OAuth 2.0 Upgrade**

**New in this version**: Upgraded from manual access tokens to secure OAuth 2.0 with refresh tokens!

✅ **What's Better:**
- **No more token copying** - Browser-based authorization
- **Automatic token refresh** - Never expires, no manual updates needed
- **Enhanced security** - Industry-standard OAuth 2.0 protocol
- **Better user experience** - Click "Authorize" and you're done!

✅ **Backward Compatible**: Existing installations continue working

## 🚀 Features

- **OAuth 2.0 Security** - Secure refresh tokens with automatic renewal
- **One-Click Installation** - Simple GUI installer handles everything automatically
- **Cross-Platform** - Works on Windows, macOS, and Linux
- **Auto-Detection** - Automatically finds MAA Redux save files
- **Real-Time Sync** - Syncs saves when you start/close the game
- **Safe Backups** - Creates local backups before each sync operation
- **Background Operation** - Runs silently in the background
- **Easy Management** - Helper scripts for manual control
- **Conflict-Free** - Intelligent sync timing prevents save corruption
- **Token-Free** - No manual token copying, browser-based authorization

## 📋 Requirements

- **Python 3.8+** (Download from [python.org](https://python.org))
- **Dropbox Account** (Free tier is sufficient)
- **MAA Redux** installed on your system
- **Internet Connection** for Dropbox synchronization

## 🔧 Installation

### Step 1: Download
```bash
git clone https://github.com/Fanushhh/MAASyncInstaller.git
cd MAASyncInstaller
```

### Step 2: Run the Installer
```bash
python maa_redux_installer.py
```

### Step 3: Follow the GUI Setup
1. **Setup Dropbox App** - Click "Setup Dropbox App" for detailed instructions
2. **Enter App Credentials** - Copy App Key and App Secret from your Dropbox app
3. **Authorize with Dropbox** - Browser-based OAuth authorization (no token copying!)
4. **Select Save File** - Use "Auto-Detect" or "Browse" manually
5. **Choose Install Location** - Default location works for most users
6. **Install & Setup** - Click to complete installation

## 🔑 Dropbox OAuth Setup

### Creating Your Dropbox App
1. Visit [Dropbox Developers](https://www.dropbox.com/developers/apps)
2. Click **"Create app"**
3. Choose **"Scoped access"**
4. Choose **"App folder"** (recommended for security)
5. Enter app name: **"MAA-Redux-Sync"**
6. Click **"Create app"**

### Setting Permissions
Navigate to the **Permissions** tab and enable:
- ✅ `files.metadata.read`
- ✅ `files.metadata.write`
- ✅ `files.content.read`
- ✅ `files.content.write`

Click **"Submit"** to save permissions.

### Configure OAuth Settings
1. Go to **Settings** tab
2. Copy **"App key"** and **"App secret"** to the installer
3. In **"OAuth 2"** section, add these **Redirect URIs**:
   - `http://localhost:8080/oauth/callback`
   - `http://127.0.0.1:8080/oauth/callback`
4. Click **"Add"** for both URIs
5. Click **"Authorize with Dropbox"** in the installer

### Browser Authorization
- Your browser will open automatically
- Log in to Dropbox and click **"Allow"**
- The browser tab will close automatically
- Return to the installer - you're now authorized!

> 🔒 **Security**: Uses OAuth 2.0 with refresh tokens - more secure than access tokens!

## 🎮 How It Works

### Automatic Sync Flow
1. **Game Start**: Downloads latest save from Dropbox before MAA Redux loads
2. **Game Play**: You play normally, no interruption
3. **Game Exit**: Uploads your save to Dropbox after MAA Redux closes
4. **Cross-Device**: Same process happens on all your configured devices

### Smart Conflict Prevention
- Only syncs when the game is completely closed
- Creates backups before each download
- 30-second cooldown prevents rapid sync conflicts
- Monitors actual game processes, not just files

## 📁 File Structure

After installation, you'll find:

```
MAA-Redux-Sync/
├── maa_sync.py              # Main sync script
├── dropbox_oauth.py         # OAuth 2.0 helper module
├── config.json              # Configuration file
├── sync.log                 # Activity logs
├── backups/                 # Local save backups
├── start_sync.bat/.sh       # Start sync manually
├── stop_sync.bat/.sh        # Stop sync service
├── manual_import.bat/.sh    # Force download from Dropbox
└── manual_upload.bat/.sh    # Force upload to Dropbox
```

## 🛠️ Manual Controls

### Windows
- **Start Sync**: Double-click `start_sync.bat`
- **Stop Sync**: Double-click `stop_sync.bat`
- **Manual Import**: Double-click `manual_import.bat`
- **Manual Upload**: Double-click `manual_upload.bat`

### macOS/Linux
```bash
./start_sync.sh        # Start sync service
./stop_sync.sh         # Stop sync service
./manual_import.sh     # Download save from Dropbox
./manual_upload.sh     # Upload save to Dropbox
```

## 📊 Monitoring

### Log Files
- **sync.log** - Main activity log
- **sync_error.log** - Error logs (macOS only)

### Status Check
```bash
# View recent activity
tail -f sync.log

# Test configuration
python maa_sync.py --test
```

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
    "app_name": "MAA Redux",
    "save_file_path": "/path/to/your/save.dat",
    "dropbox_app_key": "your_app_key_here",
    "dropbox_app_secret": "your_app_secret_here",
    "dropbox_access_token": "auto_managed_by_oauth",
    "dropbox_refresh_token": "auto_managed_by_oauth",
    "dropbox_folder": "/SyncedFiles",
    "sync_filename": "save.dat"
}
```

> 📝 **Note**: OAuth tokens are automatically managed - no manual editing needed!

## 🚨 Troubleshooting

### Common Issues

**Save not syncing?**
- Check `sync.log` for error messages
- Verify MAA Redux is completely closed before switching devices
- Test connection with `python maa_sync.py --test`

**Dropbox connection failed?**
- Re-authorize using "Authorize with Dropbox" button
- Check internet connection
- Ensure Dropbox app permissions are properly set
- Verify redirect URIs are configured correctly

**Game not detected?**
- Update `app_name` in `config.json` if MAA Redux executable name is different
- Check if game is running as administrator (may hide from process detection)

**Installation failed?**
- Ensure Python 3.8+ is installed
- Check write permissions to installation directory
- Try running installer as administrator (Windows)

### Manual Recovery

**Restore from backup:**
```bash
# Navigate to installation directory
cd /path/to/MAA-Redux-Sync

# List available backups
ls backups/

# Copy backup to save location
cp "backups/backup_YYYYMMDD_HHMMSS_save.dat" "/path/to/game/save.dat"
```

## 🔒 Security & Privacy

- **OAuth 2.0 Security**: Industry-standard authentication with refresh tokens
- **Automatic Token Refresh**: Tokens renew automatically without user intervention
- **Local Processing**: All sync logic runs locally on your machine
- **App Folder Access**: Dropbox app only accesses its own folder
- **Encrypted Transfer**: All data transfers use Dropbox's encryption
- **No External Dependencies**: No third-party services besides Dropbox
- **Open Source**: Full source code available for review
- **Revokable Access**: Users can revoke authorization anytime from Dropbox settings

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- MAA Redux community for game development
- Dropbox for providing reliable cloud storage API
- Python community for excellent cross-platform libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/MAASyncInstaller/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/MAASyncInstaller/discussions)
- **Documentation**: This README and inline code comments

---

**Made with ❤️ for the MAA Redux community**

*Keep your saves safe, keep your progress synced!*
