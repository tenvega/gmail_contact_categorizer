"""
Google Sheets exporter for Gmail Contact Categorizer.
"""

import pandas as pd
from googleapiclient.discovery import build
from gmail_contact_categorizer.exporters.base import BaseExporter


class GoogleSheetsExporter(BaseExporter):
    """Exports categorized contacts to Google Sheets."""
    
    def __init__(self, credentials):
        """
        Initialize the Google Sheets exporter.
        
        Args:
            credentials (google.oauth2.credentials.Credentials): Google OAuth2 credentials.
        """
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
        self.drive_service = build('drive', 'v3', credentials=credentials)
    
    def export(self, categories, output='Gmail Contact Categories'):
        """
        Export categorized contacts to a Google Sheet.
        
        Args:
            categories (dict): Dictionary of categorized contacts.
            output (str, optional): Title of the Google Sheet. 
                Defaults to 'Gmail Contact Categories'.
            
        Returns:
            str: ID of the created Google Sheet.
        """
        # Prepare data for export
        export_data = self._prepare_export_data(categories)
        
        # Create DataFrame
        df = pd.DataFrame(export_data)
        
        # Create a new Google Sheet
        spreadsheet_id = self._create_google_sheet(output, df)
        
        return spreadsheet_id
    
    def _create_google_sheet(self, title, dataframe):
        """
        Create a new Google Sheet and populate it with data.
        
        Args:
            title (str): Title of the Google Sheet.
            dataframe (pandas.DataFrame): Data to populate the sheet with.
            
        Returns:
            str: ID of the created Google Sheet.
        """
        # Create a new spreadsheet
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        spreadsheet = self.sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Prepare the data for the API request
        headers = dataframe.columns.tolist()
        values = [headers]  # First row is headers
        
        # Add data rows
        for _, row in dataframe.iterrows():
            values.append(row.tolist())
        
        # Define the range to update
        range_name = 'Sheet1!A1'
        
        # Prepare the update request
        body = {
            'values': values
        }
        
        # Update the sheet
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, 
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Apply formatting
        self._format_sheet(spreadsheet_id, dataframe)
        
        return spreadsheet_id
    
    def _format_sheet(self, spreadsheet_id, dataframe):
        """
        Apply formatting to the Google Sheet.
        
        Args:
            spreadsheet_id (str): ID of the Google Sheet.
            dataframe (pandas.DataFrame): Data in the sheet.
        """
        # Get the sheet ID
        sheet_metadata = self.sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_id = sheet_metadata['sheets'][0]['properties']['sheetId']
        
        # Format the header row
        format_requests = [{
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {
                            "red": 0.2,
                            "green": 0.2,
                            "blue": 0.8
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 1.0,
                                "green": 1.0,
                                "blue": 1.0
                            },
                            "bold": True
                        }
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat)"
            }
        },
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": 0,
                    "endIndex": len(dataframe.columns)
                }
            }
        }]
        
        # Find the column index for 'Category'
        category_idx = None
        for i, col in enumerate(dataframe.columns):
            if col == 'Category':
                category_idx = i
                break
        
        # Add conditional formatting for categories
        if category_idx is not None:
            # Family & Friends - Light green
            format_requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sheet_id}],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": "Family & Friends"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.8, "green": 0.9, "blue": 0.8}
                            }
                        }
                    },
                    "index": 0
                }
            })
            
            # Business Contacts - Light blue
            format_requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sheet_id}],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": "Business Contacts"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 0.8, "green": 0.85, "blue": 0.95}
                            }
                        }
                    },
                    "index": 1
                }
            })
            
            # Clients - Light yellow
            format_requests.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [{"sheetId": sheet_id}],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_EQ",
                                "values": [{"userEnteredValue": "Clients"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.8}
                            }
                        }
                    },
                    "index": 2
                }
            })
        
        # Apply the formatting
        body = {"requests": format_requests}
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
