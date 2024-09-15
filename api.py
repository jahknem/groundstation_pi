from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from uart_comm import UARTCommunication
from controller import USBController

app = FastAPI(
    title="Your Project API",
    description="API to control the microcontroller via UART",
    version="1.0.0"
)

uart_comm = UARTCommunication()
usb_controller = USBController()

class UARTConfig(BaseModel):
    port: str
    baudrate: int = 115200
    timeout: float = 1.0

class ControllerConfig(BaseModel):
    device_id: int = 0

@app.post("/uart/configure")
def configure_uart(config: UARTConfig):
    """
    Configures the UART communication.
    """
    uart_comm.configure(port=config.port, baudrate=config.baudrate, timeout=config.timeout)
    if not uart_comm.is_connected():
        raise HTTPException(status_code=500, detail="UART port could not be opened.")
    return {"message": "UART configured successfully."}

@app.post("/controller/configure")
def configure_controller(config: ControllerConfig):
    """
    Configures the USB controller.
    """
    usb_controller.configure(device_id=config.device_id)
    if not usb_controller.is_connected():
        raise HTTPException(status_code=500, detail="Controller could not be initialized.")
    return {"message": "Controller configured successfully."}

@app.get("/status")
def get_status():
    """
    Retrieves the status from the microcontroller.
    """
    if not uart_comm.is_connected():
        raise HTTPException(status_code=500, detail="UART port is not connected.")
    try:
        uart_comm.send_command(0x07, b'')
        return {"message": "Status requested"}
    except Exception as e:
        logging.error(f"Error sending status request: {e}")
        raise HTTPException(status_code=500, detail="Error sending status request.")

# ... (other endpoints with similar error handling)
