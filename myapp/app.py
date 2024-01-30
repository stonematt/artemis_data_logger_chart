# app.py
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from artemis_reader import ArtemisReader
from serial import Serial
from serial.threaded import ReaderThread
from flask_cors import CORS


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

header_data = None


# Initialize Flask and SocketIO
app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# Define selected columns for data emission
selected_columns = ["your", "columns"]  # Update with actual column names


def update_header(header):
    global header_data
    header_data = header


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


# SocketIO events
@socketio.on("connect")
def handle_connect():
    logging.info("Connect")
    if header_data:
        emit("header_data", header_data)


# SocketIO event to update selected columns
@socketio.on("update_selected_columns")
def handle_column_update(columns):
    global reader
    reader.selected_columns = columns
    logging.info(f"Updated selected columns: {reader.selected_columns}")
    emit("columns_updated", {"columns": reader.selected_columns})  # Notify clients


if __name__ == "__main__":
    # Initialize ArtemisReader and Serial with the specified port
    reader = ArtemisReader(socketio=socketio, selected_columns=[])

    ser = Serial("/dev/tty.usbserial-330", 115200, timeout=None)

    with ReaderThread(
        ser, lambda: ArtemisReader(socketio=socketio, selected_columns=[])
    ) as protocol:
        # with ReaderThread(ser, reader) as protocol:
        # Handle data received through ArtemisReader callback
        socketio.run(app, debug=True)
