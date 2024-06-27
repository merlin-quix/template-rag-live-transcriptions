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

st.image("data:image/png;base64,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g", caption="Simple Live Transcription Summary", use_column_width=True)
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
