import streamlit as st
import pandas as pd
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
def is_valid_email(email):
    # Simple regex pattern for validating an email address
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None
# Function to send email via Outlook SMTP
def send_outlook_email(subject, message_text, recipient_list):
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    smtp_user = os.getenv("OUTLOOK_USER")
    smtp_password = os.getenv("OUTLOOK_PASS")  # Load password securely from environment variables
    sender_email = smtp_user

    success_list = []
    failure_list = []

    # Try connecting to the SMTP server and sending emails
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
                    st.session_state.email_delivery_log.append({"Email": recipient_email, "Status": "Sent", "Service": "Outlook"})
                except Exception as e:
                    failure_list.append((recipient_email, str(e)))
                    st.session_state.email_delivery_log.append({"Email": recipient_email, "Status": "Failed", "Service": "Outlook", "Error": str(e)})

    except Exception as e:
        st.error(f"Failed to connect to Outlook SMTP server: {e}")
        return False

    return success_list, failure_list

# Outlook Page Function with CSV import and table for recipient emails
def outlook_page(display_sidebar):
    # Display the sidebar
    display_sidebar()

    st.header("Compose Mail using Outlook")

    # Initialize email delivery log in session state if it doesn't exist
    if 'email_delivery_log' not in st.session_state:
        st.session_state.email_delivery_log = []

    # Form to collect email data
    with st.form(key='outlook_form'):
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
            success_list, failure_list = send_outlook_email(subject, message_text, recipient_list)

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
