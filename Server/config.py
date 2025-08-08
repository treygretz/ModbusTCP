# config.py
# Stores some static variables that remain unchanged
UPLOAD_DIR = "/home/oishii/uploaded_scripts"
TARGET_FILENAME = "Barcode_Thread_Worker.py"

MODBUS_HOST = "10.190.54.222"
MODBUS_PORT = 502

FLASK_HOST = "10.190.54.222"
FLASK_PORT = 8000

# Time in seconds for file transfer to complete
TRANSFER_DELAY = 15

MODBUS_STARTING_REGISTER = 1001
TOTAL_CLIENTS = 32
# Have to include the + 1 to bring the IP range up to the correct end value
CLIENT_IP_RANGE = (1, 32 + 1)