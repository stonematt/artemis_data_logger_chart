import logging
import serial.threaded


class ArtemisReader(serial.threaded.Protocol):
    """
    Protocol class for reading and processing data from the Artemis Data Logger.

    Attributes:
        socketio (SocketIO): Instance for data emission via SocketIO.
        selected_columns (list): List of column names to emit.
        indices (dict): Maps column names to their indices.
        header_found (bool): Flag to check if header line has been processed.
        buffer (str): Accumulates incoming data.
        full_header (list): Stores the complete header line.
    """

    def __init__(self, socketio, selected_columns):
        """
        Initializes ArtemisReader with a SocketIO instance and selected columns.

        :param socketio: Instance for data emission via SocketIO.
        :param selected_columns: List of column names to emit.
        """
        logging.info("Initializing ArtemisReader...")
        self.socketio = socketio
        self.selected_columns = selected_columns
        self.indices = None
        self.header_found = False
        self.buffer = ""
        self.full_header = []

    def data_received(self, data):
        """
        Handles incoming data, appending to buffer and processing complete lines.

        :param data: The incoming data bytes.
        """
        try:
            self.buffer += data.decode()  # Append new data to buffer
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                self._process_line(line.strip())  # Process the complete line
        except serial.SerialException as e:
            logging.error(f"SerialException: {e}")

    def _process_line(self, line_str):
        """
        Processes a line of data. Logs lines until header is found,
        updates header if found again.

        :param line_str: A single line of data.
        """
        if not self.header_found:
            logging.info(f"Read line: {line_str}")
            if "rtcDate" in line_str:
                self._process_header(line_str)
                self.header_found = True
        else:
            if "rtcDate" in line_str:
                self._process_header(line_str)
            else:
                self._parse_and_emit(line_str)

    def _process_header(self, header_line):
        """
        Processes the header line and emits it to the client.

        :param header_line: The header line of the data.
        """
        self.full_header = header_line.split(",")  # Update full header
        self.indices = {name: i for i, name in enumerate(self.full_header)}
        logging.info(f"Header updated: {self.full_header}")
        self.socketio.emit("header_data", self.full_header)

    def _parse_and_emit(self, line_str):
        """
        Parses a data line and emits selected data.

        :param line_str: A single line of data.
        """
        data = line_str.split(",")
        if len(data) != len(self.full_header):
            logging.warning(f"Data line does not match header format: {line_str}")
            return

        selected_data = {
            self.full_header[i]: data[i]
            for i in range(len(data))
            if i < len(self.full_header)
            and self.full_header[i] in self.selected_columns
        }
        self.socketio.emit("serial_data", selected_data)
        # self.socketio.emit("serial_data", data)
