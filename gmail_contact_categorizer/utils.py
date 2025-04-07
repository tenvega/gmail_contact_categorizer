"""
Utility functions for Gmail Contact Categorizer.
"""

import re


def extract_email_address(header):
    """
    Extract email address from a header string.
    
    Args:
        header (str): Email header string (e.g., "John Doe <john@example.com>").
        
    Returns:
        str or None: Extracted email address or None if not found.
    """
    if not header:
        return None
        
    # Try to match an email address pattern
    match = re.search(r'[\w\.-]+@[\w\.-]+', header)
    return match.group(0).lower() if match else None


def format_datetime(dt):
    """
    Format a datetime object to a readable string.
    
    Args:
        dt (datetime): Datetime object.
        
    Returns:
        str: Formatted datetime string.
    """
    if not dt:
        return "Unknown"
        
    return dt.strftime('%Y-%m-%d %H:%M')


def truncate_text(text, max_length=50):
    """
    Truncate text to a maximum length with ellipsis.
    
    Args:
        text (str): Text to truncate.
        max_length (int, optional): Maximum length. Defaults to 50.
        
    Returns:
        str: Truncated text.
    """
    if not text:
        return ""
        
    if len(text) <= max_length:
        return text
        
    return text[:max_length - 3] + "..."
