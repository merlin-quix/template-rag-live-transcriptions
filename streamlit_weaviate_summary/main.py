import streamlit as st
import os
import pandas as pd
import weaviate
import time
import re
from datetime import datetime, timezone
from dateutil.parser import parse

# for local dev, load env vars from a .env file
from dotenv import load_dotenv
load_dotenv()

collectionname = os.getenv('COLLECTIONNAME')

st.set_page_config(
    page_title="Simple Live Transcription Summary",
    page_icon="🧊",
)

# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
        font-family: 'Arial', sans-serif;
    }
    .header {
        background-color: #005689;
        color: white;
        padding: 10px;
        text-align: center;
    }
    .entry {
        background-color: white;
        border: 1px solid #ddd;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .entry h3 {
        color: #005689 !important;
        font-weight: bold !important;  /* Make the header bold */
    }
    .entry p {
        margin: 5px 0 !important;
        color: #333 !important;  /* Darker text color */
    }
    .entry .speaker {
        font-weight: bold !important;
        color: #000 !important;  /* Darker text color */
    }
    .debug-info {
        color: #333;
        font-size: 14px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.image("https://images.squarespace-cdn.com/content/v1/64f1046c04dcd91aaa995dd3/f344ba5f-4440-4f82-953a-192f66f71976/title_header.png", caption="Simple Live Transcription Summary", use_column_width=True)
st.markdown('<p>A continuously updating summary of the ongoing discussion based on a live transcript.</p>', unsafe_allow_html=True)

# ADD DEBUG INFO
# st.markdown(f'<div class="debug-info">Using collection name: {collectionname}</div>', unsafe_allow_html=True)
print(f"Using collection name: {collectionname}")
# st.markdown(f'<div class="debug-info">Using URL: {os.getenv("WEAVIATE_REST_ENDPOINT")}</div>', unsafe_allow_html=True)
print(f"Using URL: {os.getenv('WEAVIATE_REST_ENDPOINT')}")

auth_config = weaviate.auth.AuthApiKey(api_key=os.getenv('WEAVIATE_APIKEY'))

client = weaviate.Client(
    url=os.getenv("WEAVIATE_REST_ENDPOINT"),  # URL of your Weaviate instance
    auth_client_secret=auth_config,  # (Optional) If the Weaviate instance requires authentication
    timeout_config=(5, 15),  # (Optional) Set connection timeout & read timeout time in seconds
    additional_headers={  # (Optional) Any additional headers; e.g. keys for API inference services
        "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY"),  # Replace with your OpenAI key
    }
)

class_name = collectionname

# Define the filter to get entries created after a certain time
where_filter = {
    "path": ["earliestTimestamp"],
    "operator": "GreaterThan",
    # Use either `valueDate` with a `RFC3339` datetime or `valueText` as Unix epoch milliseconds
    "valueDate": "2024-06-25T10:32:58Z"  # Example Unix epoch milliseconds
}

# Create the stop button
stop_button_placeholder = st.empty()
stop_button = stop_button_placeholder.button("Stop")

# Create a placeholder for the transcription summary
summary_placeholder = st.empty()

# Function to fetch and display data
def fetch_and_display_data():
    # Query the database
    response = (
        client.query
        .get(class_name, ["speaker", "segment", "summary", "earliestTimestamp"])
        .with_additional("creationTimeUnix")
        .with_where(where_filter)
        .do()
    )

    transcription_chunks = response['data']['Get'][class_name]

    try:
        if response['errors']:
            print(f"ERRORS: {response}")
    except:
        pass

    data = []

    for chunk in transcription_chunks:
        modified_segment = re.sub(r'\d{4}-\d{2}-\d{2}T', '', chunk['segment'])
        
        entry = {
            'speaker': chunk['speaker'],
            'segment': modified_segment,
            'summary': chunk['summary'],
            'timestamp': chunk['earliestTimestamp'],
        }
        data.append(entry)

    # Sort the data by timestamp in descending order
    data.sort(key=lambda x: parse(x['timestamp']), reverse=True)

    # Clear the placeholder and update it with the latest data
    with summary_placeholder.container():
        for entry in data:
            st.markdown('<div class="entry">', unsafe_allow_html=True)
            st.markdown(f'''<h5 style="color: #005689; font-weight: bold;"> • {entry["segment"]}</h3>''', unsafe_allow_html=True)
            summary_text = entry["summary"].replace("\n", "<br>")
            st.markdown(f'''<p style="color: #333;"><strong>SUMMARY:</strong><br><br> {summary_text}</p>''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# Loop until the stop button is clicked
while not stop_button:
    fetch_and_display_data()
    sleepsecs = 10
    # Sleep for a while before the next iteration
    print(f"Sleeping for {sleepsecs} seconds...")
    time.sleep(sleepsecs)
