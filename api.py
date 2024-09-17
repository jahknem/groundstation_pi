from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from uart_comm import UARTCommunication
from controller import USBController

app = FastAPI(
    title="Tracking Groundstation",
    description="API to control the microcontroller via UART",
    version="1.0.0"
)
# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize UARTCommunication and USBController
uart_comm = UARTCommunication()
if not uart_comm.is_connected():
    logging.error("UARTCommunication is not connected. UART port might be unavailable.")

usb_controller = USBController()
# Controller configuration remains as per your requirements

# In-memory storage for mapping
input_mapping = {}

@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """
    Serves the main page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/save-mapping")
async def save_mapping(mapping: dict):
    """
    Saves the user-defined input mapping.
    """
    global input_mapping
    input_mapping = mapping
    # Optionally, save to a file or database
    logging.info(f"Input mapping saved: {input_mapping}")
    return {"status": "success"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Process data as needed
            # For example, send commands via UART based on input
            buttons = data.get('buttons', {})
            axes = data.get('axes', {})
            # Implement action handling based on buttons and axes
            # Example:
            if buttons.get('arm'):
                uart_comm.send_command(0x01, b'')  # Command to arm
            if axes.get('move_x'):
                # Process movement on X-axis
                pass
            # Additional processing...
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")

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

def handle_action(action):
    # Implement the action, e.g., send command via UART
    if action == 'arm':
        uart_comm.send_command(0x01, b'')  # Command to arm
    elif action == 'disarm':
        uart_comm.send_command(0x02, b'')  # Command to disarm
    # Add more actions as needed

def handle_axis_action(action, value):
    # Implement axis action
    if action == 'move_x':
        # Convert axis value to movement command
        pass
    # Add more axis actions as needed