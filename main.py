#!/usr/bin/env python3
"""
Gmail Contact Categorizer
-------------------------
A tool to automatically categorize Gmail contacts into family/friends, 
business contacts, and clients based on email communication patterns.
"""

import argparse
from gmail_contact_categorizer.auth import authenticate
from gmail_contact_categorizer.gmail_client import GmailClient
from gmail_contact_categorizer.analyzer import ContactAnalyzer
from gmail_contact_categorizer.exporters import get_exporter


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Gmail Contact Categorizer')
    
    parser.add_argument(
        '--max-emails', 
        type=int, 
        default=None,
        help='Maximum number of emails to analyze. If not provided, all emails will be analyzed.'
    )
    
    parser.add_argument(
        '--export-type', 
        choices=['sheets', 'excel'], 
        default='sheets',
        help='Export type: "sheets" for Google Sheets or "excel" for Excel file'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='Output filename for Excel or sheet title for Google Sheets'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Set default output names if not provided
    if not args.output:
        if args.export_type == 'excel':
            args.output = 'contact_categories.xlsx'
        else:
            args.output = 'Gmail Contact Categories'
    
    # Initialize verbose output
    verbose = args.verbose
    
    # Authenticate with Google APIs
    if verbose:
        print("Authenticating with Google APIs...")
    credentials = authenticate()
    
    # Initialize Gmail client
    gmail_client = GmailClient(credentials)
    
    # Fetch emails
    if verbose:
        print(f"Fetching emails{' (max: ' + str(args.max_emails) + ')' if args.max_emails else ''}...")
    emails = gmail_client.fetch_emails(max_emails=args.max_emails)
    
    # Analyze contacts
    if verbose:
        print(f"Analyzing {len(emails)} emails...")
    analyzer = ContactAnalyzer()
    analyzer.process_emails(emails)
    categories = analyzer.categorize_contacts()
    
    # Export results
    if verbose:
        print(f"Exporting results as {args.export_type}...")
    exporter = get_exporter(args.export_type, credentials)
    result = exporter.export(categories, args.output)
    
    # Print summary
    print("\nContact Categorization Summary:")
    for category, contacts in categories.items():
        print(f"{category.replace('_', ' ').title()}: {len(contacts)} contacts")
    
    if args.export_type == 'sheets':
        print(f"\nResults available at: {result}")
    else:
        print(f"\nResults saved to: {result}")



if __name__ == "__main__":
    main()
