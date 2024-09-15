import pygame
import logging

class USBController:
    """
    Handles USB controller inputs.
    """
    def __init__(self):
        self.device_id = None
        self.joystick = None
        self.connected = False

    def configure(self, device_id: int = 0):
        """
        Configures and initializes the joystick.
        """
        self.device_id = device_id
        pygame.init()
        pygame.joystick.init()
        try:
            if pygame.joystick.get_count() == 0:
                raise Exception("No joystick connected")
            self.joystick = pygame.joystick.Joystick(self.device_id)
            self.joystick.init()
            self.connected = True
            logging.info(f"Joystick {self.device_id} initialized.")
        except Exception as e:
            self.connected = False
            logging.error(f"Failed to initialize joystick {self.device_id}: {e}")

    def is_connected(self):
        """
        Checks if the joystick is connected.
        """
        return self.connected

    def get_input(self):
        """
        Retrieves input from the controller.
        """
        if not self.is_connected():
            raise Exception("Joystick is not connected.")
        pygame.event.pump()
        axes = {}
        buttons = {}
        for i in range(self.joystick.get_numaxes()):
            axes[f'axis_{i}'] = self.joystick.get_axis(i)
        for i in range(self.joystick.get_numbuttons()):
            buttons[f'button_{i}'] = self.joystick.get_button(i)
        return {'axes': axes, 'buttons': buttons}
