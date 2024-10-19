import streamlit as st
import pandas as pd

# Dashboard Page Function
def dashboard_page(display_sidebar):
    # Display the sidebar
    display_sidebar()

    st.header("Email Delivery Dashboard")

    # Check if the email delivery log exists in session state
    if 'email_delivery_log' in st.session_state:
        delivery_log_df = pd.DataFrame(st.session_state.email_delivery_log)

        if not delivery_log_df.empty:
            # Filter options for statuses
            unique_statuses = delivery_log_df['Status'].unique().tolist()
            selected_statuses = st.multiselect("Select Status to Filter", options=unique_statuses, default=unique_statuses)

            # Filter the DataFrame based on selected statuses
            filtered_log_df = delivery_log_df[delivery_log_df['Status'].isin(selected_statuses)]

            # Display metrics
            st.metric("Total Emails Sent", len(filtered_log_df), delta=len(filtered_log_df[filtered_log_df['Status'] == 'Sent']))
            st.metric("Total Successful Deliveries", len(filtered_log_df[filtered_log_df['Status'] == 'Sent']))
            st.metric("Total Failed Deliveries", len(filtered_log_df[filtered_log_df['Status'] == 'Failed']))

            # Display the filtered log in an interactive table
            st.dataframe(filtered_log_df.style.set_properties(**{'text-align': 'center'}))

            # Display charts for visual insights
            status_counts = filtered_log_df['Status'].value_counts()
            st.write("Bar Chart")
            st.bar_chart(status_counts)

            # If you'd like to see delivery status over time (requires a 'Timestamp' column in log)
            if 'Timestamp' in delivery_log_df.columns:
                delivery_log_df['Date'] = pd.to_datetime(delivery_log_df['Timestamp']).dt.date
                daily_counts = delivery_log_df.groupby('Date')['Status'].value_counts().unstack().fillna(0)
                st.write("Line Chart")
                st.line_chart(daily_counts)

        else:
            st.write("No emails sent yet.")
    else:
        st.write("No emails sent yet.")

