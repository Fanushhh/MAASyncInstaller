#!/usr/bin/env python3
"""
MAA Redux Save Sync - One-Click Installer
Cross-platform GUI installer with automatic save file detection
"""

import os
import sys
import json
import platform
import subprocess
import threading
import webbrowser
import shutil
from pathlib import Path
from tkinter import *
from tkinter import ttk, messagebox, filedialog
import tkinter as tk

class MAAReduxSyncInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MAA Redux Save Sync - Installer")
        self.root.geometry("850x700")
        self.root.resizable(True, True)
        self.root.minsize(650, 500)
        
        # Set window icon if available
        try:
            self.root.iconbitmap('icon.ico')  # Optional: add an icon file
        except:
            pass
        
        # Variables
        self.dropbox_app_key = StringVar()
        self.dropbox_app_secret = StringVar()
        self.save_file_path = StringVar()
        self.app_name = StringVar(value="MAA Redux")
        self.install_location = StringVar()
        self.auto_start = BooleanVar(value=True)

        # OAuth status
        self.oauth_authorized = BooleanVar(value=False)
        
        # System detection
        self.system = platform.system()
        self.setup_default_paths()
        
        # GUI setup
        self.create_widgets()
        self.detect_save_files()
        
    def setup_default_paths(self):
        """Setup default installation paths based on OS"""
        if self.system == "Windows":
            default_install = Path.home() / "MAA-Redux-Sync"
        else:  # macOS/Linux
            default_install = Path.home() / "maa-redux-sync"
        
        self.install_location.set(str(default_install))
    
    def create_widgets(self):
        """Create the main GUI"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Create scrollable content area with proper width management
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Configure scrollable frame to update canvas scroll region
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", configure_scroll_region)

        # Configure canvas window to fill available width
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.bind("<Configure>", configure_canvas_window)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        # Pack canvas and scrollbar properly
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Use scrollable_frame for content
        content_frame = scrollable_frame
        
        # Title
        title_label = ttk.Label(content_frame, text="MAA Redux Save Sync Installer",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Description
        desc_text = ("This installer will set up automatic save file synchronization "
                    "between your devices using Dropbox. Your game progress will be "
                    "automatically synced across Windows and Mac.")
        desc_label = ttk.Label(content_frame, text=desc_text, wraplength=700, justify=CENTER)
        desc_label.pack(pady=(0, 20))

        # Progress bar (hidden initially)
        self.progress_var = DoubleVar()
        self.progress_bar = ttk.Progressbar(content_frame, variable=self.progress_var,
                                          maximum=100, length=400)

        # Status label
        self.status_label = ttk.Label(content_frame, text="Ready to install",
                                     font=("Arial", 10))
        self.status_label.pack(pady=(0, 10))

        # Configuration frame
        config_frame = ttk.LabelFrame(content_frame, text="Configuration", padding=15)
        config_frame.pack(fill=X, pady=(0, 10))

        self.create_config_widgets(config_frame)

        # Installation frame
        install_frame = ttk.LabelFrame(content_frame, text="Installation", padding=15)
        install_frame.pack(fill=X, pady=(0, 10))

        self.create_install_widgets(install_frame)

        # Buttons frame (keep outside scrollable area for always visible)
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(10, 10))

        self.create_buttons(button_frame)
    
    def create_config_widgets(self, parent):
        """Create configuration input widgets"""

        # Dropbox OAuth Configuration
        ttk.Label(parent, text="Dropbox OAuth Settings:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=W, pady=(0, 5))

        # App Key
        ttk.Label(parent, text="App Key:").grid(row=1, column=0, sticky=W, pady=(0, 2))
        app_key_frame = ttk.Frame(parent)
        app_key_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=(0, 10))

        app_key_entry = ttk.Entry(app_key_frame, textvariable=self.dropbox_app_key, width=40)
        app_key_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        # App Secret
        ttk.Label(parent, text="App Secret:").grid(row=3, column=0, sticky=W, pady=(0, 2))
        app_secret_frame = ttk.Frame(parent)
        app_secret_frame.grid(row=4, column=0, columnspan=2, sticky=EW, pady=(0, 10))

        app_secret_entry = ttk.Entry(app_secret_frame, textvariable=self.dropbox_app_secret,
                                   width=40, show="*")
        app_secret_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        # OAuth Authorization
        oauth_frame = ttk.Frame(parent)
        oauth_frame.grid(row=5, column=0, columnspan=2, sticky=EW, pady=(10, 15))

        self.auth_status_label = ttk.Label(oauth_frame, text="Not Authorized",
                                          font=("Arial", 9), foreground="red")
        self.auth_status_label.pack(side=LEFT, padx=(0, 10))

        ttk.Button(oauth_frame, text="Setup Dropbox App",
                  command=self.open_dropbox_setup).pack(side=RIGHT, padx=(10, 0))

        self.auth_button = ttk.Button(oauth_frame, text="Authorize with Dropbox",
                                     command=self.authorize_dropbox)
        self.auth_button.pack(side=RIGHT, padx=(5, 0))
        
        # Save File Location
        ttk.Label(parent, text="Save File Location:", font=("Arial", 10, "bold")).grid(
            row=6, column=0, sticky=W, pady=(15, 5))

        file_frame = ttk.Frame(parent)
        file_frame.grid(row=7, column=0, columnspan=2, sticky=EW, pady=(0, 15))

        file_entry = ttk.Entry(file_frame, textvariable=self.save_file_path, width=40)
        file_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))

        ttk.Button(file_frame, text="Browse",
                  command=self.browse_save_file).pack(side=RIGHT, padx=(10, 0))

        ttk.Button(file_frame, text="Auto-Detect",
                  command=self.detect_save_files).pack(side=RIGHT, padx=(5, 0))

        # App Name
        ttk.Label(parent, text="Application Name:", font=("Arial", 10, "bold")).grid(
            row=8, column=0, sticky=W, pady=(0, 5))

        ttk.Entry(parent, textvariable=self.app_name, width=30).grid(
            row=9, column=0, sticky=W, pady=(0, 10))
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
    
    def create_install_widgets(self, parent):
        """Create installation option widgets"""
        
        # Installation Location
        ttk.Label(parent, text="Install Location:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=W, pady=(0, 5))
        
        location_frame = ttk.Frame(parent)
        location_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(0, 15))
        
        location_entry = ttk.Entry(location_frame, textvariable=self.install_location,
                                  width=40)
        location_entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        ttk.Button(location_frame, text="Browse", 
                  command=self.browse_install_location).pack(side=RIGHT, padx=(10, 0))
        
        # Auto-start option
        ttk.Checkbutton(parent, text="Start automatically with system", 
                       variable=self.auto_start).grid(row=2, column=0, sticky=W)
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
    
    def create_buttons(self, parent):
        """Create action buttons"""

        # Configure parent padding to ensure visibility
        parent.configure(relief='flat', borderwidth=2)

        # Left side - Help
        help_frame = ttk.Frame(parent)
        help_frame.pack(side=LEFT, pady=10)

        help_button = ttk.Button(help_frame, text="Help & Guide",
                               command=self.show_help)
        help_button.pack(side=LEFT, padx=(0, 10), ipadx=10, ipady=5)

        # Right side - Actions
        action_frame = ttk.Frame(parent)
        action_frame.pack(side=RIGHT, pady=10)

        test_button = ttk.Button(action_frame, text="Test Configuration",
                               command=self.test_config)
        test_button.pack(side=RIGHT, padx=(0, 10), ipadx=10, ipady=5)

        self.install_button = ttk.Button(action_frame, text="Install & Setup",
                                       command=self.start_installation)
        self.install_button.pack(side=RIGHT, ipadx=10, ipady=5)
    
    def detect_save_files(self):
        """Auto-detect MAA Redux save files"""
        self.update_status("Detecting save files...")

        save_files = []
        common_locations = []

        if self.system == "Windows":
            common_locations = [
                Path.home() / "AppData" / "Roaming" / "MAA Redux",
                Path.home() / "AppData" / "Local" / "MAA Redux",
                Path.home() / "Documents" / "MAA Redux",
                Path("C:") / "Program Files" / "MAA Redux",
                Path("C:") / "Program Files (x86)" / "MAA Redux",
                Path.home() / "Downloads"
            ]
        else:  # macOS/Linux
            common_locations = [
                Path.home() / "Library" / "Application Support" / "MAA Redux",
                Path.home() / "Documents" / "MAA Redux",
                Path.home() / "Downloads",
                Path("/Applications") / "MAA Redux.app" / "Contents" / "Resources"
            ]

        # Search for save files (common extensions)
        save_extensions = ["*.save", "*.dat", "*.sav", "*.data", "*.json"]

        for location in common_locations:
            if location.exists():
                for ext in save_extensions:
                    for save_file in location.rglob(ext):
                        # Filter for files that might be save files
                        if self.is_likely_save_file(save_file):
                            save_files.append(save_file)

        if save_files:
            # Automatically use the first found file and open file browser for user to confirm/change
            if len(save_files) == 1:
                self.save_file_path.set(str(save_files[0]))
                self.update_status(f"Auto-detected save file: {save_files[0].name}")
            else:
                # Use the first detected file but let user know they can browse for others
                self.save_file_path.set(str(save_files[0]))
                self.update_status(f"Found {len(save_files)} save files. Selected: {save_files[0].name}")
                messagebox.showinfo("Multiple Files Found",
                                   f"Found {len(save_files)} potential save files.\n"
                                   f"Selected: {save_files[0].name}\n\n"
                                   f"Use 'Browse' button if you need to select a different file.")
        else:
            self.update_status("No save files found. Please select manually.")
            messagebox.showinfo("Auto-Detection",
                               "No MAA Redux save files found automatically.\n"
                               "Please use 'Browse' to select your save file manually.")
    
    def is_likely_save_file(self, file_path):
        """Check if a file is likely a save file"""
        filename = file_path.name.lower()
        
        # Common save file indicators
        save_indicators = [
            "save", "player", "game", "progress", "data", 
            "profile", "user", "account", "config"
        ]
        
        # Check if filename contains save indicators
        for indicator in save_indicators:
            if indicator in filename:
                return True
        
        # Check file size (save files are typically small-medium size)
        try:
            size = file_path.stat().st_size
            return 100 < size < 50 * 1024 * 1024  # Between 100 bytes and 50MB
        except:
            return False
    
    
    def browse_save_file(self):
        """Browse for save file"""
        file_path = filedialog.askopenfilename(
            title="Select MAA Redux Save File",
            filetypes=[
                ("Save files", "*.save"),
                ("Data files", "*.dat"),
                ("Saved games", "*.sav"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.save_file_path.set(file_path)
    
    def browse_install_location(self):
        """Browse for installation directory"""
        dir_path = filedialog.askdirectory(title="Select Installation Directory")
        if dir_path:
            self.install_location.set(dir_path)
    
    def open_dropbox_setup(self):
        """Open Dropbox developer page and show instructions"""
        webbrowser.open("https://www.dropbox.com/developers/apps")

        instructions = """Dropbox OAuth App Setup Instructions:

