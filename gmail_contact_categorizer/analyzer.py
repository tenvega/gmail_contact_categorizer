"""
Contact analysis and categorization module.
"""

import re
from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from bs4 import BeautifulSoup
import tldextract
import json
import os

# Download necessary NLTK resources
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)

# Load known domains for automated emails
KNOWN_NEWSLETTER_DOMAINS = {
    'mailchimp.com', 'sendgrid.net', 'mailgun.org', 'amazon.com', 'linkedin.com',
    'facebook.com', 'twitter.com', 'instagram.com', 'github.com', 'medium.com'
}

class ContactAnalyzer:
    """Analyzes and categorizes contacts based on email communication patterns."""
    
    def __init__(self):
        """Initialize the contact analyzer."""
        # Dictionary to store contact data
        self.contacts = defaultdict(lambda: {
            'emails': 0,
            'subject_words': Counter(),
            'body_words': Counter(),
            'salutations': Counter(),
            'signatures': Counter(),
            'times': [],
            'sent_count': 0,
            'received_count': 0,
            'email_bodies': [],
            'domains': Counter(),
            'html_ratio': 0,
            'link_count': 0,
            'reply_patterns': [],
            'automated_features': {
                'regular_sending': False,
                'html_heavy': False,
                'link_heavy': False,
                'template_like': False
            }
        })
        
        # Dictionary to store categorized contacts
        self.categories = {
            'family': [],
            'friends': [],
            'colleagues': [],
            'clients': [],
            'vendors': [],
            'newsletters': [],
            'promotions': [],
            'notifications': []
        }
        
        # Load stopwords
        self.stop_words = set(stopwords.words('english'))
        
        # Load domain patterns
        self._load_domain_patterns()
    
    def _load_domain_patterns(self):
        """Load known domain patterns for automated emails."""
        self.domain_patterns = {
            'newsletters': ['newsletter', 'subscription', 'subscribe', 'unsubscribe'],
            'promotions': ['promo', 'offer', 'deal', 'sale', 'discount', 'coupon'],
            'notifications': ['notification', 'alert', 'update', 'reminder']
        }
    
    def process_emails(self, emails):
        """
        Process a list of emails to extract contact information.
        
        Args:
            emails (list): List of email dictionaries.
        """
        for email in emails:
            if not email:
                continue
                
            # Extract required fields
            contact_email = email['contact_email']
            subject = email['subject']
            body = email['body']
            date = email['date']
            is_sent = email['is_sent']
            
            # Extract domain information
            domain = tldextract.extract(contact_email).registered_domain
            
            # Update contact information
            self._update_contact_info(contact_email, subject, body, date, is_sent, domain)
    
    def _update_contact_info(self, email, subject, body, date, is_sent, domain):
        """
        Update contact information with email data.
        
        Args:
            email (str): Contact email address.
            subject (str): Email subject.
            body (str): Email body.
            date (datetime): Email date.
            is_sent (bool): Whether the email was sent by the user.
            domain (str): Email domain.
        """
        # Increment counters
        self.contacts[email]['emails'] += 1
        if is_sent:
            self.contacts[email]['sent_count'] += 1
        else:
            self.contacts[email]['received_count'] += 1
            
        # Store cleaned text for later analysis
        self.contacts[email]['email_bodies'].append(body)
        
        # Update domain information
        self.contacts[email]['domains'][domain] += 1
            
        # Extract and count words
        subject_words = self._extract_words(subject)
        body_words = self._extract_words(body)
        
        self.contacts[email]['subject_words'].update(subject_words)
        self.contacts[email]['body_words'].update(body_words)
        
        # Extract salutations and signatures
        salutation = self._extract_salutation(body)
        signature = self._extract_signature(body)
        
        if salutation:
            self.contacts[email]['salutations'].update([salutation])
        if signature:
            self.contacts[email]['signatures'].update([signature])
            
        # Store timestamp
        self.contacts[email]['times'].append(date)
        
        # Analyze HTML content and links
        html_ratio, link_count = self._analyze_html_content(body)
        self.contacts[email]['html_ratio'] += html_ratio
        self.contacts[email]['link_count'] += link_count
        
        # Update reply patterns
        self.contacts[email]['reply_patterns'].append({
            'date': date,
            'is_sent': is_sent
        })
    
    def _analyze_html_content(self, body):
        """
        Analyze HTML content and links in email body.
        
        Args:
            body (str): Email body.
            
        Returns:
            tuple: (html_ratio, link_count)
        """
        try:
            soup = BeautifulSoup(body, 'html.parser')
            total_chars = len(body)
            html_chars = len(str(soup))
            links = len(soup.find_all('a'))
            
            html_ratio = html_chars / total_chars if total_chars > 0 else 0
            return html_ratio, links
        except:
            return 0, 0
    
    def _extract_words(self, text):
        """
        Extract meaningful words from text.
        
        Args:
            text (str): Input text.
            
        Returns:
            list: List of meaningful words.
        """
        # Simple tokenization using split and filtering
        words = text.lower().split()
        return [w for w in words if w.isalnum() and w not in self.stop_words]
    
    def _extract_salutation(self, body):
        """
        Extract greeting/salutation from email body.
        
        Args:
            body (str): Email body.
            
        Returns:
            str or None: Extracted salutation or None if not found.
        """
        lines = body.split('\n')
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line = line.strip()
            if line and (line.startswith('Hi') or line.startswith('Hello') or 
                        line.startswith('Dear') or line.startswith('Hey')):
                return line
        return None
    
    def _extract_signature(self, body):
        """
        Extract signature from email body.
        
        Args:
            body (str): Email body.
            
        Returns:
            str or None: Extracted signature or None if not found.
        """
        lines = body.split('\n')
        for i, line in enumerate(lines[-10:]):  # Check last 10 lines
            line = line.strip()
            if line and (line.startswith('Best') or line.startswith('Regards') or 
                        line.startswith('Thanks') or line.startswith('Cheers')):
                return line
        return None
    
    def _calculate_automated_features(self, email, data):
        """
        Calculate features that indicate automated emails.
        
        Args:
            email (str): Contact email.
            data (dict): Contact data.
            
        Returns:
            dict: Automated features.
        """
        features = {
            'regular_sending': False,
            'html_heavy': False,
            'link_heavy': False,
            'template_like': False
        }
        
        # Check for regular sending patterns
        if len(data['times']) >= 3:
            times = sorted(data['times'])
            intervals = [(times[i+1] - times[i]).total_seconds() 
                        for i in range(len(times)-1)]
            if np.std(intervals) < 3600:  # Less than 1 hour variance
                features['regular_sending'] = True
        
        # Check HTML and link ratios
        avg_html_ratio = data['html_ratio'] / data['emails']
        avg_links = data['link_count'] / data['emails']
        
        features['html_heavy'] = avg_html_ratio > 0.5
        features['link_heavy'] = avg_links > 3
        
        # Check for template-like content
        if len(data['email_bodies']) >= 3:
            # Compare similarity between email bodies
            vectorizer = TfidfVectorizer()
            try:
                tfidf_matrix = vectorizer.fit_transform(data['email_bodies'])
                similarity = (tfidf_matrix * tfidf_matrix.T).toarray()
                if np.mean(similarity) > 0.8:  # High similarity between emails
                    features['template_like'] = True
            except:
                pass
        
        return features
    
    def _analyze_domain(self, domain, subject, body):
        """
        Analyze domain and content for automated email patterns.
        
        Args:
            domain (str): Email domain.
            subject (str): Email subject.
            body (str): Email body.
            
        Returns:
            str: Category hint based on domain analysis.
        """
        # Check known domains
        if domain in KNOWN_NEWSLETTER_DOMAINS:
            return 'newsletters'
        
        # Check domain patterns
        for category, patterns in self.domain_patterns.items():
            if any(pattern in subject.lower() or pattern in body.lower() 
                  for pattern in patterns):
                return category
        
        return None
    
    def categorize_contacts(self):
        """
        Analyze contacts and categorize them using a two-stage approach.
        
        Returns:
            dict: Dictionary of categorized contacts.
        """
        print(f"Analyzing {len(self.contacts)} contacts...")
        
        # First stage: Identify automated vs human emails
        automated_contacts = []
        human_contacts = []
        
        for email, data in self.contacts.items():
            if data['emails'] < 3:
                continue
            
            # Calculate automated features
            automated_features = self._calculate_automated_features(email, data)
            data['automated_features'] = automated_features
            
            # Get domain analysis
            domain = data['domains'].most_common(1)[0][0]
            domain_category = self._analyze_domain(domain, 
                                                 data['subject_words'].most_common(1)[0][0] if data['subject_words'] else '',
                                                 ' '.join(data['email_bodies']))
            
            # Determine if contact is automated
            is_automated = (
                automated_features['regular_sending'] or
                automated_features['html_heavy'] or
                automated_features['link_heavy'] or
                automated_features['template_like'] or
                domain_category is not None
            )
            
            if is_automated:
                automated_contacts.append(email)
            else:
                human_contacts.append(email)
        
        # Second stage: Categorize human contacts
        if human_contacts:
            self._categorize_human_contacts(human_contacts)
        
        # Categorize automated contacts
        self._categorize_automated_contacts(automated_contacts)
        
        return self.categories
    
    def _categorize_human_contacts(self, contacts):
        """
        Categorize human contacts using hierarchical clustering.
        
        Args:
            contacts (list): List of contact emails.
        """
        # Prepare features for clustering
        contact_features = []
        contact_emails = []
        
        for email in contacts:
            data = self.contacts[email]
            
            # Calculate features
            features = self._extract_human_features(data)
            contact_features.append(features)
            contact_emails.append(email)
        
        if not contact_features:
            return
        
        # Normalize features
        scaler = StandardScaler()
        contact_features = scaler.fit_transform(contact_features)
        
        # Apply hierarchical clustering
        clustering = AgglomerativeClustering(n_clusters=5)
        clusters = clustering.fit_predict(contact_features)
        
        # Interpret clusters and assign to categories
        for i, email in enumerate(contact_emails):
            cluster = clusters[i]
            self._assign_human_category(email, cluster, contact_features[i])
    
    def _extract_human_features(self, data):
        """
        Extract features for human contact categorization.
        
        Args:
            data (dict): Contact data.
            
        Returns:
            list: Feature vector.
        """
        total_emails = data['emails']
        sent_ratio = data['sent_count'] / total_emails if total_emails > 0 else 0
        
        # Calculate word ratios
        informal_words = sum(data['body_words'].get(w, 0) for w in 
                           ['thanks', 'love', 'hey', 'cheers', 'haha', 'lol'])
        formal_words = sum(data['body_words'].get(w, 0) for w in 
                         ['sincerely', 'regarding', 'request', 'meeting'])
        business_words = sum(data['body_words'].get(w, 0) for w in 
                           ['project', 'client', 'meeting', 'report', 'business'])
        family_words = sum(data['body_words'].get(w, 0) for w in 
                         ['mom', 'dad', 'sister', 'brother', 'family'])
        
        # Calculate time features
        weekday_emails = sum(1 for dt in data['times'] if dt.weekday() < 5)
        weekend_emails = sum(1 for dt in data['times'] if dt.weekday() >= 5)
        evening_emails = sum(1 for dt in data['times'] 
                           if dt.hour >= 18 or dt.hour < 7)
        
        # Calculate reply patterns
        reply_times = []
        for i in range(1, len(data['reply_patterns'])):
            if data['reply_patterns'][i]['is_sent'] != data['reply_patterns'][i-1]['is_sent']:
                reply_time = (data['reply_patterns'][i]['date'] - 
                            data['reply_patterns'][i-1]['date']).total_seconds()
                reply_times.append(reply_time)
        
        avg_reply_time = np.mean(reply_times) if reply_times else 0
        
        # Get salutation and signature features
        salutation_features = []
        if data['salutations']:
            most_common_salutation = data['salutations'].most_common(1)[0][0].lower()
            salutation_features = [
                1 if "dear" in most_common_salutation else 0,
                1 if "hi" in most_common_salutation else 0,
                1 if "hey" in most_common_salutation else 0,
                1 if "hello" in most_common_salutation else 0
            ]
        else:
            salutation_features = [0, 0, 0, 0]
            
        signature_features = []
        if data['signatures']:
            most_common_signature = data['signatures'].most_common(1)[0][0].lower()
            signature_features = [
                1 if "sincerely" in most_common_signature else 0,
                1 if "regards" in most_common_signature else 0,
                1 if "thanks" in most_common_signature else 0,
                1 if "best" in most_common_signature else 0
            ]
        else:
            signature_features = [0, 0, 0, 0]
        
        return [
            sent_ratio,
            informal_words / (total_emails + 1),
            formal_words / (total_emails + 1),
            business_words / (total_emails + 1),
            family_words / (total_emails + 1),
            weekday_emails / (len(data['times']) + 1),
            weekend_emails / (len(data['times']) + 1),
            evening_emails / (len(data['times']) + 1),
            avg_reply_time / 3600,  # Convert to hours
        ] + salutation_features + signature_features
    
    def _assign_human_category(self, email, cluster, features):
        """
        Assign a category to a human contact based on cluster and features.
        
        Args:
            email (str): Contact email.
            cluster (int): Cluster number.
            features (array): Feature vector.
        """
        # Define feature thresholds for each category
        thresholds = {
            'family': {
                'family_words': 0.1,
                'informal_words': 0.2,
                'weekend_ratio': 0.3
            },
            'friends': {
                'informal_words': 0.15,
                'reply_time': 24  # hours
            },
            'colleagues': {
                'business_words': 0.15,
                'formal_words': 0.1,
                'weekday_ratio': 0.8
            },
            'clients': {
                'business_words': 0.2,
                'formal_words': 0.15,
                'sent_ratio': 0.7
            },
            'vendors': {
                'business_words': 0.1,
                'formal_words': 0.1,
                'sent_ratio': 0.3
            }
        }
        
        # Calculate ratios
        ratios = {
            'family_words': features[4],
            'informal_words': features[1],
            'formal_words': features[2],
            'business_words': features[3],
            'weekend_ratio': features[6],
            'weekday_ratio': features[5],
            'reply_time': features[8],
            'sent_ratio': features[0]
        }
        
        # Assign category based on feature thresholds
        for category, threshold in thresholds.items():
            if all(ratios[k] >= v for k, v in threshold.items()):
                self.categories[category].append(email)
                return
        
        # If no category matches, assign based on cluster
        category_map = {
            0: 'family',
            1: 'friends',
            2: 'colleagues',
            3: 'clients',
            4: 'vendors'
        }
        self.categories[category_map[cluster]].append(email)
    
    def _categorize_automated_contacts(self, contacts):
        """
        Categorize automated contacts based on their features.
        
        Args:
            contacts (list): List of contact emails.
        """
        for email in contacts:
            data = self.contacts[email]
            domain = data['domains'].most_common(1)[0][0]
            
            # Check domain patterns first
            domain_category = self._analyze_domain(domain, 
                                                 data['subject_words'].most_common(1)[0][0] if data['subject_words'] else '',
                                                 ' '.join(data['email_bodies']))
            
            if domain_category:
                self.categories[domain_category].append(email)
                continue
            
            # If no domain pattern matches, use feature-based categorization
            features = data['automated_features']
            
            if features['regular_sending'] and features['template_like']:
                self.categories['newsletters'].append(email)
            elif features['html_heavy'] and features['link_heavy']:
                self.categories['promotions'].append(email)
            else:
                self.categories['notifications'].append(email)
