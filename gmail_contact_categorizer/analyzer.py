"""
Contact analysis and categorization module.
"""

import re
from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# Download necessary NLTK resources
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)


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
            'email_bodies': []
        })
        
        # Dictionary to store categorized contacts
        self.categories = {
            'family_friends': [],
            'business_contacts': [],
            'clients': []
        }
        
        # Load stopwords
        self.stop_words = set(stopwords.words('english'))
    
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
            
            # Update contact information
            self._update_contact_info(contact_email, subject, body, date, is_sent)
    
    def _update_contact_info(self, email, subject, body, date, is_sent):
        """
        Update contact information with email data.
        
        Args:
            email (str): Contact email address.
            subject (str): Email subject.
            body (str): Email body.
            date (datetime): Email date.
            is_sent (bool): Whether the email was sent by the user.
        """
        # Increment counters
        self.contacts[email]['emails'] += 1
        if is_sent:
            self.contacts[email]['sent_count'] += 1
        else:
            self.contacts[email]['received_count'] += 1
            
        # Store cleaned text for later analysis
        self.contacts[email]['email_bodies'].append(body)
            
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
    
    def _extract_words(self, text):
        """
        Extract meaningful words from text.
        
        Args:
            text (str): Input text.
            
        Returns:
            list: List of meaningful words.
        """
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in self.stop_words]
    
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
            if line and (line.startswith('Hi') or line.startswith('Hello') or line.startswith('Dear')):
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
            if line and (line.startswith('Best') or line.startswith('Regards') or line.startswith('Thanks')):
                return line
        return None
    
    def categorize_contacts(self):
        """
        Analyze contacts and categorize them.
        
        Returns:
            dict: Dictionary of categorized contacts.
        """
        print(f"Analyzing {len(self.contacts)} contacts...")
        
        # Prepare features for clustering
        contact_features = []
        contact_emails = []
        
        for email, data in self.contacts.items():
            # Skip contacts with too few emails
            if data['emails'] < 3:
                continue
                
            # Calculate features
            total_emails = data['emails']
            sent_ratio = data['sent_count'] / total_emails if total_emails > 0 else 0
            informal_words = sum(data['body_words'].get(w, 0) for w in ['thanks', 'love', 'hey', 'cheers'])
            formal_words = sum(data['body_words'].get(w, 0) for w in ['sincerely', 'regarding', 'request', 'meeting'])
            business_words = sum(data['body_words'].get(w, 0) for w in ['project', 'client', 'meeting', 'report', 'business'])
            
            # Extract top salutations and signatures
            top_salutation = data['salutations'].most_common(1)[0][0] if data['salutations'] else ""
            top_signature = data['signatures'].most_common(1)[0][0] if data['signatures'] else ""
            
            # Calculate time features
            weekday_emails = 0
            weekend_emails = 0
            evening_emails = 0
            
            for dt in data['times']:
                if dt.weekday() < 5:  # 0-4 are Monday to Friday
                    weekday_emails += 1
                else:
                    weekend_emails += 1
                    
                if dt.hour >= 18 or dt.hour < 7:
                    evening_emails += 1
            
            # Create feature vector
            features = [
                sent_ratio,
                informal_words / (total_emails + 1),
                formal_words / (total_emails + 1),
                business_words / (total_emails + 1),
                weekday_emails / (len(data['times']) + 1) if data['times'] else 0,
                weekend_emails / (len(data['times']) + 1) if data['times'] else 0,
                evening_emails / (len(data['times']) + 1) if data['times'] else 0,
                1 if "dear" in top_salutation.lower() else 0,
                1 if "hi" in top_salutation.lower() else 0,
                1 if "hey" in top_salutation.lower() else 0,
                1 if "hello" in top_salutation.lower() else 0,
                1 if "sincerely" in top_signature.lower() else 0,
                1 if "regards" in top_signature.lower() else 0,
                1 if "thanks" in top_signature.lower() else 0,
                1 if "best" in top_signature.lower() else 0
            ]
            
            contact_features.append(features)
            contact_emails.append(email)
        
        if not contact_features:
            print("Not enough contact data for analysis.")
            return self.categories
            
        # Apply K-means clustering with 3 clusters (family/friends, business, clients)
        contact_features = np.array(contact_features)
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(contact_features)
        
        # Interpret clusters
        cluster_centers = kmeans.cluster_centers_
        
        # Determine which cluster represents which category
        # Higher informal words and weekend emails typically indicate family/friends
        family_idx = np.argmax(cluster_centers[:, 1] + cluster_centers[:, 5])
        
        # Higher business words and formality typically indicate business contacts
        business_idx = np.argmax(cluster_centers[:, 2] + cluster_centers[:, 3])
        
        # The remaining cluster is likely clients
        client_idx = 3 - family_idx - business_idx
        if client_idx < 0:
            # Handle edge case where two indices are the same
            family_idx, business_idx, client_idx = 0, 1, 2
        
        # Assign contacts to categories
        for i, email in enumerate(contact_emails):
            if clusters[i] == family_idx:
                self.categories['family_friends'].append(email)
            elif clusters[i] == business_idx:
                self.categories['business_contacts'].append(email)
            else:
                self.categories['clients'].append(email)
                
        # Refine categorization with text content analysis
        self._refine_with_text_analysis()
        
        # Collect full contact data
        categorized_contacts = {
            'family_friends': [],
            'business_contacts': [],
            'clients': []
        }
        
        for category, emails in self.categories.items():
            for email in emails:
                if email in self.contacts:
                    contact_data = self.contacts[email]
                    contact_info = {
                        'email': email,
                        'total_emails': contact_data['emails'],
                        'sent': contact_data['sent_count'],
                        'received': contact_data['received_count'],
                        'last_contact': max(contact_data['times']) if contact_data['times'] else None,
                        'common_topics': [word for word, _ in contact_data['subject_words'].most_common(5)]
                    }
                    categorized_contacts[category].append(contact_info)
        
        return categorized_contacts
    
    def _refine_with_text_analysis(self):
        """Refine categorization using TF-IDF on email bodies."""
        # Prepare text data
        emails_by_category = {
            'family_friends': [],
            'business_contacts': [],
            'clients': []
        }
        
        # Collect email bodies by initial category
        for category, emails in self.categories.items():
            for email in emails:
                if email in self.contacts:
                    for body in self.contacts[email]['email_bodies']:
                        emails_by_category[category].append(body)
        
        # Check if we have enough data
        total_emails = sum(len(emails) for emails in emails_by_category.values())
        if total_emails < 30:  # Arbitrary threshold
            return  # Skip refinement if not enough data
        
        # Extract key terms from each category
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        
        category_terms = {}
        for category, texts in emails_by_category.items():
            if not texts:
                continue
                
            # Combine texts for the category
            combined_text = " ".join(texts)
            
            # Extract top terms
            tfidf = vectorizer.fit_transform([combined_text])
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top 20 terms
            top_indices = np.argsort(tfidf.toarray()[0])[-20:]
            category_terms[category] = [feature_names[i] for i in top_indices]
        
        # Re-evaluate contacts with borderline classifications
        for email, data in self.contacts.items():
            # Find current category
            current_category = None
            for category, emails in self.categories.items():
                if email in emails:
                    current_category = category
                    break
                    
            if not current_category:
                continue
                
            # Count term matches in each category
            combined_text = " ".join(data['email_bodies']).lower()
            matches = {}
            
            for category, terms in category_terms.items():
                matches[category] = sum(combined_text.count(term) for term in terms)
            
            # Find best matching category based on terms
            best_category = max(matches, key=matches.get)
            
            # If best category differs from current, and the difference is significant, reassign
            if best_category != current_category and matches[best_category] > matches[current_category] * 1.5:
                self.categories[current_category].remove(email)
                self.categories[best_category].append(email)
