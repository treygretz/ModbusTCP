# state_manager.py
# Threading is used to keep the GUI actively running for the user to interface with a threaded ModbusTCP server
import threading
from tkinter import filedialog
import shutil
import os
from modbus_server import ModbusServerThread
from config import UPLOAD_DIR, TARGET_FILENAME

modbus_server_thread = None
# Initialize a ModbusServerThread Object to control the state of the server
modbus_server = ModbusServerThread()

# Once the user clicks the start server button from gui.py this function is called to start the server thread and calls the start_modbus_server function
# from the ModbusServerThread() object to start the ModbusTCP server
def start_modbus_server_thread():
    global modbus_server_thread
    if modbus_server_thread is None or not modbus_server_thread.is_alive():
        modbus_server.stop_event.clear()
        modbus_server_thread = threading.Thread(target=modbus_server.start_modbus_server,daemon=True)
        modbus_server_thread.start()
        print("Modbus server thread started.")

def stop_modbus_server_thread():
    modbus_server.stop_modbus_server()
    print("Modbus server stopped via GUI.")

# After the upload file button has been interacted with this gives the user a file explorer popup window to upload a python file
def handle_file_upload():
    file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
    if not file_path:
        return

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = os.path.basename(file_path)  # get just the filename
    dest_path = os.path.join(UPLOAD_DIR, filename)

    shutil.copy(file_path, dest_path)
    print(f"File uploaded and saved to {dest_path}")

    # Now update the modbus registers to notify clients
    if  modbus_server_thread.is_alive():  # assuming you have access to your ModbusServerThread instance
        modbus_server.update_file_registers(TARGET_FILENAME)
        print("Updated server file registers")