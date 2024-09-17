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
        self.button_mapping = {}
        self.axis_mapping = {}

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
        
    def set_button_mapping(self, mapping: dict):
        """
        Sets the mapping from controller buttons to actions.
        """
        self.button_mapping = mapping
        logging.info(f"Button mapping set: {self.button_mapping}")

    def set_axis_mapping(self, mapping: dict):
        """
        Sets the mapping from controller axes to actions.
        """
        self.axis_mapping = mapping
        logging.info(f"Axis mapping set: {self.axis_mapping}")

    def get_mapped_input(self):
        """
        Retrieves input and applies the user-defined mapping.
        """
        raw_input = self.get_input()
        mapped_buttons = {self.button_mapping.get(k, k): v for k, v in raw_input['buttons'].items()}
        mapped_axes = {self.axis_mapping.get(k, k): v for k, v in raw_input['axes'].items()}
        return {'axes': mapped_axes, 'buttons': mapped_buttons}