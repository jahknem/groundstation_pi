import serial
from threading import Thread, Lock
import time
import logging

class UARTCommunication:
    """
    Handles UART communication with the microcontroller.
    """
    def __init__(self):
        self.port = None
        self.baudrate = None
        self.timeout = None
        self.ser = None
        self.lock = Lock()
        self.read_thread = None
        self.buffer = bytearray()
        self.connected = False

    def configure(self, port: str, baudrate: int = 115200, timeout: float = 1):
        """
        Configures and opens the UART port.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            self.connected = True
            logging.info(f"UART port {self.port} opened successfully.")
            # Start the read thread
            self.read_thread = Thread(target=self.read_from_uart, daemon=True)
            self.read_thread.start()
        except serial.SerialException as e:
            self.connected = False
            logging.error(f"Failed to open UART port {self.port}: {e}")

    def is_connected(self):
        """
        Checks if the UART port is connected.
        """
        return self.connected

    def send_command(self, command_id: int, payload: bytes) -> None:
        """
        Constructs and sends a command to the microcontroller.
        """
        if not self.is_connected():
            raise serial.SerialException("UART port is not connected.")
        command = self.construct_command(command_id, payload)
        with self.lock:
            self.ser.write(command)
            logging.info(f"Sent command: {command.hex()}")

    def construct_command(self, command_id: int, payload: bytes) -> bytes:
        """
        Constructs a command according to the protocol.
        """
        START_BYTE = 0x02
        END_BYTE = 0x03
        payload_length = len(payload)
        header = bytes([START_BYTE, command_id, payload_length])
        checksum = self.calculate_checksum(header + payload)
        command = header + payload + bytes([checksum, END_BYTE])
        return command

    def calculate_checksum(self, data: bytes) -> int:
        """
        Calculates checksum as XOR of all bytes in data.
        """
        checksum = 0
        for b in data:
            checksum ^= b
        return checksum

    def read_from_uart(self):
        """
        Continuously reads data from UART in a separate thread.
        """
        while self.is_connected():
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    with self.lock:
                        self.buffer.extend(data)
                    self.process_uart_data()
                time.sleep(0.1)
            except serial.SerialException as e:
                logging.error(f"Error reading from UART port: {e}")
                self.connected = False
                break

    def process_uart_data(self):
        """
        Processes data received from UART.
        """
        while True:
            message = self.parse_message()
            if message:
                logging.info(f"Received message: {message.hex()}")
            else:
                break

    def parse_message(self):
        """
        Parses messages from the buffer according to the protocol.
        """
        START_BYTE = 0x02
        END_BYTE = 0x03
        with self.lock:
            if START_BYTE in self.buffer:
                start_index = self.buffer.index(START_BYTE)
                if END_BYTE in self.buffer[start_index:]:
                    end_index = self.buffer.index(END_BYTE, start_index)
                    message = self.buffer[start_index:end_index+1]
                    del self.buffer[start_index:end_index+1]
                    return message
            return None
