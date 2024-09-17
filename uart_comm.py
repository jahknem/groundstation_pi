import serial
from threading import Thread, Lock
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv() 

class UARTCommunication:
    """
    Handles UART communication with the microcontroller.
    """
    def __init__(self):
        self.port = str(os.getenv('UART_PORT'))
        self.baudrate = int(os.getenv('UART_BAUDRATE', '115200'))
        self.timeout = float(os.getenv('UART_TIMEOUT', '1')) 
        self.ser = None
        self.lock = Lock()
        self.read_thread = None
        self.buffer = bytearray()
        self.connected = False
        self.initialize_uart()

    def initialize_uart(self):
        """
        Initializes the UART port.
        """
        if not self.port:
            logging.error("UART_PORT not specified in environment variables.")
            return
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
        except Exception as e:
            self.connected = False
            logging.exception(f"Unexpected error when initializing UART: {e}")

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
            logging.error("Attempted to send command, but UART port is not connected.")
            raise serial.SerialException("UART port is not connected.")
        command = self.construct_command(command_id, payload)
        with self.lock:
            try:
                self.ser.write(command)
                logging.debug(f"Sent command: {command.hex()}")
            except Exception as e:
                logging.exception(f"Error sending command: {e}")

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
        logging.debug(f"Constructed command: {command.hex()}")
        return command

    def calculate_checksum(self, data: bytes) -> int:
        """
        Calculates checksum as XOR of all bytes in data.
        """
        checksum = 0
        for b in data:
            checksum ^= b
        logging.debug(f"Calculated checksum: {checksum:#04x}")
        return checksum

    def read_from_uart(self):
        """
        Continuously reads data from UART in a separate thread.
        """
        while True:
            if not self.is_connected():
                logging.debug("UART port is not connected. Read thread exiting.")
                break
            try:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)
                    with self.lock:
                        self.buffer.extend(data)
                    logging.debug(f"Read {len(data)} bytes from UART: {data.hex()}")
                    self.process_uart_data()
                time.sleep(0.1)
            except Exception as e:
                logging.exception(f"Error reading from UART port: {e}")
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
            buffer_length = len(self.buffer)
            if buffer_length == 0:
                return None
            try:
                if START_BYTE in self.buffer:
                    start_index = self.buffer.index(START_BYTE)
                    if END_BYTE in self.buffer[start_index + 1:]:
                        end_index = self.buffer.index(END_BYTE, start_index + 1)
                        message = self.buffer[start_index:end_index+1]
                        # Remove the processed message from the buffer
                        self.buffer = self.buffer[end_index+1:]
                        logging.debug(f"Parsed message from buffer: {message.hex()}")
                        return message
                    else:
                        # END_BYTE not found yet, wait for more data
                        logging.debug("END_BYTE not found in buffer yet.")
                        return None
                else:
                    # START_BYTE not found, discard the buffer
                    logging.debug("START_BYTE not found in buffer. Clearing buffer.")
                    self.buffer.clear()
                    return None
            except Exception as e:
                logging.exception(f"Error parsing message from buffer: {e}")
                self.buffer.clear()
                return None
