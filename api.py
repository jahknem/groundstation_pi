from fastapi import FastAPI, HTTPException
import logging
from uart_comm import UARTCommunication
from controller import USBController

app = FastAPI(
    title="Your Project API",
    description="API to control the microcontroller via UART",
    version="1.0.0"
)

# Initialize UARTCommunication and USBController
uart_comm = UARTCommunication()
if not uart_comm.is_connected():
    logging.error("UARTCommunication is not connected. UART port might be unavailable.")

usb_controller = USBController()
# Controller configuration remains as per your requirements

@app.get("/status")
def get_status():
    """
    Retrieves the status from the microcontroller.
    """
    if not uart_comm.is_connected():
        logging.error("UART port is not connected. Cannot retrieve status.")
        raise HTTPException(status_code=500, detail="UART port is not connected.")
    try:
        uart_comm.send_command(0x07, b'')
        return {"message": "Status requested"}
    except Exception as e:
        logging.exception(f"Error sending status request: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending status request: {str(e)}")

# Other endpoints with similar error handling and logging
