# tests/test_uart_comm.py
import unittest
from uart_comm import UARTCommunication

class TestUARTCommunication(unittest.TestCase):
    def test_construct_command(self):
        uart_comm = UARTCommunication(port='/dev/null')
        command_id = 0x01
        payload = b'\x00\x01\x00\x02'
        command = uart_comm.construct_command(command_id, payload)
        expected_length = 1 + 1 + 1 + 4 + 1 + 1  # Start, ID, Length, Payload, Checksum, End
        self.assertEqual(len(command), expected_length)
