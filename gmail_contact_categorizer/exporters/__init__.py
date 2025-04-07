"""
Exporters package for Gmail Contact Categorizer.
Provides functionality to export contact categories to different formats.
"""

from gmail_contact_categorizer.exporters.excel import ExcelExporter
from gmail_contact_categorizer.exporters.sheets import GoogleSheetsExporter


def get_exporter(export_type, credentials=None):
    """
    Factory function to get the appropriate exporter.
    
    Args:
        export_type (str): Type of export ('excel' or 'sheets').
        credentials (google.oauth2.credentials.Credentials, optional): 
            Google OAuth2 credentials. Required for 'sheets' export.
            
    Returns:
        BaseExporter: An exporter instance.
        
    Raises:
        ValueError: If the export type is not supported.
    """
    if export_type.lower() == 'excel':
        return ExcelExporter()
    elif export_type.lower() == 'sheets':
        if credentials is None:
            raise ValueError("Google credentials are required for Google Sheets export.")
        return GoogleSheetsExporter(credentials)
    else:
        raise ValueError(f"Unsupported export type: {export_type}")


__all__ = ['get_exporter', 'ExcelExporter', 'GoogleSheetsExporter']
