"""
Authentication module for Gmail Contact Categorizer.
Handles OAuth2 authentication with Google APIs.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


def authenticate():
    """
    Authenticate with Google APIs using OAuth2.
    
    We need access to:
    - Gmail (readonly)
    - Google Sheets (if exporting to sheets)
    - Google Drive (if exporting to sheets)
    
    Returns:
        google.oauth2.credentials.Credentials: OAuth2 credentials
    """
    # Define the required API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    credentials = None
    
    # Try to load credentials from the token file
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # If credentials are missing or invalid, refresh them or create new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
            
        # Save the credentials for future runs
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    return credentials
