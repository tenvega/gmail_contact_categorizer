"""
Base exporter class for Gmail Contact Categorizer.
"""

from abc import ABC, abstractmethod
from datetime import datetime


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
        
        # Category display names
        category_display = {
            'family': 'Family',
            'friends': 'Friends',
            'colleagues': 'Colleagues',
            'clients': 'Clients',
            'vendors': 'Vendors',
            'newsletters': 'Newsletters',
            'promotions': 'Promotions',
            'notifications': 'Notifications'
        }
        
        for category_name, contacts in categories.items():
            formatted_category = category_display.get(category_name, category_name.replace('_', ' ').title())
            
            for contact in contacts:
                # Get contact data
                contact_data = self.contacts.get(contact, {})
                
                # Calculate communication patterns
                weekday_ratio = sum(1 for dt in contact_data.get('times', []) if dt.weekday() < 5) / len(contact_data.get('times', [])) if contact_data.get('times') else 0
                evening_ratio = sum(1 for dt in contact_data.get('times', []) if dt.hour >= 18 or dt.hour < 7) / len(contact_data.get('times', [])) if contact_data.get('times') else 0
                
                # Get automated features
                automated_features = contact_data.get('automated_features', {})
                is_automated = any(automated_features.values())
                
                # Get domain information
                domain = contact_data.get('domains', {}).most_common(1)[0][0] if contact_data.get('domains') else 'Unknown'
                
                # Get reply patterns
                reply_times = []
                for i in range(1, len(contact_data.get('reply_patterns', []))):
                    if contact_data['reply_patterns'][i]['is_sent'] != contact_data['reply_patterns'][i-1]['is_sent']:
                        reply_time = (contact_data['reply_patterns'][i]['date'] - 
                                    contact_data['reply_patterns'][i-1]['date']).total_seconds()
                        reply_times.append(reply_time)
                avg_reply_time = sum(reply_times) / len(reply_times) if reply_times else 0
                
                # Standardize the contact data format
                export_data.append({
                    'Email': contact,
                    'Category': formatted_category,
                    'Domain': domain,
                    'Total Emails': contact_data.get('emails', 0),
                    'Sent': contact_data.get('sent_count', 0),
                    'Received': contact_data.get('received_count', 0),
                    'Last Contact': max(contact_data.get('times', [])).strftime('%Y-%m-%d %H:%M') if contact_data.get('times') else 'Unknown',
                    'Common Topics': ', '.join(word for word, _ in contact_data.get('subject_words', {}).most_common(5)) if contact_data.get('subject_words') else 'N/A',
                    'Weekday Ratio': f"{weekday_ratio:.2%}",
                    'Evening Ratio': f"{evening_ratio:.2%}",
                    'Avg Reply Time (hours)': f"{avg_reply_time/3600:.1f}",
                    'Is Automated': 'Yes' if is_automated else 'No',
                    'Automated Features': ', '.join(k for k, v in automated_features.items() if v) if is_automated else 'None',
                    'HTML Ratio': f"{contact_data.get('html_ratio', 0)/contact_data.get('emails', 1):.2%}",
                    'Link Count': contact_data.get('link_count', 0),
                    'Formal Words': sum(contact_data.get('body_words', {}).get(w, 0) for w in ['sincerely', 'regarding', 'request', 'meeting']),
                    'Informal Words': sum(contact_data.get('body_words', {}).get(w, 0) for w in ['thanks', 'love', 'hey', 'cheers', 'haha', 'lol']),
                    'Business Words': sum(contact_data.get('body_words', {}).get(w, 0) for w in ['project', 'client', 'meeting', 'report', 'business']),
                    'Family Words': sum(contact_data.get('body_words', {}).get(w, 0) for w in ['mom', 'dad', 'sister', 'brother', 'family'])
                })
        
        return export_data
