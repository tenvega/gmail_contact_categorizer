"""
Gmail Contact Categorizer
A tool for automatically categorizing Gmail contacts into family/friends,
business contacts, and clients based on email communication patterns.
"""

__version__ = '1.0.0'

from gmail_contact_categorizer.auth import authenticate
from gmail_contact_categorizer.gmail_client import GmailClient
from gmail_contact_categorizer.analyzer import ContactAnalyzer

__all__ = ['authenticate', 'GmailClient', 'ContactAnalyzer']