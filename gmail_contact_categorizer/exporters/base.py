"""
Base exporter class for Gmail Contact Categorizer.
"""

from abc import ABC, abstractmethod


class BaseExporter(ABC):
    """Base class for all exporters."""
    
    @abstractmethod
    def export(self, categories, output):
        """
        Export categorized contacts.
        
        Args:
            categories (dict): Dictionary of categorized contacts.
            output (str): Output filename or destination.
            
        Returns:
            str: Status message or path/ID of the exported data.
        """
        pass
    
    def _prepare_export_data(self, categories):
        """
        Prepare data for export in a standard format.
        
        Args:
            categories (dict): Dictionary of categorized contacts.
            
        Returns:
            list: List of dictionaries with standardized contact data.
        """
        export_data = []
        
        for category_name, contacts in categories.items():
            formatted_category = category_name.replace('_', ' ').title()
            
            for contact in contacts:
                # Standardize the contact data format
                export_data.append({
                    'Email': contact['email'],
                    'Category': formatted_category,
                    'Total Emails': contact['total_emails'],
                    'Sent': contact['sent'],
                    'Received': contact['received'],
                    'Last Contact': contact['last_contact'].strftime('%Y-%m-%d') if contact['last_contact'] else 'Unknown',
                    'Common Topics': ', '.join(contact['common_topics']) if contact['common_topics'] else 'N/A'
                })
        
        return export_data
