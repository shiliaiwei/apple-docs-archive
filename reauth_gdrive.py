#!/usr/bin/env python3
import os
import sys
import json
from google_auth_oauthlib.flow import InstalledAppFlow

TOKEN_PATH = "/Users/Apple16/.credentials/gdrive_user_token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def reauth():
    if not os.path.exists(TOKEN_PATH):
        print(f"Token file not found: {TOKEN_PATH}")
        sys.exit(1)

    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    cfg = {
        "installed": {
            "client_id": data["client_id"],
            "client_secret": data["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": data.get("token_uri", "https://oauth2.googleapis.com/token"),
            "redirect_uris": ["http://localhost:8088/"]
        }
    }

    flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    print("\n=======================================================")
    print(" GOOGLE DRIVE USER RE-AUTHENTICATION")
    print(f" Auth URL: {auth_url}")
    print(" Opening browser for authorization on port 8088...")
    print("=======================================================\n")

    creds = flow.run_local_server(port=8088, prompt="consent", access_type="offline")

    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nAuthentication successful!")
    print(f"Updated token written to: {TOKEN_PATH}")

if __name__ == "__main__":
    reauth()
