#!/usr/bin/env python3
"""
File: uart_comm.py
Author: Jan Kühnemund
Description: Handles UART communication with the microcontroller.
"""

import serial
from threading import Thread, Lock
import time
import logging
import os
import random
from dotenv import load_dotenv
from collections import deque

load_dotenv()

class UARTCommunication:
    """
    Handles UART communication with the microcontroller.
    """
    def __init__(self):
        self.port = os.getenv('UART_PORT')
        self.baudrate = int(os.getenv('UART_BAUDRATE', '115200'))
        self.timeout = float(os.getenv('UART_TIMEOUT', '1'))
        self.ser = None
        self.lock = Lock()
        self.read_thread = None
        self.buffer = bytearray()
        self.connected = False
        self.pending_messages = {}  # Track messages awaiting ACKs
        self.current_position = {'azimuth': 0, 'elevation': 0}  # Latest position data
        self.position_lock = Lock()  # Lock for accessing current_position
        self.initialize_uart()

    def initialize_uart(self):
        """
        Initializes the UART port.
        """
        logging.info("Initializing UART port...")
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

    def send_command(self, command_id: int, payload: bytes = b'') -> None:
        """
        Constructs and sends a command to the microcontroller with retransmission logic.
        """
        if not self.is_connected():
            logging.error("Attempted to send command, but UART port is not connected.")
            raise serial.SerialException("UART port is not connected.")

        message_id = random.randint(0, 255)
        command = self.construct_command(message_id, command_id, payload)
        self.pending_messages[message_id] = {
            'command': command,
            'attempts': 0,
            'last_sent': 0,
            'ack_received': False
        }

        # Start a separate thread to handle retransmission
        Thread(target=self._send_with_retransmission, args=(message_id,), daemon=True).start()

    def _send_with_retransmission(self, message_id):
        """
        Sends the message and handles retransmissions if ACK is not received.
        """
        max_backoff = 1.0
        base_timeout = 0.1
        while not self.pending_messages[message_id]['ack_received']:
            current_time = time.time()
            last_sent = self.pending_messages[message_id]['last_sent']
            attempts = self.pending_messages[message_id]['attempts']

            # Exponential backoff
            timeout = min(base_timeout * (2 ** attempts), max_backoff)

            if current_time - last_sent >= timeout:
                with self.lock:
                    try:
                        self.ser.write(self.pending_messages[message_id]['command'])
                        self.pending_messages[message_id]['last_sent'] = current_time
                        self.pending_messages[message_id]['attempts'] += 1
                        logging.debug(f"Sent command with MESSAGE_ID {message_id}: {self.pending_messages[message_id]['command'].hex()}")
                    except Exception as e:
                        logging.exception(f"Error sending command: {e}")
                        break
            time.sleep(0.1)

            # Optionally, set a maximum number of attempts
            if self.pending_messages[message_id]['attempts'] > 10:
                logging.error(f"Failed to receive ACK for MESSAGE_ID {message_id} after multiple attempts.")
                del self.pending_messages[message_id]
                break

    def construct_command(self, message_id: int, command_id: int, payload: bytes) -> bytes:
        """
        Constructs a command according to the protocol.
        """
        START_BYTE = 0x02
        END_BYTE = 0x03
        payload_length = len(payload)
        header = bytes([START_BYTE, message_id, command_id, payload_length])
        checksum_data = bytes([message_id, command_id, payload_length]) + payload
        checksum = self.calculate_checksum(checksum_data)
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
                self.handle_message(message)
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
            if buffer_length < 6:  # Minimum length of a message
                return None
            try:
                # Find START_BYTE
                if START_BYTE in self.buffer:
                    start_index = self.buffer.index(START_BYTE)
                    # Ensure there are enough bytes for header
                    if buffer_length - start_index < 6:
                        return None
                    message_id = self.buffer[start_index + 1]
                    command_id = self.buffer[start_index + 2]
                    payload_length = self.buffer[start_index + 3]
                    expected_length = 6 + payload_length  # Total expected length of the message
                    if buffer_length - start_index < expected_length:
                        logging.debug("Incomplete message received. Waiting for more data.")
                        return None
                    # Extract the message
                    end_index = start_index + expected_length - 1
                    if self.buffer[end_index] != END_BYTE:
                        logging.error("END_BYTE not found where expected. Discarding bytes.")
                        self.buffer = self.buffer[end_index+1:]
                        return None
                    message = self.buffer[start_index:end_index+1]
                    # Remove the processed message from the buffer
                    self.buffer = self.buffer[end_index+1:]
                    logging.debug(f"Parsed message from buffer: {message.hex()}")
                    return message
                else:
                    # START_BYTE not found, discard the buffer
                    logging.debug("START_BYTE not found in buffer. Clearing buffer.")
                    self.buffer.clear()
                    return None
            except Exception as e:
                logging.exception(f"Error parsing message from buffer: {e}")
                self.buffer.clear()
                return None

    def handle_message(self, message: bytes):
        """
        Handles a complete message received from UART.
        """
        try:
            START_BYTE = message[0]
            message_id = message[1]
            command_id = message[2]
            payload_length = message[3]
            payload = message[4:4+payload_length]
            checksum = message[4+payload_length]
            END_BYTE = message[5+payload_length]

            # Recalculate checksum
            checksum_data = message[1:4+payload_length]
            calculated_checksum = self.calculate_checksum(checksum_data)

            if checksum != calculated_checksum:
                logging.error(f"Invalid checksum for received message. Expected {calculated_checksum:#04x}, got {checksum:#04x}")
                return

            logging.info(f"Received message - MESSAGE_ID: {message_id}, COMMAND_ID: {command_id}, PAYLOAD: {payload.hex()}")

            # Handle ACK
            if command_id == 0x06:  # ACK Command ID
                self.handle_ack(message_id)
            else:
                # Handle data messages (e.g., status updates)
                self.process_data_message(command_id, payload)
        except Exception as e:
            logging.exception(f"Error handling message: {e}")

    def handle_ack(self, message_id):
        """
        Handles an ACK message.
        """
        original_message_id = (message_id - 1) % 256
        if original_message_id in self.pending_messages:
            self.pending_messages[original_message_id]['ack_received'] = True
            logging.info(f"ACK received for MESSAGE_ID {original_message_id}")
            del self.pending_messages[original_message_id]
        else:
            logging.warning(f"Received ACK for unknown MESSAGE_ID {original_message_id}")

    def process_data_message(self, command_id, payload):
        """
        Processes data messages received from the microcontroller.
        """
        logging.info(f"Processing data message COMMAND_ID {command_id:#04x} with payload: {payload.hex()}")

        # If the command is a status update (e.g., COMMAND_ID = 0x09)
        if command_id == 0x09:
            # Parse the payload to extract azimuth and elevation
            if len(payload) >= 4:
                azimuth = int.from_bytes(payload[0:2], 'big', signed=False)
                elevation = int.from_bytes(payload[2:4], 'big', signed=False)
                with self.position_lock:
                    self.current_position['azimuth'] = azimuth
                    self.current_position['elevation'] = elevation
                logging.info(f"Updated position: Azimuth={azimuth}, Elevation={elevation}")
            else:
                logging.error("Payload too short for position data")
        else:
            # Handle other data messages if needed
            pass

    def get_current_position(self):
        """
        Retrieves the latest position data in a thread-safe manner.
        """
        with self.position_lock:
            return self.current_position.copy()

    def get_received_data(self):
        """
        Retrieves received data messages.

        Returns:
            A list of data messages received from the microcontroller.
        """
        data_messages = []
        while self.received_data:
            data_messages.append(self.received_data.popleft())
        return data_messages
