import serial
import command_pb2  # Import the generated Protobuf code from your command.proto

def send_command(command):
    ser = serial.Serial('/dev/ttyS0', 115200)  # Adjust this to your serial port
    ser.write(command.SerializeToString())
    ser.close()

# Test SetPositionCommand
def test_set_position():
    command = command_pb2.Command()
    command.set_position.azimuth = 45.0
    command.set_position.elevation = 30.0
    send_command(command)

# Test GetPositionCommand
def test_get_position():
    command = command_pb2.Command()
    command.get_position.SetInParent()  # Create an empty GetPositionCommand
    send_command(command)

if __name__ == "__main__":
    test_set_position()  # Test SetPositionCommand
    test_get_position()  # Test GetPositionCommand
