import logging
from flask import Flask, render_template
from flask_socketio import SocketIO
from artemis_reader import ArtemisReader
from serial import Serial
from serial.threaded import ReaderThread

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config.from_pyfile("config.py")  # Load configuration from config.py
socketio = SocketIO(app)


@app.route("/")
def index():
    return render_template("index.html")


def start_serial_communication():
    logging.info("Attempting to connect to serial port")
    try:
        logging.debug(
            f"Starting ser on {app.config["SERIAL_PORT"]}@{app.config["BAUD_RATE"]}")
        ser = Serial(app.config["SERIAL_PORT"], app.config["BAUD_RATE"], timeout=1)
        logging.debug(
            f"Starting reader on {app.config["SERIAL_PORT"]}@{app.config["BAUD_RATE"]}")
        reader = ArtemisReader(
            socketio, [], app.config["SERIAL_PORT"], app.config["BAUD_RATE"]
        )
        with ReaderThread(ser, lambda: reader) as protocol:
            pass  # Keep the thread running
    except Exception as e:
        logging.error(f"Error in serial communication: {e}")


if __name__ == "__main__":
    logging.info("Starting Flask app with SocketIO")
    socketio.start_background_task(start_serial_communication)
    socketio.run(app)
