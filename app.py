import streamlit as st
import plotly.express as px
from flask import Flask, request, jsonify
from threading import Thread, Event
import time

DATA = None

# Initialize Flask app
app = Flask(__name__)

data_ready = Event()

# Flask route to receive data
@app.route('/receive_data', methods=['POST'])
def receive_data():
    global DATA
    DATA = request.get_json()
    print("Received data:", DATA)
    data_ready.set()
    return jsonify({"status": "success"}), 200

# Function to run Flask server
def run_flask():
    app.run(host='0.0.0.0', port=8502)

# Start Flask server in a separate thread
if 'data' not in st.session_state:
    time.sleep(10)

thread = Thread(target=run_flask)
thread.start()

data_ready.wait()

# Streamlit page configuration
st.set_page_config(
    page_title="Politic Cube", 
    page_icon="🧊", 
    layout="wide"
)

st.session_state['data'] = DATA

# Streamlit UI
st.title("Politic Cube")
st.header("Stay updated with the latest political news from Sri Lanka")

# Plotly pie chart for candidate expected vote percentage
st.subheader("Candidate Expected Vote Percentage")
st.write("This pie chart shows the expected vote percentage for each candidate in the upcoming election.")

# Function to update the pie chart
def update_chart():
    data = st.session_state['data']
    labels = list(data.keys())
    values = [round(val * 100, 2) for val in list(data.values())]
    fig = px.pie(values=values, names=labels, title='Candidate Expected Vote Percentage')
    st.plotly_chart(fig)

# run once every 30 secs
while True:
    update_chart()
    time.sleep(30)
