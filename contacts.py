import pyrebase
from dotenv import load_dotenv  # Import dotenv to load environment variables
import os  # Import os to access environment variables
# Load environment variables from .env file
load_dotenv()
# Initialize Firebase (this is just a snippet, make sure your config is correct)
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

# Function to add a contact
def add_contact(user_email, contact_name, contact_email):
    sanitized_email = sanitize_email(user_email)
    try:
        # Create a unique identifier for the contact
        contact_id = db.child("contacts").child(sanitized_email).push({
            "name": contact_name,
            "email": contact_email
        })
        print(f"Contact added successfully with ID: {contact_id}")
    except Exception as e:
        print(f"Error adding contact: {e}")

# Example usage
user_email = "chris@gmail.com"
contact_name = "John Doe"
contact_email = "johndoe@example.com"

add_contact(user_email, contact_name, contact_email)
