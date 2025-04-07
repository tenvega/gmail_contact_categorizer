# Gmail Contact Categorizer

A Python tool that uses AI techniques to automatically categorize your Gmail contacts into three groups:
- Family & Friends
- Business Contacts
- Clients

The tool analyzes email communication patterns, language, timing, and other factors to intelligently group your contacts.

## Features

- **Automatic Contact Categorization**: Uses machine learning to identify and categorize contacts
- **Multiple Export Options**: 
  - Export to Google Sheets with professional formatting and color-coding
  - Export to Excel with similar formatting
- **Comprehensive Analysis**: Examines various factors including:
  - Communication frequency and patterns
  - Language formality and content
  - Time of day and day of week patterns
  - Greetings and signatures
- **Detailed Reports**: Includes total emails, common topics, and last contact date for each contact

## Installation

### Prerequisites

- Python 3.7 or higher
- A Google account with Gmail
- Google API credentials (see setup instructions)

### Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/gmail-contact-categorizer.git
   cd gmail-contact-categorizer
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up Google API access:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Gmail API, Google Sheets API, and Google Drive API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download the credentials JSON file and save it as `credentials.json` in the project directory

## Usage

### Basic Usage

Run the tool with default settings:

```
python main.py
```

This will:
- Process all available emails in your Gmail account
- Categorize your contacts
- Export the results to Google Sheets

### Command Line Options

```
python main.py --help
```

Available options:
- `--max-emails NUM`: Limit the number of emails to analyze
- `--export-type TYPE`: Choose between "sheets" (default) or "excel"
- `--output NAME`: Specify the output filename or sheet title
- `--verbose`: Enable detailed progress information

Examples:

```
# Analyze the last 1000 emails and export to Excel
python main.py --max-emails 1000 --export-type excel

# Export to a specific Google Sheet name
python main.py --export-type sheets --output "My Contact Categories"
```

## How It Works

1. **Authentication**: Securely connects to your Gmail account using OAuth
2. **Email Analysis**: Fetches and processes your email communications
3. **Feature Extraction**: Identifies patterns in communication style, timing, etc.
4. **Machine Learning**: Uses k-means clustering to group contacts
5. **Refinement**: Applies text analysis to improve categorization
6. **Export**: Creates a professionally formatted report

## Privacy & Security

- All processing happens locally on your machine
- OAuth authentication ensures secure access without storing passwords
- Your data is not sent to any third-party servers
- The tool only requires read access to your Gmail

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Thanks to the scikit-learn and NLTK teams for their excellent libraries
- Google for providing the Gmail, Sheets, and Drive APIs
