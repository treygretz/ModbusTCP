# modbus_server.py
import time
import psutil
import threading
from pyModbusTCP.server import ModbusServer
from utils import writeToLog
from config import MODBUS_HOST, MODBUS_PORT, TRANSFER_DELAY, MODBUS_STARTING_REGISTER, TOTAL_CLIENTS, CLIENT_IP_RANGE

# ModbusServer Object can be interacted with to start/stop the server and 
# the file location registers are updated for the client to pull from via FTP
class ModbusServerThread:
    def __init__(self):
        self.server = None
        self.stop_event = threading.Event()

    def update_file_registers(self, filename):
        # ascii_codes = [ord(c) for c in filename[:10]]
        self.server.data_bank.set_holding_registers(1000, [1])       # File available flag
        # self.server.data_bank.set_holding_registers(1001, ascii_codes)
        print(f"File available: {filename}")

    def start_modbus_server(self):
        try:
            self.server = ModbusServer(host=MODBUS_HOST, port=MODBUS_PORT, no_block=True)
            self.server.start()
            if self.server.is_run:
                print(f"Modbus Server Started at {MODBUS_HOST}:{MODBUS_PORT}")

            # Ensure the new file uploaded flag is set to false
            self.server.data_bank.set_holding_registers(1000, [0])

            ip_addresses = [63 * 1000 + i for i in range(*CLIENT_IP_RANGE)]
            self.server.data_bank.set_holding_registers(MODBUS_STARTING_REGISTER, ip_addresses)
            print("IP addresses stored in registers.")

            while not self.stop_event.is_set():
                for i in range(*CLIENT_IP_RANGE):
                    data = self.server.data_bank.get_holding_registers(i * 10, 9)
                    if data and data[0] != 0:
                        print(f"Data read from holding registers {i*10} -> {(i * 10) + 9}: {data}")
                print(f"CPU Usage: {psutil.cpu_percent(interval=1)}%")
                try:
                    status = self.server.data_bank.get_holding_registers(1000)
                    if status and status[0] == 1:
                        print(f"File transfer is online! \n Time: {TRANSFER_DELAY} sec \n")
                        time.sleep(TRANSFER_DELAY)
                        self.server.data_bank.set_holding_registers(1000, [0])
                        print("File transfer is now offline...\n")
                    else:
                        print("-----------------------------------")
                except Exception as e:
                    print(f"Error reading holding register 1000: {e}")
                time.sleep(2)

        except Exception as ex:
            print(f"Error in Modbus Server: {ex}")
            writeToLog(f"Error in Modbus Server: {ex}")
        finally:
            if self.server:
                self.server.stop()
                print("Modbus Server Stopped")
                writeToLog("Modbus Server Stopped")

    def stop_modbus_server(self):
        self.stop_event.set()
        if self.server:
            self.server.stop()
