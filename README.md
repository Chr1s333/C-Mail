# Cmail - A Mass Mailing Application

Cmail is a powerful mass mailing application built using Streamlit and Firebase, designed to streamline the process of sending bulk emails through Gmail and Outlook. The application allows users to manage recipients, send personalized emails, track delivery status, and view detailed analytics. The app ensures user data security through environment variables and session management using cookies.

## Features

### Core Functionality
- **User Authentication**: Users can sign up and log in using Firebase authentication.
- **Session Management**: Persistent login sessions are managed securely with cookies.
- **Gmail and Outlook Integration**: Users can compose and send emails using either Gmail or Outlook.
- **CSV Import for Recipients**: Allows users to import a list of recipient email addresses from a CSV file.
- **Email Validation**: Built-in validation for recipient email addresses to ensure valid formatting.
- **Bulk Email Sending**: Send emails to multiple recipients at once, with feedback on delivery success and failure.
- **Email Delivery Log**: A log of email statuses, showing which emails were successfully sent and which failed, including detailed error messages.
- **Dashboard for Tracking**: A dedicated dashboard for monitoring email delivery statistics, such as email status (Sent, Failed, Delivered, etc.) with filters for easy sorting.

### Security
- **Environment Variables**: Sensitive information (API keys, database URLs, SMTP credentials) is stored securely using environment variables managed through the `.env` file.
- **OAuth 2.0 for Outlook**: Secure authentication for sending emails through Outlook is implemented using OAuth 2.0.

## Installation

### Prerequisites
- Python 3.7 or higher
- Firebase project credentials
- Gmail and Outlook API credentials

### Steps to Set Up the Application
1. Clone the repository:
   ```bash
   git clone https://github.com/Mass-Mailing-Application_oct_2024/cmail.git
   cd cmail

2. Create a `.env` file in the project root with the following content:
   ```env
   API_KEY=your_api_key_here
   AUTH_DOMAIN=your_auth_domain_here
   DATABASE_URL=your_database_url_here
   PROJECT_ID=your_project_id_here
   STORAGE_BUCKET=your_storage_bucket_here
   MESSAGING_SENDER_ID=your_messaging_sender_id_here
   APP_ID=your_app_id_here
   COOKIE_MANAGER_PASSWORD=your_secure_cookie_password
3. Install the required Python packages:
    pip install -r requirements.txt

## Run the application:
    streamlit run main.py
