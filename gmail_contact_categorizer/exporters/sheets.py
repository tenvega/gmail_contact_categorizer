"""
Google Sheets exporter for Gmail Contact Categorizer.
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime

from .base import BaseExporter


class GoogleSheetsExporter(BaseExporter):
    """Exports categorized contacts to Google Sheets."""
    
    def __init__(self, credentials):
        """
        Initialize the Google Sheets exporter.
        
        Args:
            credentials (Credentials): Google API credentials.
        """
        self.credentials = credentials
        self.contacts = {}
        self.service = build('sheets', 'v4', credentials=credentials)
    
    def export(self, categories, output):
        """
        Export categorized contacts to Google Sheets.
        
        Args:
            categories (dict): Dictionary of categorized contacts.
            output (str): Google Sheets spreadsheet title.
            
        Returns:
            str: URL of the created Google Sheet.
        """
        # Store contacts for data preparation
        self.contacts = categories
        
        # Prepare data for export
        export_data = self._prepare_export_data(categories)
        
        try:
            # Create new spreadsheet
            spreadsheet_id = self._get_or_create_spreadsheet(output)
            
            # Prepare the data
            headers = list(export_data[0].keys())
            values = [headers]
            values.extend([list(row.values()) for row in export_data])
            
            # Clear existing content and update with new data
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range='Contacts!A1'
            ).execute()
            
            # Update the sheet with new data
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Contacts!A1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Apply formatting
            self._apply_sheets_formatting(spreadsheet_id)
            
            # Return the URL
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            
        except HttpError as error:
            print(f"An error occurred while exporting to Google Sheets: {error}")
            return None
    
    def _get_or_create_spreadsheet(self, title):
        """
        Get existing spreadsheet or create a new one.
        
        Args:
            title (str): Spreadsheet title.
            
        Returns:
            str: Spreadsheet ID.
        """
        try:
            # Create a unique title with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_title = f"{title}_{timestamp}"
            
            # Create new spreadsheet with Contacts sheet
            spreadsheet = {
                'properties': {
                    'title': unique_title
                },
                'sheets': [{
                    'properties': {
                        'title': 'Contacts'
                    }
                }]
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            return spreadsheet.get('spreadsheetId')
                
        except Exception as e:
            print(f"Error creating Google Sheet: {e}")
            raise
    
    def _apply_sheets_formatting(self, spreadsheet_id):
        """
        Apply formatting to the Google Sheet.
        
        Args:
            spreadsheet_id (str): ID of the spreadsheet.
        """
        try:
            # Get the sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']
            
            # Define formatting requests
            requests = [
                # Header formatting
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 0.21,
                                    'green': 0.38,
                                    'blue': 0.57
                                },
                                'textFormat': {
                                    'foregroundColor': {
                                        'red': 1,
                                        'green': 1,
                                        'blue': 1
                                    },
                                    'bold': True
                                },
                                'horizontalAlignment': 'LEFT',
                                'verticalAlignment': 'MIDDLE',
                                'wrapStrategy': 'WRAP',
                                'borders': {
                                    'top': {'style': 'SOLID'},
                                    'bottom': {'style': 'SOLID'},
                                    'left': {'style': 'SOLID'},
                                    'right': {'style': 'SOLID'}
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,wrapStrategy,borders)'
                    }
                },
                # Data cell formatting
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'horizontalAlignment': 'LEFT',
                                'verticalAlignment': 'MIDDLE',
                                'wrapStrategy': 'WRAP',
                                'borders': {
                                    'top': {'style': 'SOLID'},
                                    'bottom': {'style': 'SOLID'},
                                    'left': {'style': 'SOLID'},
                                    'right': {'style': 'SOLID'}
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(horizontalAlignment,verticalAlignment,wrapStrategy,borders)'
                    }
                },
                # Auto-resize columns
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 20  # Adjust based on number of columns
                        }
                    }
                },
                # Freeze header row
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'gridProperties': {
                                'frozenRowCount': 1
                            }
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]
            
            # Apply formatting
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()
            
        except HttpError as error:
            print(f"An error occurred while applying formatting: {error}")
