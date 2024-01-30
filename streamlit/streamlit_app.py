import streamlit as st
import serial
import threading
import pandas as pd
import logging
from datetime import datetime
from collections import deque

# Initialize logging
logging.basicConfig(
    filename="streamlit_app.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize global variables
data = deque()


def connect_serial(port, baud_rate, timeout, queue_length):
    global ser, data
    try:
        logging.debug(f"Connecting to Serial Port: {port} at {baud_rate} baud.")
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        data = deque(maxlen=queue_length)
        logging.info(f"Connected to Serial Port: {port} at {baud_rate} baud.")
        st.session_state.ser = ser
        st.success("Connected to Serial Port.")
        return True
    except serial.SerialException as e:
        logging.error(f"Serial connection error: {e}")
        st.error("Failed to connect to Serial Port.")
        return False


def read_initial_details():
    logging.debug("Reading initial connection details.")
    connection_details = []
    try:
        for _ in range(25):  # Read the first 25 lines for debugging
            line = (
                st.session_state.ser.readline().decode("utf-8", errors="ignore").strip()
            )
            logging.debug(f"Serial line: {line}")
            connection_details.append(line)
        logging.info("Initial 25 lines from Serial Port: " + str(connection_details))
        # Assuming the header is in one of these lines; adjust as necessary
        for line in connection_details:
            if "rtcDate" in line:
                logging.info(f"Header: {line}")
                header = line.split(",")
                return header
        return []
    except Exception as e:
        logging.error(f"Error reading initial details: {e}")
        return []


def read_data():
    logging.debug("Starting read_data()")
    while not st.session_state.stop_threads:
        line = st.session_state.ser.readline().decode("utf-8", errors="ignore").strip()
        if line:
            yield line


def display_data(selected_column):
    global data
    chart_data = pd.DataFrame(columns=["DateTime", selected_column])
    chart = st.line_chart(chart_data)
    for line in read_data():
        if "rtcDate" not in line:  # Ignore header
            values = line.split(",")
            datetime_str = (
                values[0] + " " + values[1].split(".")[0]
            )  # Split and remove milliseconds
            try:
                datetime_obj = datetime.strptime(datetime_str, "%m/%d/%Y %H:%M:%S")
                new_data = pd.DataFrame(
                    {
                        "DateTime": [datetime_obj],
                        selected_column: [float(values[header.index(selected_column)])],
                    }
                )
                chart_data = chart_data.append(new_data, ignore_index=True)
                chart_data = chart_data.tail(
                    data.maxlen
                )  # Keep only the latest data according to queue length
                chart.add_rows(new_data)
            except ValueError as e:
                logging.error(f"Error parsing datetime: {e}")


# Initialize session state variables
if "ser" not in st.session_state:
    st.session_state.ser = None
if "stop_threads" not in st.session_state:
    st.session_state.stop_threads = False
if "thread" not in st.session_state:
    st.session_state.thread = None

# Streamlit UI
st.title("Serial Port Data Streaming")

# Serial connection settings
port = st.sidebar.text_input("Serial Port", "/dev/tty.usbserial-330")
baud_rate = st.sidebar.number_input("Baud Rate", value=115200)
timeout = st.sidebar.number_input("Timeout", value=1)
queue_length = st.sidebar.number_input("Queue Length", value=1000, min_value=10)

# Connect button
if st.sidebar.button("Connect"):
    if connect_serial(port, baud_rate, timeout, queue_length):
        st.session_state.stop_threads = False
        header = read_initial_details()  # Get header
        if header:
            st.session_state.thread = threading.Thread(target=read_data)
            st.session_state.thread.start()
            st.sidebar.success("Reading data...")
            st.session_state.header = header  # Store header in session state
        else:
            st.error("Failed to read header from serial port.")

# Select column to chart
if "header" in st.session_state and st.session_state.header:
    selected_column = st.sidebar.selectbox(
        "Select Column to Chart",
        st.session_state.header[2:],  # Exclude date and time columns
    )
    # Start displaying data
    if selected_column:
        display_data(selected_column)

# Disconnect button
if st.sidebar.button("Disconnect"):
    st.session_state.stop_threads = True
    if st.session_state.thread and st.session_state.thread.is_alive():
        st.session_state.thread.join()
    if st.session_state.ser:
        st.session_state.ser.close()
        logging.info(f"Disconnected from Serial Port: {port}")
        st.sidebar.success("Disconnected.")
