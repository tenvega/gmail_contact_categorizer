"""
Gmail Client module for fetching and processing emails from Gmail.
"""

import re
import base64
from datetime import datetime
from googleapiclient.discovery import build
from tqdm import tqdm
from gmail_contact_categorizer.utils import extract_email_address


class GmailClient:
    """Client for fetching and processing emails from Gmail."""
    
    def __init__(self, credentials):
        """
        Initialize the Gmail client.
        
        Args:
            credentials (google.oauth2.credentials.Credentials): OAuth2 credentials
        """
        self.service = build('gmail', 'v1', credentials=credentials)
        self.user_id = 'me'  # 'me' refers to the authenticated user
        self.user_email = None  # Will be populated when fetching emails
    
    def fetch_emails(self, max_emails=None):
        """
        Fetch emails from Gmail.
        
        Args:
            max_emails (int, optional): Maximum number of emails to fetch.
                If None, all emails will be fetched.
                
        Returns:
            list: List of processed email dictionaries.
        """
        # Initialize list to store processed emails
        processed_emails = []
        
        # Get list of message IDs
        messages = self._get_message_ids(max_emails)
        
        if not messages:
            print("No messages found.")
            return processed_emails
        
        print(f"Processing {len(messages)} emails...")
        
        # Process each email
        for message in tqdm(messages):
            msg = self._get_message(message['id'])
            if msg:
                processed_emails.append(msg)
        
        return processed_emails
    
    def _get_message_ids(self, max_emails=None):
        """
        Get message IDs from Gmail.
        
        Args:
            max_emails (int, optional): Maximum number of message IDs to fetch.
            
        Returns:
            list: List of message ID dictionaries.
        """
        messages = []
        next_page_token = None
        
        # Keep fetching pages of messages until we have all of them
        while True:
            # Request parameters
            params = {'userId': self.user_id}
            if next_page_token:
                params['pageToken'] = next_page_token
            if max_emails:
                params['maxResults'] = min(max_emails - len(messages), 500)  # Gmail API allows max 500 per request
            else:
                params['maxResults'] = 500  # Maximum allowed by Gmail API
                
            # Make the API request
            results = self.service.users().messages().list(**params).execute()
            batch = results.get('messages', [])
            messages.extend(batch)
            
            # Check if we need to stop
            next_page_token = results.get('nextPageToken')
            if not next_page_token or (max_emails and len(messages) >= max_emails):
                break
        
        return messages
    
    def _get_message(self, msg_id):
        """
        Get a single message from Gmail.
        
        Args:
            msg_id (str): Message ID.
            
        Returns:
            dict: Processed email dictionary or None if processing failed.
        """
        try:
            # Fetch the message
            msg = self.service.users().messages().get(
                userId=self.user_id, id=msg_id, format='full'
            ).execute()
            
            # Extract headers
            headers = msg['payload']['headers']
            
            # Extract email details
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date_header = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
            
            # Identify the user's email if not already known
            if not self.user_email:
                # Look for email addresses in the 'From' header of received messages
                # and in the 'To' header of sent messages
                sent_items = next((h['value'] for h in headers if h['name'].lower() == 'x-gm-labels' 
                                  and 'SENT' in h['value']), None)
                if sent_items:
                    # This is a sent message, user's email is in the 'From' header
                    self.user_email = extract_email_address(from_header)
            
            # Determine if this is a sent email
            is_sent = False
            if self.user_email:
                is_sent = self.user_email == extract_email_address(from_header)
            else:
                # If we can't identify the user's email, use labels as a fallback
                labels = msg.get('labelIds', [])
                is_sent = 'SENT' in labels
            
            # Extract contact email (who we're communicating with)
            contact_header = to_header if is_sent else from_header
            contact_email = extract_email_address(contact_header)
            
            # Skip if no valid contact email found or if it's the user's own email
            if not contact_email:
                return None
            if self.user_email and contact_email == self.user_email:
                return None
            
            # Get email body
            body = self._get_email_body(msg)
            
            # Parse date
            try:
                # Try a common format first
                dt = datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                try:
                    # Try without timezone
                    dt = datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S")
                    # Make it timezone-aware by assuming UTC
                    dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
                except ValueError:
                    # If all else fails, use current date
                    dt = datetime.now().astimezone()
            
            # Return processed email
            return {
                'id': msg_id,
                'subject': subject,
                'body': body,
                'from': from_header,
                'to': to_header,
                'date': dt,
                'contact_email': contact_email,
                'is_sent': is_sent
            }
            
        except Exception as e:
            print(f"Error processing message {msg_id}: {e}")
            return None
    
    def _get_email_body(self, msg):
        """
        Extract body text from email message.
        
        Args:
            msg (dict): Message dictionary from Gmail API.
            
        Returns:
            str: Email body text.
        """
        body = ""
        
        if 'payload' not in msg:
            return body
            
        payload = msg['payload']
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = self._decode_body(part['body']['data'])
                        break
        
        # Handle single part messages
        elif 'body' in payload and 'data' in payload['body']:
            body = self._decode_body(payload['body']['data'])
        
        return body
    
    def _decode_body(self, data):
        """
        Decode base64 encoded email body.
        
        Args:
            data (str): Base64 encoded string.
            
        Returns:
            str: Decoded string.
        """
        if not data:
            return ""
            
        try:
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        except Exception:
            return ""
