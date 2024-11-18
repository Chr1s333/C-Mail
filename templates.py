import pyrebase
from dotenv import load_dotenv
import os
import streamlit as st
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(
    filename="cmail_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Firebase Configuration
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
db = firebase.database()

# Helper function to sanitize email
def sanitize_email(email):
    return email.replace('@', '_at_').replace('.', '_dot_')

# Function to load default templates with subjects for a new user
def load_default_templates(user_email):
    messages = []
    for template_name, (template_content, subject) in default_templates.items():
        message = add_template(user_email, template_name, template_content, subject)
        messages.append(message)
        logging.info("Default templates Loaded")
    return messages

# Sample predefined templates with subjects
default_templates = {
    "Basic Email Template": (
        "Dear [Recipient's Name],\n\n"
        "I hope this message finds you well. "
        "[Your main content goes here. This could be an update, a request, or any information you wish to share with the recipient. Keep it concise and to the point.] "
        "Thank you for your time, and I look forward to your response.\n\n"
        "Best regards,\n"
        "[Your Name]\n"
        "[Your Position]\n"
        "[Your Contact Information]\n"
        "[Your Company/Organization Name]",
        "[Your Subject Here]"
    ),

    "HTML Email Template": (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        "    <title>Your Subject Here</title>\n"
        "</head>\n"
        "<body>\n"
        "    <h2>Your Subject Here</h2>\n"
        "    <p>Dear [Recipient's Name],</p>\n"
        "    <p>[Your main content goes here.]</p>\n"
        "    <p>Best,<br>[Your Name]</p>\n"
        "</body>\n"
        "</html>",
        "HTML Template Subject"
    ),

    "Email with Attachment": (
        "Dear [Name],\n\n"
        "I hope this message finds you well. "
        "Please find the attached file regarding [brief description of the attachment, e.g., \"the project update,\" \"the invoice,\" etc.]. "
        "If you have any questions or need further information, feel free to reach out.\n\n"
        "Thank you!\n"
        "Best regards,\n"
        "[Your Name]",
        "Attachment Email Subject"
    ),

    "Personalized Email Template": (
        "Dear [Name],\n\n"
        "Thank you for being a valued customer. We appreciate your support and loyalty. "
        "As a token of our gratitude, we would like to offer you [brief description of the offer or special deal]. "
        "Please let us know if there's anything else we can assist you with.\n\n"
        "Best wishes,\n"
        "[Your Name]\n"
        "[Your Position]\n"
        "[Your Company/Organization Name]",
        "Personalized Email Subject"
    )
}
def add_template(user_email, template_name, template_content, subject):
    sanitized_email = sanitize_email(user_email)
    try:
        db.child("templates").child(sanitized_email).push({
            "name": template_name,
            "content": template_content,
            "subject": subject
        })
        logging.info(f" \"{template_name}\" Template added successfully")
        return f" \"{template_name}\" Template added successfully"

    except Exception as e:
        logging.error(f"Error adding template for {user_email}: {e}")
        return f"Error adding template: {e}"

# Function to retrieve templates including subject
def get_templates(user_email):
    sanitized_email = sanitize_email(user_email)
    try:
        templates = db.child("templates").child(sanitized_email).get().val()
        return templates if templates else {}
    except Exception as e:
        st.error(f"Error fetching templates: {e}")
        logging.error(f"Error fetching templates for {user_email}: {e}")
        return {}

# Function to update a template
def update_template(user_email, template_id, new_content, new_subject):
    sanitized_email = sanitize_email(user_email)
    try:
        db.child("templates").child(sanitized_email).child(template_id).update({
            "content": new_content,
            "subject": new_subject
        })
        logging.info(f"Template {template_id} updated successfully")
        return "Template updated successfully"
    except Exception as e:
        logging.error(f"Error updating template with ID {template_id} for {user_email}: {e}")
        return f"Error updating template: {e}"

# Function to delete a template
def delete_template(user_email, template_id):
    sanitized_email = sanitize_email(user_email)
    try:
        db.child("templates").child(sanitized_email).child(template_id).remove()
        logging.warning(f"Template {template_id} Deleted successfully")
        return "Template deleted successfully"
    except Exception as e:
        logging.error(f"Error deleting template with ID {template_id} for {user_email}: {e}")
        return f"Error deleting template: {e}"

# Streamlit interface for managing templates
def manage_templates(display_sidebar):
    display_sidebar()
    st.header("Manage Templates")
    user_email = st.session_state.get("user_email")

    if user_email is None:
        st.error("User email not found. Please log in.")
        return

    st.subheader("Your Templates")
    templates = get_templates(user_email)
    
    if templates:
        for template_id, template in templates.items():
            with st.expander(f"{template['name']} (Subject: {template['subject']})"):
                new_name = st.text_input("Edit Template Name", value=template["name"], key=f"edit_name_{template_id}")
                new_content = st.text_area("Edit Content", value=template["content"], key=f"edit_content_{template_id}")
                new_subject = st.text_input("Edit Subject", value=template["subject"], key=f"edit_subject_{template_id}")

                if st.button("Update Template", key=f"update_{template_id}"):
                    if new_name and new_content and new_subject:
                        update_message = update_template(user_email, template_id, new_content, new_subject)
                        st.success(update_message)
                    else:
                        st.warning("Please enter all fields to update.")

                if st.button("Delete Template", key=f"delete_{template_id}"):
                    delete_message = delete_template(user_email, template_id)
                    st.warning(delete_message)
    else:
        st.write("No templates found.")

    with st.form(key='add_template_form'):
        template_name = st.text_input("Template Name")
        template_content = st.text_area("Template Content")
        subject = st.text_input("Template Subject")
        submit_button = st.form_submit_button(label='Add Template')

        if submit_button:
            if template_name and template_content and subject:
                add_message = add_template(user_email, template_name, template_content, subject)
                st.success(add_message)
            else:
                st.error("Please fill out all fields.")
    # Load default templates button
    if st.button("Load Default Templates", key="load_default_templates"):
        load_messages = load_default_templates(user_email)
        for message in load_messages:
            st.success(message)
