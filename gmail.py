import os
import pickle
import base64
import pandas as pd
import streamlit as st
import re
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from dotenv import load_dotenv

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
        return True, message['id']
    except HttpError as error:
        # Extract error details from the HttpError
        error_details = error.resp.data.decode('utf-8')
        error_code = error.resp.status

        # Check for specific error messages and categorize them
        if error_code == 400:
            # Bad Request: Email not valid
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
    # Simple regex pattern for validating an email address
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

# Gmail Page Function with CSV import and table for recipient emails
def gmail_page(display_sidebar):
    # Display the sidebar
    display_sidebar()

    st.header("Compose Mail using Gmail")

    # Initialize email delivery log in session state if it doesn't exist
    if 'email_delivery_log' not in st.session_state:
        st.session_state.email_delivery_log = []

    # Form to collect email data
    with st.form(key='gmail_form'):
        subject = st.text_input('Subject')
        message_text = st.text_area('Message')
        
        # Input for multiple recipient emails (comma-separated)
        recipient_email = st.text_input('Recipient Email (For Multiple Recipients Enter Mail-id separated by comma)')

        # File uploader for CSV
        uploaded_file = st.file_uploader("Import CSV of Recipient Emails(CSV must contain an 'email' column)", type=['csv'])

        submit_button = st.form_submit_button(label='Send Email')

    # Process recipient emails
    recipient_list = []

    # Add manually entered emails to the list if provided (comma-separated)
    if recipient_email:
        for email in recipient_email.split(','):
            email = email.strip()
            if is_valid_email(email):
                recipient_list.append(email)
            else:
                st.error(f"Invalid email format: {email}")

    # Process CSV file if uploaded
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if 'email' in df.columns:
                for email in df['email'].tolist():
                    if is_valid_email(email):
                        recipient_list.append(email)
                    else:
                        st.error(f"Invalid email format in CSV: {email}")
            else:
                st.error("CSV must contain an 'email' column.")
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    # Show the recipient emails in a table format (center aligned)
    if recipient_list:
        st.write("Recipient Emails:")
        st.dataframe(pd.DataFrame(recipient_list, columns=["Email"]).style.set_properties(**{'text-align': 'center'}))

    # Sending the email to recipients when submit button is clicked
    if submit_button:
        if subject and message_text and recipient_list:
            service = authenticate_gmail()
            sender_email = 'me'  # Use 'me' to indicate the authenticated user
            success_list = []
            failure_list = []

            for recipient in recipient_list:
                email_message = create_message(sender_email, recipient, subject, message_text)
                success, response = send_email(service, 'me', email_message)
                if success:
                    success_list.append(recipient)
                    # Log successful delivery
                    st.session_state.email_delivery_log.append({"Email": recipient, "Status": "Sent", "Service": "Gmail"})
                else:
                    failure_list.append((recipient, response))
                    # Log failure delivery with error message
                    st.session_state.email_delivery_log.append({"Email": recipient, "Status": "Failed", "Service": "Gmail", "Error": response})

            # Show success and failure messages
            if success_list:
                st.success(f"Emails sent successfully to: {', '.join(success_list)}")

            if failure_list:
                st.error("Failed to send emails to:")
                for failure in failure_list:
                    st.error(f"{failure[0]} - Error: {failure[1]}")

            # Display email delivery log with error messages
            st.subheader("Email Delivery Log")
            delivery_log_df = pd.DataFrame(st.session_state.email_delivery_log)
            st.dataframe(delivery_log_df)

        else:
            st.error("Please fill out the subject, message, and at least one recipient.")