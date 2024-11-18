# Cmail - A Mass Mailing Application

Cmail is a powerful mass mailing application built using Streamlit and Firebase, designed to streamline the process of sending bulk emails through Gmail and Outlook. The application allows users to manage recipients, send personalized emails, track delivery status, and view detailed analytics. The app ensures user data security through environment variables and session management using cookies.
## Features

### Core Functionalities
- **User Authentication**  
  - Secure user signup and login via Firebase authentication.
- **Session Management**  
  - Persistent sessions managed securely with cookies.
- **Gmail and Outlook Integration**  
  - Seamless email composition and delivery through Gmail and Outlook APIs.
- **CSV Import for Recipients**  
  - Bulk import of recipient email addresses from CSV files.
- **Email Validation**  
  - Validation to ensure proper formatting of recipient email addresses.
- **Bulk Email Sending**  
  - Ability to send emails to multiple recipients at once with real-time delivery feedback.
- **Email Scheduling**  
  - Schedule emails for later delivery with flexible options.
- **Email Delivery Log**  
  - Detailed logs showing email statuses (Sent, Failed, Delivered, etc.) and error details.
- **Dashboard and Analytics**  
  - Interactive dashboard to track email statistics with filters for easy sorting and visualization.

### Contact and Template Management
- **Contact Management**  
  - CRUD operations for managing recipients, including importing from CSV and other formats.
- **Template Management**  
  - Create, read, update, and delete email templates with various predefined options (Basic Email, HTML Email, Personalized Email, etc.).

### Security
- **Environment Variables**  
  - Sensitive credentials like API keys, database URLs, and SMTP credentials are securely stored using a `.env` file.
- **OAuth 2.0 Authentication**  
  - Secure integration with Outlook and Gmail APIs using OAuth 2.0.

---
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
