import re
import pyrebase
import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import logging

# Load environment variables from .env file
load_dotenv()
logging.basicConfig(
    filename="cmail_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Initialize Firebase configuration
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

# Function to sanitize email format
def sanitize_email(email):
    return email.replace('@', '_at_').replace('.', '_dot_')

# Contact management functions
def is_valid_email(email):
    # Regex pattern for validating email
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Function to add a contact for the logged-in user
def add_contact(contact_name, contact_email):
    if not is_valid_email(contact_email):
        st.error("Invalid email format. Please enter a valid email address.")
        return  # Stop if email is invalid

    if "user_email" in st.session_state:
        logged_in_email = st.session_state["user_email"]
        sanitized_email = sanitize_email(logged_in_email)
        try:
            # Add the contact under the logged-in user's sanitized email
            db.child("contacts").child(sanitized_email).push({
                "name": contact_name,
                "email": contact_email
            })
            st.success(f"Contact '{contact_name}' added successfully!")
            logging.info(f"Added contact: {contact_name} for user {logged_in_email}")
        except Exception as e:
            st.error(f"Error adding contact: {e}")
            logging.error(f"Error adding contact for user {logged_in_email}: {e}")
    else:
        st.error("No user logged in. Please log in to add contacts.")
        logging.warning("Attempt to add contact without logged-in user.")

# Function to retrieve contacts for the logged-in user
def get_contacts(user_email=None):
    contacts = []
    if user_email is None and "user_email" in st.session_state:
        user_email = st.session_state["user_email"]

    if user_email:
        sanitized_email = sanitize_email(user_email)
        try:
            contacts_data = db.child("contacts").child(sanitized_email).get().val()
            if contacts_data:
                for key, value in contacts_data.items():
                    contacts.append({"id": key, "name": value.get("name"), "email": value.get("email")})
            else:
                st.info("No contacts found.")
                logging.info("No contacts found for user.")
        except Exception as e:
            st.error(f"Error retrieving contacts: {e}")
            logging.error(f"Error retrieving contacts for user {user_email}: {e}")
    else:
        st.error("No user logged in. Please log in to view contacts.")
        logging.warning("Attempt to retrieve contacts without logged-in user.")
    return contacts

# Function to update a specific contact
def update_contact(contact_id, new_name, new_email):
    if not is_valid_email(new_email):
        st.error("Invalid email format. Please enter a valid email address.")
        return  # Stop if email is invalid

    if "user_email" in st.session_state:
        logged_in_email = st.session_state["user_email"]
        sanitized_email = sanitize_email(logged_in_email)
        try:
            db.child("contacts").child(sanitized_email).child(contact_id).update({
                "name": new_name,
                "email": new_email
            })
            st.success("Contact updated successfully!")
            logging.info(f"Updated contact {contact_id} for user {logged_in_email}")
        except Exception as e:
            st.error(f"Error updating contact: {e}")
            logging.error(f"Error updating contact {contact_id} for user {logged_in_email}: {e}")
    else:
        st.error("No user logged in. Please log in to update contacts.")
        logging.warning("Attempt to update contact without logged-in user.")

# Function to delete a specific contact
def delete_contact(contact_id):
    if "user_email" in st.session_state:
        logged_in_email = st.session_state["user_email"]
        sanitized_email = sanitize_email(logged_in_email)
        try:
            db.child("contacts").child(sanitized_email).child(contact_id).remove()
            st.success("Contact deleted successfully!")
            logging.warning(f"Deleted contact {contact_id} for user {logged_in_email}")
        except Exception as e:
            st.error(f"Error deleting contact: {e}")
            logging.error(f"Error deleting contact {contact_id} for user {logged_in_email}: {e}")
    else:
        st.error("No user logged in. Please log in to delete contacts.")
        logging.warning("Attempt to delete contact without logged-in user.")

def delete_all_contacts():
    if "user_email" in st.session_state:
        logged_in_email = st.session_state["user_email"]
        sanitized_email = sanitize_email(logged_in_email)
        try:
            db.child("contacts").child(sanitized_email).remove()
            st.success("All contacts deleted successfully!")
            logging.warning(f"Deleted all contacts for user {logged_in_email}")
        except Exception as e:
            st.error(f"Error deleting all contacts: {e}")
            logging.error(f"Error deleting all contacts for user {logged_in_email}: {e}")
    else:
        st.error("No user logged in. Please log in to delete contacts.")
        logging.warning("Attempt to delete all contacts without logged-in user.")

# Streamlit interface for managing contacts
def manage_contacts(display_sidebar):
    display_sidebar()
    st.title("Manage Contacts")

    # Container for adding a new contact
    with st.container():
        st.subheader("Add a New Contact")
        contact_name = st.text_input("Contact Name")
        contact_email = st.text_input("Contact Email")
        if st.button("Add Contact"):
            if contact_name and contact_email:
                add_contact(contact_name, contact_email)
            else:
                st.warning("Please enter both name and email to add a contact.")

    # Container for uploading contacts from CSV
    with st.container():
        st.subheader("Add Contacts from CSV File")
        uploaded_file = st.file_uploader("Upload a CSV file with 'Name' and 'Email' columns", type="csv")
        if uploaded_file:
            try:
                csv_data = pd.read_csv(uploaded_file)
                
                if 'Name' in csv_data.columns and 'Email' in csv_data.columns:
                    for index, row in csv_data.iterrows():
                        if is_valid_email(row['Email']):
                            add_contact(row['Name'], row['Email'])
                        else:
                            st.warning(f"Invalid email at row {index + 1}: {row['Email']}")
                    
                    st.success("All valid contacts from CSV have been added successfully!")
                    logging.info("Contacts added from CSV for user.")
                else:
                    st.error("CSV must contain 'Name' and 'Email' columns.")
                    logging.error("CSV missing required columns.")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                logging.error(f"Error reading CSV file: {e}")

    # Container for displaying existing contacts with edit and delete options
    with st.container():
        st.subheader("Your Contacts")
        contacts = get_contacts()
        if contacts:
            for contact in contacts:
                with st.expander(f"{contact['name']} ({contact['email']})"):
                    new_name = st.text_input("Edit Name", value=contact["name"], key=f"edit_name_{contact['id']}")
                    new_email = st.text_input("Edit Email", value=contact["email"], key=f"edit_email_{contact['id']}")

                    if st.button("Update Contact", key=f"update_{contact['id']}"):
                        if new_name and new_email:
                            update_contact(contact["id"], new_name, new_email)
                        else:
                            st.warning("Please enter both name and email to update.")

                    if st.button("Delete Contact", key=f"delete_{contact['id']}"):
                        delete_contact(contact["id"])

    st.write("---")
    if st.button("Delete All Contacts"):
        delete_all_contacts()