1. Click "Create app" on the opened page
2. Choose "Scoped access"
3. Choose "App folder" (recommended for security)
4. Enter app name: "MAA-Redux-Sync"
5. Click "Create app"

6. Go to "Permissions" tab and enable:
   ✓ files.metadata.read
   ✓ files.metadata.write
   ✓ files.content.read
   ✓ files.content.write

7. Click "Submit"

8. Go to "Settings" tab:
   - Copy "App key" and paste it in the installer
   - Copy "App secret" and paste it in the installer

9. ⚠️  IMPORTANT - Add Redirect URI:
   In "OAuth 2" section, under "Redirect URIs":
   - Add: http://localhost:8080/oauth/callback
   - Add: http://127.0.0.1:8080/oauth/callback
   - Click "Add" for BOTH URIs

10. Make sure to click "Add" and save the redirect URIs!

11. Click "Authorize with Dropbox" in the installer
    to complete the OAuth flow

Note: Both localhost and 127.0.0.1 URIs are needed for compatibility.
This method is more secure than access tokens as it uses
refresh tokens that can be automatically renewed!"""

        messagebox.showinfo("Dropbox OAuth Setup", instructions)

    def authorize_dropbox(self):
        """Start OAuth authorization flow"""
        app_key = self.dropbox_app_key.get().strip()
        app_secret = self.dropbox_app_secret.get().strip()

        if not app_key:
            messagebox.showerror("Missing App Key", "Please enter your Dropbox App Key first")
            return

        if not app_secret:
            messagebox.showerror("Missing App Secret", "Please enter your Dropbox App Secret first")
            return

        # Validate App Key format (Dropbox app keys are typically alphanumeric)
        if len(app_key) < 10:
            messagebox.showerror("Invalid App Key",
                               "App Key seems too short. Please check that you copied the complete App Key from Dropbox.")
            return

        if len(app_secret) < 10:
            messagebox.showerror("Invalid App Secret",
                               "App Secret seems too short. Please check that you copied the complete App Secret from Dropbox.")
            return

        try:
            from dropbox_oauth import DropboxTokenManager

            # Create token manager
            config_path = "temp_oauth_config.json"
            token_manager = DropboxTokenManager(
                config_path,
                app_key,
                app_secret
            )

            self.update_status("Starting OAuth authorization...")
            self.auth_button.config(state=DISABLED)

            # Start authorization in thread to avoid blocking UI
            auth_thread = threading.Thread(target=self._perform_oauth, args=(token_manager,))
            auth_thread.daemon = True
            auth_thread.start()

        except ImportError:
            messagebox.showerror("Error", "OAuth module not found. Please ensure dropbox_oauth.py is available.")
        except Exception as e:
            messagebox.showerror("Authorization Error", f"Failed to start authorization: {str(e)}")
            self.auth_button.config(state=NORMAL)

    def _perform_oauth(self, token_manager):
        """Perform OAuth in background thread"""
        try:
            # Show instruction
            self.root.after(0, lambda: messagebox.showinfo(
                "Browser Authorization",
                "Your browser will open for Dropbox authorization.\n\n"
                "1. Log in to your Dropbox account\n"
                "2. Click 'Allow' to authorize the app\n"
                "3. The browser tab will close automatically\n"
                "4. Return to this installer\n\n"
                "This may take up to 5 minutes to complete."
            ))

            # Perform authorization
            success = token_manager.authorize_new_user()

            if success:
                self.root.after(0, self._oauth_success)
            else:
                self.root.after(0, self._oauth_failed, "Authorization was cancelled or failed")

        except Exception as e:
            self.root.after(0, self._oauth_failed, str(e))

    def _oauth_success(self):
        """Handle successful OAuth"""
        self.oauth_authorized.set(True)
        self.auth_status_label.config(text="✓ Authorized", foreground="green")
        self.auth_button.config(text="Re-authorize", state=NORMAL)
        self.update_status("Dropbox authorization successful!")
        messagebox.showinfo("Success", "Dropbox authorization completed successfully!\n\n"
                                      "You can now proceed with installation.")

    def _oauth_failed(self, error_msg):
        """Handle failed OAuth"""
        self.oauth_authorized.set(False)
        self.auth_status_label.config(text="❌ Failed", foreground="red")
        self.auth_button.config(state=NORMAL)
        self.update_status("Dropbox authorization failed")

        # Check for specific error types
        error_lower = error_msg.lower()

        if "redirect_uri" in error_lower or "bad request" in error_lower or "invalid_request" in error_lower:
            messagebox.showerror("App Configuration Error",
                               f"❌ Configuration Error\n\n"
                               f"There's an issue with your Dropbox app configuration.\n\n"
                               f"🔧 Check These Settings:\n\n"
                               f"1. App Key & Secret:\n"
                               f"   • Make sure they're copied correctly (no extra spaces)\n"
                               f"   • App Key should be 15+ characters\n"
                               f"   • App Secret should be 15+ characters\n\n"
                               f"2. Redirect URIs (in Dropbox app settings):\n"
                               f"   • Go to Settings tab in your Dropbox app\n"
                               f"   • Add these EXACT URIs:\n"
                               f"     - http://localhost:8080/oauth/callback\n"
                               f"     - http://127.0.0.1:8080/oauth/callback\n"
                               f"   • Click 'Add' for each URI\n\n"
                               f"3. App Type:\n"
                               f"   • Make sure you selected 'Scoped access'\n"
                               f"   • App folder or Full Dropbox access\n\n"
                               f"Error: {error_msg}")
        else:
            messagebox.showerror("Authorization Failed",
                               f"Dropbox authorization failed:\n\n{error_msg}\n\n"
                               f"Please check:\n"
                               f"• App Key and App Secret are correct\n"
                               f"• Redirect URIs are configured:\n"
                               f"  - http://localhost:8080/oauth/callback\n"
                               f"  - http://127.0.0.1:8080/oauth/callback\n"
                               f"• Internet connection is working\n"
                               f"• No firewall blocking localhost:8080")
    
    def test_config(self):
        """Test the current configuration"""
        if not self.validate_config():
            return

        self.update_status("Testing configuration...")

        try:
            # Test OAuth tokens
            from dropbox_oauth import DropboxTokenManager
            import dropbox

            config_path = "temp_oauth_config.json"
            token_manager = DropboxTokenManager(
                config_path,
                self.dropbox_app_key.get().strip(),
                self.dropbox_app_secret.get().strip()
            )

            # Get valid access token
            access_token = token_manager.get_valid_access_token()
            if not access_token:
                raise Exception("No valid access token available. Please authorize first.")

            # Test Dropbox connection
            dbx = dropbox.Dropbox(access_token)
            account = dbx.users_get_current_account()

            # Test save file access
            save_path = Path(self.save_file_path.get())
            if not save_path.exists():
                raise FileNotFoundError("Save file not found")

            # Test file permissions
            if not os.access(save_path, os.R_OK):
                raise PermissionError("Cannot read save file")

            self.update_status("Configuration test successful!")
            messagebox.showinfo("Test Result",
                               f"Configuration test successful!\n\n"
                               f"Dropbox: Connected as {account.name.display_name}\n"
                               f"Save file: Found ({save_path.name})\n"
                               f"File size: {save_path.stat().st_size} bytes\n"
                               f"OAuth: Using refresh tokens ✓")

        except ImportError as e:
            if "dropbox_oauth" in str(e):
                messagebox.showerror("Test Failed",
                                   "OAuth module not found. Please ensure dropbox_oauth.py is available.")
            else:
                messagebox.showwarning("Test Incomplete",
                                     "Dropbox module not installed. "
                                     "Installation will handle this automatically.")
        except Exception as e:
            messagebox.showerror("Test Failed", f"Configuration test failed:\n{str(e)}")
            self.update_status("Configuration test failed")
    
    def validate_config(self):
        """Validate configuration inputs"""
        if not self.dropbox_app_key.get().strip():
            messagebox.showerror("Validation Error", "Please enter your Dropbox App Key")
            return False

        if not self.dropbox_app_secret.get().strip():
            messagebox.showerror("Validation Error", "Please enter your Dropbox App Secret")
            return False

        if not self.oauth_authorized.get():
            messagebox.showerror("Validation Error", "Please authorize with Dropbox first")
            return False
        
        if not self.save_file_path.get().strip():
            messagebox.showerror("Validation Error", "Please select your save file")
            return False
        
        save_path = Path(self.save_file_path.get())
        if not save_path.exists():
            messagebox.showerror("Validation Error", "Selected save file does not exist")
            return False
        
        if not save_path.is_file():
            messagebox.showerror("Validation Error", "Selected path is not a file")
            return False
        
        if not self.app_name.get().strip():
            messagebox.showerror("Validation Error", "Please enter the application name")
            return False
        
        return True
    
    def start_installation(self):
        """Start the installation process"""
        if not self.validate_config():
            return
        
        # Disable install button
        self.install_button.config(state=DISABLED)
        
        # Show progress bar
        self.progress_bar.pack(pady=10)
        
        # Start installation in thread
        install_thread = threading.Thread(target=self.install_process)
        install_thread.daemon = True
        install_thread.start()
    
    def install_process(self):
        """Main installation process"""
        try:
            self.update_progress(0, "Starting installation...")
            
            # Step 1: Create installation directory
            self.update_progress(10, "Creating installation directory...")
            install_dir = Path(self.install_location.get())
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 2: Install Python dependencies
            self.update_progress(20, "Installing Python dependencies...")
            self.install_dependencies()
            
            # Step 3: Copy OAuth module
            self.update_progress(30, "Copying OAuth module...")
            self.copy_oauth_module(install_dir)

            # Step 4: Create main script
            self.update_progress(40, "Creating sync script...")
            self.create_sync_script(install_dir)

            # Step 5: Create configuration
            self.update_progress(60, "Creating configuration...")
            self.create_config_file(install_dir)
            
            # Step 6: Create helper scripts
            self.update_progress(70, "Creating helper scripts...")
            self.create_helper_scripts(install_dir)

            # Step 7: Setup auto-start
            if self.auto_start.get():
                self.update_progress(80, "Setting up auto-start...")
                self.setup_autostart(install_dir)

            # Step 8: Test installation
            self.update_progress(90, "Testing installation...")
            self.test_installation(install_dir)
            
            self.update_progress(100, "Installation complete!")
            
            # Show success message
            self.root.after(0, self.show_success_dialog, install_dir)
            
        except Exception as e:
            self.root.after(0, self.show_error_dialog, str(e))
    
    def install_dependencies(self):
        """Install required Python packages"""
        packages = ["psutil", "dropbox"]

        for package in packages:
            try:
                __import__(package)
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    def copy_oauth_module(self, install_dir):
        """Copy OAuth module to installation directory"""
        oauth_module_path = Path("dropbox_oauth.py")
        if oauth_module_path.exists():
            target_path = install_dir / "dropbox_oauth.py"
            shutil.copy2(oauth_module_path, target_path)
        else:
            raise FileNotFoundError("OAuth module (dropbox_oauth.py) not found in current directory")
    
    def create_sync_script(self, install_dir):
        """Create the main synchronization script"""
        
        script_content = '''#!/usr/bin/env python3
"""
MAA Redux Save Sync - Auto-generated by installer
"""

import os
import sys
import time
import json
import psutil
import shutil
import platform
import argparse
from datetime import datetime
from pathlib import Path
import logging

try:
    import dropbox
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False
    print("Warning: Dropbox module not available")

try:
    from dropbox_oauth import DropboxTokenManager
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False
    print("Warning: OAuth module not available")

# Logging setup
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sync.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class MAAReduxSync:
    def __init__(self):
        self.load_config()
        self.init_dropbox()
        self.last_upload_time = 0
        self.upload_delay = 5  # seconds to wait after game closes

    def load_config(self):
        """Load configuration from config.json"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.app_name = config['app_name']
            self.save_file_path = Path(config['save_file_path'])
            self.dropbox_folder = config.get('dropbox_folder', '/SyncedFiles')
            self.sync_filename = config.get('sync_filename', 'save.dat')

            # OAuth credentials
            self.app_key = config.get('dropbox_app_key', '')
            self.app_secret = config.get('dropbox_app_secret', '')

            # Legacy support for old access token method
            self.legacy_token = config.get('dropbox_token', '')

            logger.info(f"Configuration loaded: {self.app_name}")
            logger.info(f"OAuth available: {OAUTH_AVAILABLE}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def init_dropbox(self):
        """Initialize Dropbox connection with OAuth support"""
        if not DROPBOX_AVAILABLE:
            logger.error("Dropbox module not available")
            self.dbx = None
            self.token_manager = None
            return

        # Try OAuth first (preferred method)
        if OAUTH_AVAILABLE and self.app_key and self.app_secret:
            try:
                self.token_manager = DropboxTokenManager(
                    'config.json',
                    self.app_key,
                    self.app_secret
                )

                access_token = self.token_manager.get_valid_access_token()
                if access_token:
                    self.dbx = dropbox.Dropbox(access_token)
                    account = self.dbx.users_get_current_account()
                    logger.info(f"Connected to Dropbox via OAuth as: {account.name.display_name}")
                    return
                else:
                    logger.warning("No valid OAuth access token available")

            except Exception as e:
                logger.error(f"OAuth connection failed: {e}")

        # Fallback to legacy token method
        if self.legacy_token:
            try:
                self.dbx = dropbox.Dropbox(self.legacy_token)
                account = self.dbx.users_get_current_account()
                logger.info(f"Connected to Dropbox via legacy token as: {account.name.display_name}")
                logger.warning("Using legacy access token - consider upgrading to OAuth")
                self.token_manager = None
                return
            except Exception as e:
                logger.error(f"Legacy token connection failed: {e}")

        # No valid connection method
        logger.error("No valid Dropbox credentials available")
        self.dbx = None
        self.token_manager = None

    def refresh_dropbox_connection(self):
        """Refresh Dropbox connection if using OAuth"""
        if self.token_manager:
            try:
                access_token = self.token_manager.get_valid_access_token()
                if access_token:
                    self.dbx = dropbox.Dropbox(access_token)
                    logger.info("Dropbox connection refreshed")
                    return True
                else:
                    logger.error("Failed to get valid access token")
                    return False
            except Exception as e:
                logger.error(f"Failed to refresh connection: {e}")
                return False
        return True  # No refresh needed for legacy tokens
    
    def is_app_running(self):
        """Check if the target application is running"""
        app_name_lower = self.app_name.lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                proc_info = proc.info
                if proc_info['name'] and app_name_lower in proc_info['name'].lower():
                    return True
                if proc_info['exe'] and app_name_lower in proc_info['exe'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    
    def create_backup(self, reason="manual"):
        """Create a backup of the current save file"""
        if not self.save_file_path.exists():
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{reason}_{timestamp}_{self.save_file_path.name}"
            backup_path = self.save_file_path.parent / "backups" / backup_name
            
            # Create backups directory
            backup_path.parent.mkdir(exist_ok=True)
            
            shutil.copy2(self.save_file_path, backup_path)
            logger.info(f"Backup created: {backup_path.name}")
            return backup_path
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def quick_import(self):
        """Import save file from Dropbox before game starts"""
        if not self.dbx:
            logger.warning("Dropbox not available for import")
            return False

        try:
            remote_path = f"{self.dropbox_folder}/{self.sync_filename}"

            # Check if file exists on Dropbox
            try:
                metadata = self.dbx.files_get_metadata(remote_path)
                logger.info(f"Remote file found: {metadata.client_modified}")
            except dropbox.exceptions.AuthError:
                logger.info("Authentication error, attempting to refresh token...")
                if self.refresh_dropbox_connection():
                    # Retry after refresh
                    return self.quick_import()
                else:
                    logger.error("Failed to refresh token for import")
                    return False
            except dropbox.exceptions.ApiError:
                logger.info("No remote save file found")
                return False

            # Create backup before importing
            self.create_backup("pre_import")

            # Download from Dropbox
            try:
                self.dbx.files_download_to_file(str(self.save_file_path), remote_path)
                logger.info("Quick import successful")
                return True
            except dropbox.exceptions.AuthError:
                logger.info("Authentication error during download, attempting to refresh token...")
                if self.refresh_dropbox_connection():
                    # Retry after refresh
                    self.dbx.files_download_to_file(str(self.save_file_path), remote_path)
                    logger.info("Quick import successful after token refresh")
                    return True
                else:
                    logger.error("Failed to refresh token for download")
                    return False

        except Exception as e:
            logger.error(f"Import failed: {e}")
            return False
    
    def upload_save(self):
        """Upload save file to Dropbox after game closes"""
        if not self.dbx or not self.save_file_path.exists():
            return False

        try:
            # Read file data
            with open(self.save_file_path, 'rb') as f:
                file_data = f.read()

            # Upload to Dropbox
            remote_path = f"{self.dropbox_folder}/{self.sync_filename}"

            try:
                self.dbx.files_upload(
                    file_data,
                    remote_path,
                    mode=dropbox.files.WriteMode('overwrite')
                )

                self.last_upload_time = time.time()
                logger.info("Upload successful")
                return True

            except dropbox.exceptions.AuthError:
                logger.info("Authentication error during upload, attempting to refresh token...")
                if self.refresh_dropbox_connection():
                    # Retry after refresh
                    self.dbx.files_upload(
                        file_data,
                        remote_path,
                        mode=dropbox.files.WriteMode('overwrite')
                    )

                    self.last_upload_time = time.time()
                    logger.info("Upload successful after token refresh")
                    return True
                else:
                    logger.error("Failed to refresh token for upload")
                    return False

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def monitor(self):
        """Main monitoring loop"""
        logger.info("=== MAA Redux Save Sync Started ===")
        logger.info(f"Monitoring: {self.app_name}")
        logger.info(f"Save file: {self.save_file_path}")
        logger.info(f"Dropbox available: {self.dbx is not None}")
        
        app_was_running = False
        app_start_time = 0
        
        try:
            while True:
                is_running = self.is_app_running()
                current_time = time.time()
                
                if is_running and not app_was_running:
                    logger.info(f"Detected {self.app_name} starting...")
                    app_start_time = current_time
                    
                    # Quick import before game loads saves
                    if self.quick_import():
                        logger.info("Pre-load import successful")
                    else:
                        logger.info("No remote save to import or import failed")
                    
                    app_was_running = True
                    logger.info("Game is now running")
                    
                elif not is_running and app_was_running:
                    logger.info(f"{self.app_name} closed")
                    
                    # Wait a moment for complete shutdown and file writes
                    time.sleep(self.upload_delay)
                    
                    # Upload save if enough time has passed since last upload
                    if current_time - self.last_upload_time > 30:  # 30 second cooldown
                        if self.upload_save():
                            logger.info("Save uploaded successfully")
                        else:
                            logger.warning("Save upload failed")
                    else:
                        logger.info("Skipping upload (too soon since last upload)")
                    
                    app_was_running = False
                
                time.sleep(2)  # Check every 2 seconds
                
        except KeyboardInterrupt:
            logger.info("Sync stopped by user")
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            time.sleep(10)  # Wait before potential restart

def main():
    parser = argparse.ArgumentParser(description='MAA Redux Save Sync')
    parser.add_argument('--test', action='store_true', help='Test configuration and exit')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Import save from Dropbox and exit')
    parser.add_argument('--upload', action='store_true', help='Upload save to Dropbox and exit')
    
    args = parser.parse_args()
    
    sync = MAAReduxSync()
    
    if args.test:
        logger.info("Configuration test passed")
        sys.exit(0)
    elif args.do_import:
        if sync.quick_import():
            logger.info("Manual import successful")
        else:
            logger.error("Manual import failed")
            sys.exit(1)
    elif args.upload:
        if sync.upload_save():
            logger.info("Manual upload successful")
        else:
            logger.error("Manual upload failed")
            sys.exit(1)
    else:
        sync.monitor()

if __name__ == "__main__":
    main()
'''
        
        script_path = install_dir / "maa_sync.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Make executable on Unix systems
        if self.system != "Windows":
            os.chmod(script_path, 0o755)
    
    def create_config_file(self, install_dir):
        """Create configuration file"""

        # Load OAuth tokens from temp config
        oauth_tokens = {}
        temp_config_path = Path("temp_oauth_config.json")
        if temp_config_path.exists():
            try:
                with open(temp_config_path, 'r', encoding='utf-8') as f:
                    oauth_tokens = json.load(f)
                # Clean up temp file
                temp_config_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to load OAuth tokens: {e}")

        config = {
            "app_name": self.app_name.get(),
            "save_file_path": str(self.save_file_path.get()),
            "dropbox_app_key": self.dropbox_app_key.get(),
            "dropbox_app_secret": self.dropbox_app_secret.get(),
            "dropbox_access_token": oauth_tokens.get("dropbox_access_token", ""),
            "dropbox_refresh_token": oauth_tokens.get("dropbox_refresh_token", ""),
            "dropbox_token_expires_in": oauth_tokens.get("dropbox_token_expires_in", 0),
            "dropbox_token_obtained_at": oauth_tokens.get("dropbox_token_obtained_at", 0),
            "dropbox_folder": "/SyncedFiles",
            "sync_filename": Path(self.save_file_path.get()).name
        }

        config_path = install_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    def create_helper_scripts(self, install_dir):
        """Create helper scripts for manual operations"""
        
        if self.system == "Windows":
            # Windows batch files
            start_script = f'''@echo off
cd /d "{install_dir}"
echo Starting MAA Redux Save Sync...
pythonw maa_sync.py
'''
            
            stop_script = '''@echo off
echo Stopping MAA Redux Save Sync...
taskkill /f /im python.exe /fi "WINDOWTITLE eq MAA Redux Save Sync*" >nul 2>&1
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq MAA Redux Save Sync*" >nul 2>&1
echo Sync stopped.
pause
'''
            
            manual_import = f'''@echo off
cd /d "{install_dir}"
echo Importing save from Dropbox...
python maa_sync.py --import
pause
'''
            
            manual_upload = f'''@echo off
cd /d "{install_dir}"
echo Uploading save to Dropbox...
python maa_sync.py --upload
pause
'''
            
            with open(install_dir / "start_sync.bat", 'w') as f:
                f.write(start_script)
            with open(install_dir / "stop_sync.bat", 'w') as f:
                f.write(stop_script)
            with open(install_dir / "manual_import.bat", 'w') as f:
                f.write(manual_import)
            with open(install_dir / "manual_upload.bat", 'w') as f:
                f.write(manual_upload)
                
        else:
            # Unix shell scripts
            start_script = f'''#!/bin/bash
cd "{install_dir}"
echo "Starting MAA Redux Save Sync..."
python3 maa_sync.py &
echo "Sync started in background"
'''
            
            stop_script = f'''#!/bin/bash
echo "Stopping MAA Redux Save Sync..."
pkill -f "maa_sync.py"
echo "Sync stopped"
'''
            
            manual_import = f'''#!/bin/bash
cd "{install_dir}"
echo "Importing save from Dropbox..."
python3 maa_sync.py --import
'''
            
            manual_upload = f'''#!/bin/bash
cd "{install_dir}"
echo "Uploading save to Dropbox..."
python3 maa_sync.py --upload
'''
            
            scripts = [
                ("start_sync.sh", start_script),
                ("stop_sync.sh", stop_script),
                ("manual_import.sh", manual_import),
                ("manual_upload.sh", manual_upload)
            ]
            
            for script_name, content in scripts:
                script_path = install_dir / script_name
                with open(script_path, 'w') as f:
                    f.write(content)
                os.chmod(script_path, 0o755)
    
    def setup_autostart(self, install_dir):
        """Setup auto-start for the system"""
        
        if self.system == "Windows":
            self.setup_windows_autostart(install_dir)
        else:
            self.setup_macos_autostart(install_dir)
    
    def setup_windows_autostart(self, install_dir):
        """Setup Windows auto-start"""
        
        # Create VBS script for silent startup
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{install_dir}"
WshShell.Run "pythonw maa_sync.py", 0, False
'''
        
        vbs_path = install_dir / "start_sync_silent.vbs"
        with open(vbs_path, 'w') as f:
            f.write(vbs_content)
        
        # Add to registry
        try:
            import winreg
            key_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "MAAReduxSync", 0, winreg.REG_SZ, str(vbs_path))
            winreg.CloseKey(key)
            
        except ImportError:
            # Fallback: create startup folder shortcut
            import subprocess
            startup_folder = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            if startup_folder.exists():
                batch_path = install_dir / "start_sync.bat"
                shortcut_path = startup_folder / "MAA Redux Sync.bat"
                try:
                    shutil.copy2(batch_path, shortcut_path)
                except Exception as e:
                    logger.warning(f"Could not create startup shortcut: {e}")
        except Exception as e:
            logger.warning(f"Could not set up auto-start: {e}")
    
    def setup_macos_autostart(self, install_dir):
        """Setup macOS LaunchAgent"""
        
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.maa.redux.sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{install_dir}/maa_sync.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{install_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{install_dir}/sync.log</string>
    <key>StandardErrorPath</key>
    <string>{install_dir}/sync_error.log</string>
</dict>
</plist>'''
        
        try:
            launchagents_dir = Path.home() / "Library" / "LaunchAgents"
            launchagents_dir.mkdir(exist_ok=True)
            
            plist_path = launchagents_dir / "com.maa.redux.sync.plist"
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the agent
            subprocess.run(["launchctl", "load", str(plist_path)], check=False)
            
        except Exception as e:
            logger.warning(f"Could not set up macOS auto-start: {e}")
    
    def test_installation(self, install_dir):
        """Test the installation"""

        # Check if files exist
        required_files = ["maa_sync.py", "config.json", "dropbox_oauth.py"]
        for file_name in required_files:
            file_path = install_dir / file_name
            if not file_path.exists():
                raise FileNotFoundError(f"Required file not created: {file_name}")
        
        # Test script execution
        original_cwd = os.getcwd()
        try:
            os.chdir(install_dir)
            result = subprocess.run(
                [sys.executable, "maa_sync.py", "--test"], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Script test failed: {result.stderr}")
                
        finally:
            os.chdir(original_cwd)
    
    def update_progress(self, value, status):
        """Update progress bar and status"""
        self.root.after(0, lambda: self.progress_var.set(value))
        self.root.after(0, lambda: self.update_status(status))
    
    def update_status(self, status):
        """Update status label"""
        self.status_label.config(text=status)
    
    def show_success_dialog(self, install_dir):
        """Show installation success dialog"""
        
        self.progress_bar.pack_forget()
        self.install_button.config(state=NORMAL)
        
        helper_scripts = []
        if self.system == "Windows":
            helper_scripts = [
                "start_sync.bat - Start sync manually",
                "stop_sync.bat - Stop sync service",
                "manual_import.bat - Import save from Dropbox",
                "manual_upload.bat - Upload save to Dropbox"
            ]
        else:
            helper_scripts = [
                "start_sync.sh - Start sync manually",
                "stop_sync.sh - Stop sync service", 
                "manual_import.sh - Import save from Dropbox",
                "manual_upload.sh - Upload save to Dropbox"
            ]
        
        success_msg = f"""Installation completed successfully!

Installation location: {install_dir}

Your MAA Redux save sync is now active. The system will:
• Automatically sync saves when you start/close the game
• Create local backups for safety
• Work across all your devices with the same Dropbox token

Helper scripts created:
{chr(10).join('• ' + script for script in helper_scripts)}

Log files:
• sync.log - Main sync activity log
• sync_error.log - Error logs (macOS only)

The sync service {"is running and " if self.auto_start.get() else ""}will start automatically on system boot."""

        result = messagebox.showinfo("Installation Complete", success_msg)
        
        # Ask if user wants to start monitoring now
        if messagebox.askyesno("Start Now?", 
                              "Would you like to start the sync service now?\n"
                              "(It will start automatically on next system boot)"):
            self.start_sync_service(install_dir)
    
    def show_error_dialog(self, error_msg):
        """Show installation error dialog"""
        
        self.progress_bar.pack_forget()
        self.install_button.config(state=NORMAL)
        
        messagebox.showerror("Installation Failed", 
                           f"Installation failed with error:\n\n{error_msg}\n\n"
                           f"Please check that:\n"
                           f"• Python is properly installed\n"
                           f"• You have write permissions to the install directory\n"
                           f"• Your internet connection is working\n"
                           f"• Your Dropbox token is valid")
    
    def start_sync_service(self, install_dir):
        """Start the sync service"""
        
        original_cwd = os.getcwd()
        try:
            os.chdir(install_dir)
            
            if self.system == "Windows":
                # Use VBS script for silent startup
                vbs_path = install_dir / "start_sync_silent.vbs"
                if vbs_path.exists():
                    subprocess.Popen(["wscript", str(vbs_path)])
                else:
                    subprocess.Popen([sys.executable, "maa_sync.py"], 
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen([sys.executable, "maa_sync.py"])
            
            messagebox.showinfo("Service Started", 
                               "MAA Redux sync service is now running in the background!\n\n"
                               "Check sync.log for activity logs.")
        except Exception as e:
            messagebox.showerror("Start Failed", f"Failed to start sync service:\n{str(e)}")
        finally:
            os.chdir(original_cwd)
    
    def show_help(self):
        """Show help information"""
        
        help_text = """MAA Redux Save Sync Help

This tool automatically synchronizes your MAA Redux save files between devices using Dropbox.

Setup Requirements:
• Dropbox account (free tier is sufficient)
• Python 3.8+ installed
• MAA Redux game installed

How it works:
• When you start MAA Redux, it downloads the latest save from Dropbox
• When you close MAA Redux, it uploads your save to Dropbox
• This happens automatically on all your configured devices
• Local backups are created before each sync operation

File Locations:
• Sync logs: Check sync.log in the installation directory
• Backups: Created in backups/ subdirectory
• Configuration: config.json in installation directory

Manual Controls:
Use the helper scripts in the installation directory:
• Start/stop the sync service manually
• Force import/upload operations
• View logs and troubleshoot issues

Troubleshooting:
• Make sure MAA Redux is completely closed before starting on another device
• Check sync.log file for any error messages
• Verify your Dropbox token is correctly entered and hasn't expired
• Ensure the save file path is correct and accessible
• Try manual import/upload to test connectivity

Best Practices:
• Let the game fully close before switching devices
• Keep backups of important save files
• Don't modify save files while the game is running
• Check logs periodically for any issues

For more help, visit the project documentation or community forums."""
        
        help_window = Toplevel(self.root)
        help_window.title("MAA Redux Save Sync - Help")
        help_window.geometry("700x600")
        help_window.transient(self.root)
        
        # Create scrollable text widget
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        text_widget = Text(text_frame, wrap=WORD, yscrollcommand=scrollbar.set,
                          font=("Arial", 10), state=NORMAL)
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.insert(END, help_text)
        text_widget.config(state=DISABLED)
        
        # Close button
        ttk.Button(help_window, text="Close", 
                  command=help_window.destroy).pack(pady=10)
    
    def run(self):
        """Start the GUI application"""
        # Center window on screen
        self.root.update_idletasks()
        width = 850
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start the main loop
        self.root.mainloop()
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit the installer?"):
            self.root.quit()
            self.root.destroy()

def main():
    """Main entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            messagebox.showerror("Python Version Error", 
                               "Python 3.8 or higher is required.\n"
                               f"Current version: {sys.version}")
            sys.exit(1)
        
        # Create and run installer
        installer = MAAReduxSyncInstaller()
        installer.run()
        
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Failed to start installer:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()