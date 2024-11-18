import streamlit as st
import pandas as pd
import os
import re
import pyrebase
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from contacts import get_contacts  # Import the get_contacts function
from templates import get_templates  # Import the get_templates function
from dotenv import load_dotenv
import datetime
import time
import threading

def schedule_email(email_id, send_time, send_function, **kwargs):
    def email_task():
        try:
            while True:
                current_time = datetime.datetime.now()
                if current_time >= send_time:
                    send_function(**kwargs)  # Call the provided send function with the given arguments
                    logging.info(f"Scheduled email with ID {email_id} sent at {current_time}")
                    break
                time.sleep(10)  # Check every 10 seconds
        except Exception as e:
            logging.error(f"Error in scheduled email task: {e}")

    # Run the scheduling task in a separate thread
    threading.Thread(target=email_task, daemon=True).start()

# Load environment variables
load_dotenv()

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

logging.basicConfig(
    filename="cmail_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Function to validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    valid = re.match(pattern, email) is not None
    if not valid:
        logging.warning(f"Invalid email format: {email}")
    return re.match(pattern, email) is not None

# Function to send email via Outlook SMTP
def send_outlook_email(subject, message_text, recipient_list):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    smtp_user = os.getenv("OUTLOOK_USER")
    smtp_password = os.getenv("OUTLOOK_PASS")
    sender_email = smtp_user

    success_list = []
    failure_list = []

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()  # Secure the connection
            server.ehlo()
            server.login(smtp_user, smtp_password)

            for recipient_email in recipient_list:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(message_text, 'plain'))

                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    success_list.append(recipient_email)
                except Exception as e:
                    failure_list.append((recipient_email, str(e)))

    except Exception as e:
        logging.critical(f"Outlook SMTP connection failure - Error: {e}")
        return False

    return success_list, failure_list
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

def send_outlook_email(subject, message_text, recipient_list):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    smtp_user = os.getenv("OUTLOOK_USER")
    smtp_password = os.getenv("OUTLOOK_PASS")  # Load securely from environment variables
    sender_email = smtp_user

    success_list = []
    failure_list = []

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()  # Secure the connection
            server.ehlo()
            server.login(smtp_user, smtp_password)

            for recipient_email in recipient_list:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(message_text, 'plain'))

                    # Send the email
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    success_list.append(recipient_email)
                    logging.info(f"Email by Outlook sent successfully to: {recipient_email}")
                except Exception as e:
                    failure_list.append((recipient_email, str(e)))
                    logging.error(f"Failed to send email by Outlook to {recipient_email} - Error: {e}")
    except Exception as e:
        logging.critical(f"Outlook SMTP connection failure - Error: {e}")
        return [], [(recipient, str(e)) for recipient in recipient_list]

    return success_list, failure_list

# Updated outlook_page function
def outlook_page(display_sidebar):
    display_sidebar()

    st.header("Compose Mail using Outlook")

    if 'email_delivery_log' not in st.session_state:
        st.session_state.email_delivery_log = []

    user_email = st.session_state.get("user_email")
    contacts = get_contacts(user_email)
    contact_emails = [contact['email'] for contact in contacts]

    selected_contacts = st.multiselect("Select Contacts", options=contact_emails)

    if st.button("Send to All Contacts"):
        selected_contacts = contact_emails
        st.session_state.selected_contacts = selected_contacts
        st.success(f"All contacts selected: {', '.join(selected_contacts)}")
        logging.info(f"All contacts selected for email: {', '.join(selected_contacts)}")

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

    with st.form(key='outlook_form'):
        subject = st.text_input('Subject', value=subject)
        message_text = st.text_area('Message', value=message_text)
        recipient_email = st.text_input(
            'Recipient Email (For Multiple Recipients Enter Mail-IDs separated by comma)', 
            value=", ".join(st.session_state.get("selected_contacts", selected_contacts))
        )
        uploaded_file = st.file_uploader("Import CSV of Recipient Emails (must contain 'email' column)", type=['csv'])
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
        st.dataframe(pd.DataFrame(list(recipient_list), columns=["Email"]))

    if submit_button:
        if subject and message_text and recipient_list:
            if schedule_email_check and send_datetime:
                now = datetime.datetime.now()
                if send_datetime < now:
                    st.warning("The selected time is in the past. Please choose a time in the future.")
                else:
                    for recipient in recipient_list:
                        schedule_email(
                            email_id=f"{user_email}_{send_datetime.strftime('%Y%m%d%H%M%S')}_{recipient}",
                            send_time=send_datetime,
                            send_function=send_outlook_email,
                            subject=subject,
                            message_text=message_text,
                            recipient_list=[recipient]
                        )
                    st.success(f"Emails scheduled successfully for {send_datetime.strftime('%H:%M')}.")
                    save_email_log(user_email, recipient, "Scheduled", "Outlook", send_datetime, subject)
                    logging.info(f"Scheduled emails for {send_datetime.strftime('%H:%M')} to {', '.join(recipient_list)}.")
            else:
                success_list, failure_list = send_outlook_email(subject, message_text, recipient_list)
                for recipient in success_list:
                    save_email_log(user_email, recipient, "Sent", "Outlook", datetime.datetime.now(), subject)
                for recipient, error in failure_list:
                    save_email_log(user_email, recipient, "Failed", "Outlook", datetime.datetime.now(), subject, error)
                if success_list:
                    st.success(f"Emails sent successfully to: {', '.join(success_list)}")
                if failure_list:
                    st.error(f"Failed to send emails to: {', '.join([item[0] for item in failure_list])}")
        else:
            st.error("Subject, message, and at least one valid recipient email are required.")