#12:09
import threading
import time
import queue
import datetime
import evdev
from pyModbusTCP.client import ModbusClient
from config import MODBUS_HOST, MODBUS_PORT, FLASK_HOST, FLASK_PORT, MODBUS_STARTING_REGISTER, TOTAL_CLIENTS
import subprocess
import flask
import requests

# Constants
URL = "http://" + FLASK_HOST + ":" + str(FLASK_PORT) + "/file"
SAVE_AS = "/home/oishii/Python/Barcode_Thread_Worker.py"

# Global events
scanner_event = threading.Event()
client_event = threading.Event()
retry_event = threading.Event()

def WriteToLog(xstr):
    dt = datetime.datetime.now()
    dtstr = f"{dt.month}/{dt.day}/{dt.year} {dt.hour}:{dt.minute}:{dt.second} --> "
    with open("/home/oishii/Documents/ReadBarcode.log", "a") as f:
        f.write(dtstr + xstr + "\n")


def findIP():
    while True:
        try:
            result = subprocess.run(["ip addr show eth0 | grep 'inet ' | awk '{print$2}' | cut -d/ -f1"],
                                    shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ip_address = result.stdout.strip()
            print(ip_address)
            return ip_address
        except Exception as Ex:
            print(f"Error in findIP(): {Ex}")
            time.sleep(2)


def parseIPtoRegister():
    ip_parts = list(map(int, findIP().split('.')))
    return ip_parts[2] * 1000 + ip_parts[3]


def getDevices(scanner_queue):
    while not retry_event.is_set():
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for scanner in devices:
                if "Barcode" in scanner.name:
                    print("Barcode Scanner Found!")
                    scanner_queue.put(scanner)
                    scanner_event.set()
                    return
            print("Trying to connect to barcode scanner...")
            time.sleep(2)
        except Exception as Ex:
            print(f"Error in getDevices(): {Ex}")
            time.sleep(2)


def getConnectedToServer(client_queue):
    while not retry_event.is_set():
        try:
            client = ModbusClient(host='10.190.54.222', port=502, auto_open=True, timeout=5)
            if client.open():
                print("Server connection found!")
                client_queue.put(client)
                client_event.set()
                return
            else:
                print("Attempting reconnection to Server...")
                print(client.last_error_as_txt)
                time.sleep(5)
        except Exception as Ex:
            print(f"Error in getConnectedToServer(): {Ex}")
            time.sleep(2)


def sendPulse(client, retry_event):
    while not retry_event.is_set():
        if not client.is_open:
            raise ConnectionError('Lost Modbus Connection')

        scanner_event.wait()
        if retry_event.is_set():
            return

        serverIPRegister = parseIPtoRegister()
        IPlist = client.read_holding_registers(MODBUS_STARTING_REGISTER, TOTAL_CLIENTS)
        print(f"{IPlist}\n")
        PulseRegister = None

        for IP in IPlist:
            if IP == serverIPRegister:
                PulseRegister = IPlist.index(IP)

        if PulseRegister is not None:
            client.write_single_register((PulseRegister * 10) + 7, 1)
            for _ in range(50):
                if retry_event.is_set():
                    return
                time.sleep(0.1)
            client.write_single_register((PulseRegister * 10) + 7, 0)
            for _ in range(50):
                if retry_event.is_set():
                    return
                time.sleep(0.1)
        else:
            print("PulseRegister not found")


def updateServerBarcodeRegisters(scanner, client, retry_event):
    barcode = ''

    try:
        while not retry_event.is_set():
            if not client.is_open:
                raise ConnectionError("Lost Modbus Connection")
            
			# Prevents the scanner from blocking so it can easily detect server disconnections
            event = scanner.read_one()

            if event is None:
                time.sleep(0.05)  # Sleep briefly to reduce CPU usage
                continue

            if event.value == 1:
                if event.code == evdev.ecodes.KEY_ENTER:
                    if len(barcode) > 0:
                        print("Read: " + barcode)
                        serverIPRegister = parseIPtoRegister()
                        IPlist = client.read_holding_registers(MODBUS_STARTING_REGISTER, TOTAL_CLIENTS)
                        QRregister = None
                        for IP in IPlist:
                            if IP == serverIPRegister:
                                QRregister = (IPlist.index(IP))+1
                        dt = datetime.datetime.now()
                        current_value = client.read_holding_registers(QRregister * 10, 1)
                        if current_value != [int(barcode)]:
                            client.write_multiple_registers(QRregister * 10, [
                                int(barcode), dt.year, dt.month, dt.day,
                                dt.hour, dt.minute, dt.second
                            ])
                        barcode = ""
                else:
                    barcode += str(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][event.code]).replace("KEY_", "")
    except Exception as ex:
        print(f"[updateServerBarcodeRegisters] Error: {ex}")
        retry_event.set()



def checkForUpdates(client, retry_event):
    while not retry_event.is_set():
        try:
            print("Checking for updates...")
            # The function read_holding_registers returns a list for the Modbus Client so it just checks the first index of that list to determine if the server set the flag high
            if client.read_holding_registers(1000, 1)[0] == 1:
                print("Update Found")
                response = requests.get(URL)
                if response.status_code == 200:
                    with open(SAVE_AS, 'wb') as f:
                        f.write(response.content)
                    print(f"File downloaded and saved as '{SAVE_AS}'")
                    time.sleep(15)
                    subprocess.run(["sudo", "reboot", "now"])
                else:
                    print(f"Failed to download file. Server responded with status code {response.status_code}")
            time.sleep(10)
        except Exception as Ex:
            print(f"Error in checkForUpdates(): {Ex}")
            retry_event.set()


# ✅ Central Thread Wrapper
def thread_worker(target_func, *args):
    try:
        target_func(*args)
    except Exception as e:
        print(f"[{target_func.__name__}] error: {e}")
        retry_event.set()
    finally:
        print(f"[{target_func.__name__}] exiting.")


def continuousRun():
    while True:
        # Reset everything for this loop
        scanner_queue = queue.Queue()
        client_queue = queue.Queue()
        retry_event.clear()
        scanner_event.clear()
        client_event.clear()

        # Step 1: Connect to scanner and server
        print("Starting setup threads...")
        server_thread = threading.Thread(target=thread_worker, args=(getConnectedToServer, client_queue))
        device_thread = threading.Thread(target=thread_worker, args=(getDevices, scanner_queue))
        server_thread.start()
        device_thread.start()
        server_thread.join()
        device_thread.join()

        if retry_event.is_set():
            print("Setup failed. Restarting...")
            continue

        scanner = scanner_queue.get()
        client = client_queue.get()

        print("Starting worker threads...\n")
        # Step 2: Start all worker threads as daemon threads
        pulse_thread = threading.Thread(target=thread_worker, args=[sendPulse, client, retry_event], daemon=True)
        barcode_thread = threading.Thread(target=thread_worker, args=[updateServerBarcodeRegisters, scanner, client, retry_event], daemon=True)
        update_thread = threading.Thread(target=thread_worker, args=[checkForUpdates, client, retry_event], daemon=True)

        pulse_thread.start()
        barcode_thread.start()
        update_thread.start()

        # Step 3: Wait for retry trigger
        while not retry_event.is_set():
            time.sleep(1)
            
        pulse_thread.join()
        barcode_thread.join()
        update_thread.join()

        print("Retry triggered. Restarting all threads...\n")


if __name__ == "__main__":
    continuousRun()
