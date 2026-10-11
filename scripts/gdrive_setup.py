"""One-time Google Drive setup for Card Heroes. Run this on YOUR computer, not on Render.

What it does:
  1. Opens your browser so you can sign in with the Google account that will hold the images.
  2. Gets a long-lived "refresh token" the website will use to upload images.
  3. Creates a folder called "Card Heroes Media" in that account's Drive.
  4. Prints the four GDRIVE_* values to paste into Render's Environment tab.

Before running it, follow DEPLOY.md section "Google Drive" to download
client_secret.json from Google Cloud Console and put it next to manage.py.

Usage (inside the project's virtual environment):
    python scripts/gdrive_setup.py
    python scripts/gdrive_setup.py path\\to\\client_secret.json
"""
import json
import sys
from pathlib import Path

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_NAME = 'Card Heroes Media'


def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit('Missing packages. Run:  pip install -r requirements.txt')

    secret_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'client_secret.json')
    if not secret_path.exists():
        sys.exit(f'Could not find {secret_path}. Download it from Google Cloud Console (see DEPLOY.md).')

    client_info = json.loads(secret_path.read_text(encoding='utf-8'))
    client = client_info.get('installed') or client_info.get('web') or {}

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
    # access_type=offline + prompt=consent guarantees Google returns a refresh token
    creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
    if not creds.refresh_token:
        sys.exit('Google did not return a refresh token. Remove the app at '
                 'https://myaccount.google.com/permissions and run this again.')

    drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
    folder = drive.files().create(
        body={'name': FOLDER_NAME, 'mimeType': 'application/vnd.google-apps.folder'},
        fields='id',
    ).execute()

    print('\n' + '=' * 70)
    print(f'Success! Folder "{FOLDER_NAME}" created in your Google Drive.')
    print('Paste these into Render -> your service -> Environment:')
    print('=' * 70)
    print(f'GDRIVE_CLIENT_ID={client.get("client_id", creds.client_id)}')
    print(f'GDRIVE_CLIENT_SECRET={client.get("client_secret", creds.client_secret)}')
    print(f'GDRIVE_REFRESH_TOKEN={creds.refresh_token}')
    print(f'GDRIVE_FOLDER_ID={folder["id"]}')
    print('=' * 70)
    print('Treat these like passwords: never commit them to GitHub.\n')


if __name__ == '__main__':
    main()
