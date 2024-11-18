import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
import pyrebase
load_dotenv()

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

# Save email delivery log to Firebase
def save_email_log_to_firebase(user_email, log_entry):
    sanitized_email = sanitize_email(user_email)
    try:
        db.child("email_delivery_logs").child(sanitized_email).push(log_entry)
    except Exception as e:
        st.error(f"Error saving log to Firebase: {e}")

# Retrieve email delivery logs from Firebase
def get_email_logs(user_email):
    sanitized_user_email = sanitize_email(user_email)  # Sanitize the email
    
    # Fetch logs for the sanitized user email
    logs = db.child("email_logs").child(sanitized_user_email).get()
    
    if logs.each():
        return [
            {
                "recipient": log.val()["recipient"],
                "status": log.val()["status"],
                "Timestamp": log.val()["Timestamp"],
                "service": log.val()["service"],
                "error": log.val().get("error")
            }
            for log in logs.each()
        ]
    else:
        return []  # Return empty list if no logs are found

# Enhanced Dashboard Page Function
def dashboard_page(display_sidebar):
    # Display the sidebar
    display_sidebar()

    st.header("Email Delivery Dashboard")

    # Get user email from session
    user_email = st.session_state.get("user_email")

    if user_email is None:
        st.error("User email not found. Please log in.")
        return  # Exit if user email is not found

    # Retrieve email delivery logs from Firebase
    email_delivery_log = get_email_logs(user_email)

    # Check if there are any logs to display
    if email_delivery_log:
        delivery_log_df = pd.DataFrame(email_delivery_log)

        if not delivery_log_df.empty:
            # Convert 'Timestamp' column to datetime if it exists
            if 'Timestamp' in delivery_log_df.columns:
                try:
                    delivery_log_df['Timestamp'] = pd.to_datetime(delivery_log_df['Timestamp'])
                    delivery_log_df['Date'] = delivery_log_df['Timestamp'].dt.date
                    delivery_log_df['Hour'] = delivery_log_df['Timestamp'].dt.hour
                except Exception as e:
                    st.warning(f"Error parsing timestamps: {e}")

            # Date range filter
            st.subheader("Filter by Date Range")
            min_date = delivery_log_df['Date'].min()
            max_date = delivery_log_df['Date'].max()
            start_date, end_date = st.date_input(
                "Select Date Range",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )

            # Apply date range filter
            filtered_log_df = delivery_log_df[
                (delivery_log_df['Date'] >= start_date) & (delivery_log_df['Date'] <= end_date)
            ]

            # Status filter
            unique_statuses = filtered_log_df['status'].unique().tolist()
            selected_statuses = st.multiselect("Select Status to Filter", options=unique_statuses, default=unique_statuses)
            filtered_log_df = filtered_log_df[filtered_log_df['status'].isin(selected_statuses)]

            # Reset filter button
            if st.button("Reset Filters"):
                filtered_log_df = delivery_log_df

            # Display metrics in columns for better layout
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Emails Sent", len(filtered_log_df))
            with col2:
                success_count = len(filtered_log_df[filtered_log_df['status'] == 'Sent'])
                st.metric("Total Successful Deliveries", success_count, delta=success_count / len(filtered_log_df) * 100 if len(filtered_log_df) > 0 else 0)
            with col3:
                failed_count = len(filtered_log_df[filtered_log_df['status'] == 'Failed'])
                st.metric("Total Failed Deliveries", failed_count, delta=-failed_count / len(filtered_log_df) * 100 if len(filtered_log_df) > 0 else 0)

             # Display the filtered log in an interactive table with styling
            st.dataframe(
                filtered_log_df.style.set_properties(**{'text-align': 'center'}).map(
                    lambda x: 'background-color: #f99;' if x == 'Failed' else 'background-color: #9f9;', subset=['status']
                )
            )

            # Display bar chart for statuses
            status_counts = filtered_log_df['status'].value_counts()
            st.subheader("Email Delivery Status Overview")
            st.bar_chart(status_counts)

            # Display Service-wise Email Distribution
            st.subheader("Service-wise Email Distribution")
            service_counts = filtered_log_df['service'].value_counts()
            st.bar_chart(service_counts)

            # Display Hourly Email Trendsr
            if 'Hour' in filtered_log_df.columns:
                st.subheader("Hourly Email Trends")
                hourly_counts = filtered_log_df.groupby('Hour')['status'].value_counts().unstack().fillna(0)
                st.line_chart(hourly_counts)

            # Display Daily Trends if timestamp data is available
            if 'Date' in filtered_log_df.columns:
                st.subheader("Daily Email Trends")
                daily_counts = filtered_log_df.groupby('Date')['status'].value_counts().unstack().fillna(0)
                st.line_chart(daily_counts)

        else:
            st.info("No emails have been sent yet. Start sending emails to view delivery data here.")
    else:
        st.info("No emails have been sent yet. Start sending emails to view delivery data here.")

