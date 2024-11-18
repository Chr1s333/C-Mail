import os
import pickle
import base64
import pandas as pd
import streamlit as st
import re
import pyrebase
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from dotenv import load_dotenv
from contacts import get_contacts  # Import the get_contacts function
from templates import get_templates  # Import the get_templates function
import datetime
import time
import threading

def sanitize_email(email):
    # Replace "@" and "." with "_" to make it Firebase-compatible
    return email.replace('@', '_at_').replace('.', '_dot_')

config = {
    "apiKey": os.getenv('API_KEY'),
    "authDomain": os.getenv('AUTH_DOMAIN'),
    "databaseURL": os.getenv('DATABASE_URL'),
    "projectId": os.getenv('PROJECT_ID'),
    "storageBucket": os.getenv('STORAGE_BUCKET'),
    "messagingSenderId": os.getenv('MESSAGING_SENDER_ID'),
    "appId": os.getenv('APP_ID')
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

# Logging configuration
logging.basicConfig(
    filename="cmail_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load environment variables
load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Function to authenticate and initialize Gmail API client
def authenticate_gmail():
    creds = None
    token_path = 'token.pickle'

    # Load credentials from file
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no credentials or they are invalid, authenticate using credentials.json
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv('CREDENTIALS_PATH'), SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def schedule_email(email_id, send_time, send_function, **kwargs):
    def email_task():
        while True:
            current_time = datetime.datetime.now()
            if current_time >= send_time:
                send_function(**kwargs)
                logging.info(f"Scheduled email with ID {email_id} sent at {current_time}")
                break
            time.sleep(10)

    threading.Thread(target=email_task, daemon=True).start()

# Function to create the email message
def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw}

# Function to send the email using Gmail API
def send_email(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        logging.info(f"Email sent successfully by Gmail with message ID: {message['id']}")
        return True, message['id']
    except HttpError as error:
        error_details = error.resp.data.decode('utf-8')
        error_code = error.resp.status
        logging.error(f"Error sending email - Code: {error_code}, Details: {error_details}")

        if error_code == 400:
            if "Address not found" in error_details or "Domain name not found" in error_details:
                return False, "Invalid email address or domain not found."
            else:
                return False, "Bad Request: Please check the email addresses."
        elif error_code == 404:
            return False, "Not Found: The requested resource could not be found."
        else:
            return False, f"An error occurred: {error_details}"

    return False, "Unknown error occurred."

# Function to validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    valid = re.match(pattern, email) is not None
    if not valid:
        logging.warning(f"Invalid email format: {email}")
    return valid

# Function to process CSV emails
def process_csv_emails(uploaded_file):
    recipient_emails = set()  # Use a set to avoid duplicates
    try:
        df = pd.read_csv(uploaded_file)
        if 'email' not in df.columns:
            logging.error("CSV missing 'email' column")
            return None, "CSV must contain an 'email' column."

        for email in df['email'].dropna().unique():  # Remove NaNs, get unique emails
            email = email.strip()
            if is_valid_email(email):
                recipient_emails.add(email)
            else:
                st.warning(f"Invalid email format in CSV: {email}")

        logging.info(f"Processed CSV - valid emails found: {len(recipient_emails)}")
        return list(recipient_emails), None  # Return emails list and no error
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
        return None, f"Error reading CSV: {e}"  # Return error for display

# Firebase log saving and retrieval functions
def save_email_log(user_email, recipient, status, service, timestamp, subject=None, error=None):

    sanitized_user_email = sanitize_email(user_email)  # Sanitize the email
    sanitized_recipient = sanitize_email(recipient)  # Sanitize recipient email

    log_data = {
        "recipient": recipient,
        "status": status,
        "service": service,
        "Timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),  # ISO 8601 format
        "subject": subject if subject else "No Subject",
        "error": error if error else None,
    }

    # Push sanitized email logs to Firebase
    db.child("email_logs").child(sanitized_user_email).push(log_data)

def gmail_page(display_sidebar):
    # Display the sidebar
    display_sidebar()

    st.header("Compose Mail using Gmail")

    # Initialize email delivery log in session state if it doesn't exist
    if 'email_delivery_log' not in st.session_state:
        st.session_state.email_delivery_log = []

    # Load contacts and templates for the current user
    user_email = st.session_state.get("user_email")
    contacts = get_contacts(user_email)
    contact_emails = [contact['email'] for contact in contacts]

    # Multiselect for contacts
    selected_contacts = st.multiselect("Select Contacts", options=contact_emails)

    # Button to send to all contacts
    if st.button("Send to All Contacts"):
        selected_contacts = contact_emails
        st.session_state.selected_contacts = selected_contacts
        st.success(f"All contacts selected: {', '.join(selected_contacts)}")
        logging.info(f"All contacts selected for email: {', '.join(selected_contacts)}")

    # Load templates for the current user
    templates = get_templates(user_email)
    template_names = [template['name'] for template in templates.values()]
    selected_template = st.selectbox("Select a Template", options=[""] + template_names)

    message_text = ""
    subject = ""

    if selected_template:
        selected_template_data = next(
            (template for template in templates.values() if template['name'] == selected_template), None)

        if selected_template_data:
            message_text = selected_template_data['content']
            subject = selected_template_data.get('subject', '')

    # Form to collect email data
    with st.form(key='gmail_form'):
        subject = st.text_input('Subject', value=subject)
        message_text = st.text_area('Message', value=message_text)
        recipient_email = st.text_input(
            'Recipient Email (For Multiple Recipients Enter Mail-id separated by comma)', 
            value=", ".join(st.session_state.get("selected_contacts", selected_contacts))
        )
        uploaded_file = st.file_uploader("Import CSV of Recipient Emails (CSV must contain an 'email' column)", type=['csv'])
        schedule_email_check = st.checkbox("Schedule Email")
        send_datetime = None
        if schedule_email_check:
            send_date = st.date_input("Send Date")
            send_time = st.time_input("Send Time")
            send_datetime = datetime.datetime.combine(send_date, send_time)
        submit_button = st.form_submit_button("Send Email")

    recipient_list = set()

    if recipient_email:
        for email in recipient_email.split(','):
            email = email.strip()
            if is_valid_email(email):
                recipient_list.add(email)
            else:
                st.error(f"Invalid email format: {email}")

    if uploaded_file is not None:
        csv_emails, csv_error = process_csv_emails(uploaded_file)
        if csv_error:
            st.error(csv_error)
        else:
            recipient_list.update(csv_emails)

    if recipient_list:
        st.write("Recipient Emails:")
        st.dataframe(pd.DataFrame(list(recipient_list), columns=["Email"]).style.set_properties(**{'text-align': 'center'}))

    if submit_button:
        if subject and message_text and recipient_list:
            if schedule_email_check and send_datetime:
                # Get current time
                now = datetime.datetime.now()

                # Check if the selected time is in the future
                if send_datetime < now:
                    st.warning("The selected time is in the past. Please choose a time in the future.")
                else:
                    # Proceed with scheduling for each recipient
                    service = authenticate_gmail()
                    for recipient in recipient_list:
                        schedule_email(
                            email_id=f"{user_email}_{send_datetime.strftime('%Y%m%d%H%M%S')}_{recipient}",
                            send_time=send_datetime,
                            send_function=send_email,
                            service=service,
                            user_id="me",
                            message=create_message("me", recipient, subject, message_text)
                        )
                    st.success(f"Emails scheduled successfully for {send_datetime.strftime('%H:%M')}.")
                    save_email_log(user_email, recipient, "Scheduled", "Gmail", send_datetime, subject)
                    logging.info(f"Scheduled emails for {send_datetime.strftime('%H:%M')} to {', '.join(recipient_list)}.")
            else:
                # Immediate email sending
                service = authenticate_gmail()
                sender_email = 'me'
                success_list = []
                failure_list = []

                for recipient in recipient_list:
                    email_message = create_message(sender_email, recipient, subject, message_text)
                    success, response = send_email(service, 'me', email_message)
                    if success:
                        success_list.append(recipient)
                        save_email_log(user_email, recipient, "Sent", "Gmail", datetime.datetime.now(), subject)
                        st.session_state.email_delivery_log.append({"Email": recipient, "Status": "Sent", "Service": "Gmail"})
                        logging.info(f"Email sent to {recipient}")
                    else:
                        failure_list.append((recipient, response))
                        save_email_log(user_email, recipient, "Failed", "Gmail", datetime.datetime.now(), subject, response)
                        st.session_state.email_delivery_log.append({"Email": recipient, "Status": "Failed", "Service": "Gmail", "Error": response})
                        logging.error(f"Failed to send email to {recipient}: {response}")

                if success_list:
                    st.success(f"Emails sent successfully to: {', '.join(success_list)}")
                if failure_list:
                    st.error(f"Failed to send emails to: {', '.join([item[0] for item in failure_list])}")
        else:
            st.error("Subject, message, and at least one valid recipient email are required.")  
