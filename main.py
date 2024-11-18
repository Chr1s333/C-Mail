import streamlit as st

st.set_page_config(
    page_title="Cmail", 
    page_icon="📧",  
)
st.logo(image="Logo.png",size='large')

import pyrebase
import time
import logging
from requests.exceptions import HTTPError
import re
from streamlit_cookies_manager import EncryptedCookieManager  # For cookies
from dotenv import load_dotenv
import os
from gmail import gmail_page
from outlook import outlook_page
from dashboard import dashboard_page
from contacts import manage_contacts
from templates import manage_templates

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    filename="cmail_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_action(action, details=""):
    logging.info(f"{action} - {details}")
    
# Initialize the cookie manager
cookies = EncryptedCookieManager(
    prefix="cmail_",  # Optional prefix for the cookie
    password=os.getenv('COOKIE_MANAGER_PASSWORD')  # Set a secure password from environment variables
)

# Global variable to store email delivery log
email_delivery_log = []
# Wait for cookies to be ready
if not cookies.ready():
    st.stop()

# Firebase Configuration using environment variables
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

# Function to validate email format
def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Function to check if an email already exists
def check_if_email_exists(email):
    try:
        users = db.child("users").get().val()
        if users:
            for value in users.values():
                if value.get('email') == email:
                    return True  # Email already exists
    except HTTPError:
        st.error("Error fetching users.")
    return False  # Email does not exist

# Store the user's session state in cookies
def set_login_session(username, email):
    cookies["logged_in"] = "true"
    cookies["username"] = username
    cookies["email"] = email
    cookies.save()
    log_action("User Login", f"User {username} logged in with email {email}")

def clear_login_session():
    username = cookies.get("username", "Unknown")
    log_action("User Logout", f"User {username} logged out")
    cookies["logged_in"] = ""
    cookies["username"] = ""
    cookies["email"] = ""
    cookies.save()

def display_sidebar():
    # Check if user is logged in using cookies
    if cookies.get("logged_in") == "true":
        username = cookies.get("username")
        email = cookies.get("email")
        st.sidebar.header(f"Welcome, {username}!")

        # Provide buttons for Gmail, Outlook, etc.
        if st.sidebar.button("Compose Gmail"):
            st.session_state["page"] = "gmail_page"
            st.rerun()
        if st.sidebar.button("Compose Outlook"):
            st.session_state["page"] = "outlook_page"
            st.rerun()
        if st.sidebar.button("Dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        if st.sidebar.button("Manage Contacts"):
            st.session_state["page"] = "contacts"
            st.rerun()
        if st.sidebar.button("Manage Templates"):
            st.session_state["page"] = "templates"
            st.rerun()
        if st.sidebar.button("Logout"):
            clear_login_session()
            st.session_state["page"] = "login"
            st.rerun()
        
    else:
        st.write("You are not logged in. Please log in to access the services.")

# Function to display the Signup page
def signup():
    st.header('Welcome to Cmail - A Mass Mailing Application')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button('Signup', key='signup_button'):
            if email and password:
                # Log email entry
                logging.info(f"Attempted signup with email: {email}")

                # Validate email format
                if not is_valid_email(email):
                    st.error("Invalid email format.")
                    logging.warning("Signup failed - invalid email format.")
                    return

                # Check password length
                if len(password) < 6:
                    st.error("Password must be at least 6 characters long.")
                    logging.warning("Signup failed - password too short.")
                    return

                # Check if email already exists
                if check_if_email_exists(email):
                    st.error("Email already exists. Please continue with login.")
                    logging.warning(f"Signup failed - email already exists: {email}")
                else:
                    try:
                        # Attempt to create user
                        user = auth.create_user_with_email_and_password(email, password)
                        if user:
                            user_id = user['localId']
                            db.child("users").child(user_id).set({
                                "email": email,
                                "password": password
                            })
                            st.success("Account created successfully!")
                            st.balloons()
                            logging.info(f"Account created successfully for email: {email}")
                            
                            # Delay for effect and navigate to login page
                            time.sleep(2)
                            st.session_state["page"] = "login"
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create account: {str(e)}")
                        logging.error(f"Error during signup for {email}: {str(e)}")
            else:
                st.error("Please fill out all fields.")
                logging.warning("Signup failed - missing fields.")

    with col2:
        st.write("")  # Placeholder for alignment

    with col3:
        if st.button("Already have an account? Log in"):
            st.session_state["page"] = "login"
            st.rerun()

# Function to display the Login page
def login():
    st.header('Welcome to Cmail - A Mass Mailing Application')
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button('Login', key='login_button'):
            if email and password:
                # Log the login attempt
                logging.info(f"Login attempt with email: {email}")

                # Validate email format
                if not is_valid_email(email):
                    st.error("Invalid email format.")
                    logging.warning(f"Login failed - invalid email format for email: {email}")
                    return

                try:
                    # Attempt to sign in the user
                    auth.sign_in_with_email_and_password(email, password)
                    username = email.split('@')[0]
                    set_login_session(username, email)  # Store email and username

                    # Store login data in session state
                    st.session_state["user_email"] = email
                    st.session_state["page"] = "welcome"
                    
                    # Log successful login
                    logging.info(f"Login successful for email: {email}")
                    st.rerun()
                except Exception as e:
                    # Specific error handling for login credentials
                    if "INVALID_LOGIN_CREDENTIALS" in str(e):
                        st.error("Invalid email or password.")
                        logging.warning(f"Invalid login credentials for email: {email}")
                    else:
                        st.error(f"Error logging in: {str(e)}")
                        logging.error(f"Unexpected error during login for {email}: {str(e)}")
            else:
                st.error("Please enter both email and password.")
                logging.warning("Login failed - missing email or password fields.")
                
    with col2:
        st.write("")  # Placeholder for alignment

    with col3:
        if st.button("Don't have an account? Create now"):
            st.session_state["page"] = "signup"
            st.rerun()

# Function to display the Welcome page
def welcome():
    st.header("Welcome!")

    if cookies.get("logged_in") == "true":

        st.write("Compose a mail using:")
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Compose Mail using Gmail"):
                st.session_state["page"] = "gmail_page"
                st.rerun()

        with col2:
            if st.button("Compose Mail using Outlook"):
                st.session_state["page"] = "outlook_page"
                st.rerun()

        display_sidebar()

    else:
        st.write("You are not logged in. Please log in to access the services.")

# Main function to manage page transitions
def main():
    # Ensure session state is initialized
    if "page" not in st.session_state:
        st.session_state["page"] = "login" if cookies.get("logged_in") != "true" else "welcome"

    # Check if the user is logged in via cookies
    if cookies.get("logged_in") == "true":
        # Set the session state based on cookies
        st.session_state["user_email"] = cookies.get("email")
        st.session_state["username"] = cookies.get("username")

    # Show appropriate page
    if st.session_state["page"] == "login":
        login()
    elif st.session_state["page"] == "signup":
        signup()
    elif st.session_state["page"] == "welcome":
        welcome()
    elif st.session_state["page"] == "gmail_page":
        gmail_page(display_sidebar)
    elif st.session_state["page"] == "outlook_page":
        outlook_page(display_sidebar)
    elif st.session_state["page"] == "dashboard":
        dashboard_page(display_sidebar)
    elif st.session_state["page"] == "contacts":
        manage_contacts(display_sidebar)
    elif st.session_state["page"] == "templates":
        manage_templates(display_sidebar)

if __name__ == "__main__":
    main()