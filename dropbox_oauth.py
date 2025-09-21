#!/usr/bin/env python3
"""
Dropbox OAuth 2.0 Helper Module with Refresh Token Support
"""

import json
import time
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Dict, Optional, Tuple
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logger = logging.getLogger(__name__)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server handler for OAuth callback"""

    def do_GET(self):
        """Handle OAuth callback"""
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        if 'code' in query_params:
            self.server.auth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
                <html><body>
                <h2>Authorization Successful!</h2>
                <p>You can now close this window and return to the MAA Redux Sync Installer.</p>
                <script>window.close();</script>
                </body></html>
            ''')
        elif 'error' in query_params:
            self.server.auth_error = query_params['error'][0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
                <html><body>
                <h2>Authorization Failed</h2>
                <p>Error: {query_params['error'][0]}</p>
                <p>Please close this window and try again.</p>
                </body></html>
            '''.encode())
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h2>Invalid Request</h2></body></html>')

    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

class DropboxOAuth:
    """Dropbox OAuth 2.0 handler with refresh token support"""

    def __init__(self, app_key: str, app_secret: str, redirect_uri: str = "http://localhost:8080/oauth/callback"):
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.server_port = 8080

        # OAuth endpoints
        self.auth_url = "https://www.dropbox.com/oauth2/authorize"
        self.token_url = "https://api.dropboxapi.com/oauth2/token"

    def start_auth_flow(self) -> str:
        """Start OAuth flow and return authorization URL"""
        # Validate inputs
        if not self.app_key or not self.app_key.strip():
            raise ValueError("App key is required")

        if not self.redirect_uri:
            raise ValueError("Redirect URI is required")

        params = {
            'client_id': self.app_key.strip(),
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'token_access_type': 'offline',  # This enables refresh tokens
        }

        # URL encode parameters properly
        auth_url = f"{self.auth_url}?{urllib.parse.urlencode(params)}"

        # Log the URL for debugging (without sensitive info)
        logger.info(f"Generated OAuth URL with client_id length: {len(params['client_id'])}")
        logger.info(f"Redirect URI: {params['redirect_uri']}")

        return auth_url

    def get_auth_code_via_browser(self) -> Optional[str]:
        """Launch browser and wait for OAuth callback"""
        auth_url = self.start_auth_flow()

        # Try to start server on localhost first, then 127.0.0.1
        server = None
        server_addresses = [('localhost', self.server_port), ('127.0.0.1', self.server_port)]

        for address, port in server_addresses:
            try:
                server = HTTPServer((address, port), OAuthCallbackHandler)
                server.auth_code = None
                server.auth_error = None
                logger.info(f"OAuth server started on {address}:{port}")
                break
            except OSError as e:
                logger.warning(f"Failed to start server on {address}:{port}: {e}")
                continue

        if not server:
            raise Exception(f"Could not start OAuth server on port {self.server_port}")

        # Start server in background
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        try:
            # Open browser
            logger.info(f"Opening browser for authorization: {auth_url}")
            webbrowser.open(auth_url)

            # Wait for callback (max 5 minutes)
            timeout = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < timeout:
                if server.auth_code:
                    logger.info("OAuth authorization code received")
                    return server.auth_code
                elif server.auth_error:
                    raise Exception(f"OAuth error from Dropbox: {server.auth_error}")
                time.sleep(0.5)

            raise Exception("OAuth timeout - no response received within 5 minutes")

        finally:
            server.shutdown()
            server.server_close()

    def exchange_code_for_tokens(self, auth_code: str) -> Dict[str, str]:
        """Exchange authorization code for access and refresh tokens"""
        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': self.app_key,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri
        }

        # Make request
        request_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(
            self.token_url,
            data=request_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        try:
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode())

            if 'access_token' not in response_data:
                raise Exception(f"Token exchange failed: {response_data}")

            return {
                'access_token': response_data['access_token'],
                'refresh_token': response_data['refresh_token'],
                'expires_in': response_data.get('expires_in'),
                'token_type': response_data.get('token_type', 'bearer')
            }

        except urllib.error.HTTPError as e:
            error_response = e.read().decode()
            raise Exception(f"Token exchange failed: {error_response}")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """Use refresh token to get a new access token"""
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.app_key,
            'client_secret': self.app_secret
        }

        request_data = urllib.parse.urlencode(data).encode()
        request = urllib.request.Request(
            self.token_url,
            data=request_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        try:
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode())

            if 'access_token' not in response_data:
                raise Exception(f"Token refresh failed: {response_data}")

            return {
                'access_token': response_data['access_token'],
                'expires_in': response_data.get('expires_in'),
                'token_type': response_data.get('token_type', 'bearer')
            }

        except urllib.error.HTTPError as e:
            error_response = e.read().decode()
            raise Exception(f"Token refresh failed: {error_response}")

class DropboxTokenManager:
    """Manages Dropbox tokens with automatic refresh"""

    def __init__(self, config_path: str, app_key: str, app_secret: str):
        self.config_path = Path(config_path)
        self.app_key = app_key
        self.app_secret = app_secret
        self.oauth = DropboxOAuth(app_key, app_secret)

        self._tokens = self._load_tokens()
        self._token_expires_at = 0

    def _load_tokens(self) -> Dict[str, str]:
        """Load tokens from config file"""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return {
                'access_token': config.get('dropbox_access_token', ''),
                'refresh_token': config.get('dropbox_refresh_token', ''),
                'expires_in': config.get('dropbox_token_expires_in', 0)
            }
        except Exception as e:
            logger.warning(f"Failed to load tokens: {e}")
            return {}

    def _save_tokens(self, tokens: Dict[str, str]):
        """Save tokens to config file"""
        try:
            # Load existing config
            config = {}
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # Update with new tokens
            config.update({
                'dropbox_access_token': tokens.get('access_token', ''),
                'dropbox_refresh_token': tokens.get('refresh_token', ''),
                'dropbox_token_expires_in': tokens.get('expires_in', 0),
                'dropbox_token_obtained_at': int(time.time())
            })

            # Save config
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)

            self._tokens = tokens

        except Exception as e:
            logger.error(f"Failed to save tokens: {e}")
            raise

    def authorize_new_user(self) -> bool:
        """Complete OAuth flow for new user"""
        try:
            # Get authorization code
            auth_code = self.oauth.get_auth_code_via_browser()
            if not auth_code:
                return False

            # Exchange for tokens
            tokens = self.oauth.exchange_code_for_tokens(auth_code)

            # Save tokens
            self._save_tokens(tokens)

            # Set expiration time
            if tokens.get('expires_in'):
                self._token_expires_at = time.time() + int(tokens['expires_in'])

            logger.info("Authorization successful - tokens saved")
            return True

        except Exception as e:
            logger.error(f"Authorization failed: {e}")
            return False

    def get_valid_access_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        # Check if we have tokens
        if not self._tokens.get('access_token'):
            logger.warning("No access token available")
            return None

        # Check if token is expired (with 5 minute buffer)
        current_time = time.time()
        if self._token_expires_at and current_time >= (self._token_expires_at - 300):
            logger.info("Access token expired, refreshing...")

            if not self._refresh_token():
                logger.error("Failed to refresh token")
                return None

        return self._tokens.get('access_token')

    def _refresh_token(self) -> bool:
        """Refresh the access token using refresh token"""
        refresh_token = self._tokens.get('refresh_token')
        if not refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            # Get new access token
            new_tokens = self.oauth.refresh_access_token(refresh_token)

            # Update stored tokens (keep existing refresh token)
            updated_tokens = self._tokens.copy()
            updated_tokens.update(new_tokens)

            # Save updated tokens
            self._save_tokens(updated_tokens)

            # Update expiration time
            if new_tokens.get('expires_in'):
                self._token_expires_at = time.time() + int(new_tokens['expires_in'])

            logger.info("Token refreshed successfully")
            return True

        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False

    def is_authorized(self) -> bool:
        """Check if user is properly authorized"""
        return bool(self._tokens.get('access_token') and self._tokens.get('refresh_token'))

    def revoke_authorization(self):
        """Remove stored tokens"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Remove token fields
                config.pop('dropbox_access_token', None)
                config.pop('dropbox_refresh_token', None)
                config.pop('dropbox_token_expires_in', None)
                config.pop('dropbox_token_obtained_at', None)

                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)

            self._tokens = {}
            self._token_expires_at = 0
            logger.info("Authorization revoked")

        except Exception as e:
            logger.error(f"Failed to revoke authorization: {e}")