# tests/test_controller.py
import unittest
from unittest.mock import MagicMock, patch
from controller import USBController

class TestUSBController(unittest.TestCase):
    @patch('controller.pygame')
    def test_get_input(self, mock_pygame):
        mock_pygame.init.return_value = None
        mock_pygame.joystick.init.return_value = None
        mock_pygame.joystick.get_count.return_value = 1
        mock_joystick = MagicMock()
        mock_joystick.get_numaxes.return_value = 2
        mock_joystick.get_numbuttons.return_value = 2
        mock_joystick.get_axis.return_value = 0.5
        mock_joystick.get_button.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        controller = USBController()
        input_data = controller.get_input()
        self.assertIn('axes', input_data)
        self.assertIn('buttons', input_data)
