import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
client_file = os.path.join(ROOT, "client_secret.json")
if not os.path.exists(client_file):
    raise SystemExit("Save your Google OAuth Desktop client JSON as client_secret.json in the project root first.")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file(client_file, SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\nCopy these values into GitHub repository Actions secrets. Do not share them:")
print("YT_CLIENT_ID=" + str(creds.client_id))
print("YT_CLIENT_SECRET=" + str(creds.client_secret))
print("YT_REFRESH_TOKEN=" + str(creds.refresh_token))
if not creds.refresh_token:
    print("WARNING: No refresh token was returned. Revoke this app's access in your Google account and run again with consent.")
