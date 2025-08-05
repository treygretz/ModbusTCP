import threading
import time
import queue
import datetime
import evdev
from pyModbusTCP.client import ModbusClient
from config import MODBUS_HOST, MODBUS_PORT
import subprocess
import flask


# Global variables to track running threads and retry state
scanner_event = threading.Event()  # Signal when scanner is found
client_event = threading.Event()  # Signal when client is connected
retry_event = threading.Event()  # Retry event for restarting the process

def WriteToLog(xstr):
    dt = datetime.datetime.now()
    dtstr = str(dt.month) + "/" + str(dt.day) + "/" + str(dt.year) + " " + str(dt.hour) + ":" + str(dt.minute) + ":" + str(dt.second) + " --> "
    with open("/home/oishii/Documents/ReadBarcode.log", "a") as f:
        f.write(dtstr + xstr + "\n")


def findIP():
    while True:
        try:
            result = subprocess.run(["ip addr show eth0 | grep 'inet ' | awk '{print$2}' | cut -d/ -f1"], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ip_address = result.stdout.strip()
            print(ip_address)
            return ip_address
        except Exception as Ex:
            print(f"Error in findIP(): {Ex}")
            time.sleep(2)


def parseIPtoRegister():
    ip_parts = list(map(int, findIP().split('.')))
    register = ip_parts[2] * 1000 + ip_parts[3]
    return register


def getDevices(scanner_queue):
    while not retry_event.is_set():
        try:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            for scanner in devices:
                if "Barcode" in scanner.name:
                    print("Barcode Scanner Found!")
                    scanner_queue.put(scanner)  # Put the scanner in the queue
                    scanner_event.set()  # Signal that the scanner is found
                    return  # Exit once scanner is found
            else:
                print("Trying to connect to barcode scanner...")
                time.sleep(2)
        except Exception as Ex:
            print(f"Error in getDevices(): {Ex}")
            time.sleep(2)


def getConnectedToServer(client_queue):
    while not retry_event.is_set():
        try:
            serverIP = MODBUS_HOST
            client = ModbusClient(host=serverIP, port=MODBUS_PORT, auto_open=True, timeout=1)
            if client.open():
                print("Server connection found!")
                client_queue.put(client)  # Put the client in the queue
                client_event.set()  # Signal that the client is connected
                return
            else:
                print("Attempting reconnection to Server...")
                time.sleep(2)
        except Exception as Ex:
            print(f"Error in getConnectedToServer(): {Ex}")
            time.sleep(2)

def sendPulse(client):
    try:
        while not retry_event.is_set():
            if client.is_open == False:
                raise ConnectionError('Lost Connection')
            scanner_event.wait()  # Wait for the scanner to be found
            serverIPRegister = parseIPtoRegister()
            IPlist = client.read_holding_registers(1051, 26)
            PulseRegister = None

            for IP in IPlist:
                if IP == serverIPRegister:
                    PulseRegister = IPlist.index(IP)

            if PulseRegister is not None:
                client.write_single_register((PulseRegister * 10) + 7, 1)
                time.sleep(5)
                client.write_single_register((PulseRegister * 10) + 7, 0)
                time.sleep(5)
            else:
                print("PulseRegister not found")
    except Exception as Ex:
        print(f"Error in sendPulse(): {Ex}")
    finally:
        retry_event.set()


def updateServerBarcodeRegisters(scanner, client):
    try:
        print(str(scanner))
        barcode = ''
        while not retry_event.is_set():
            for event in scanner.read_loop():
                if client.is_open == False:
                    raise ConnectionError('Lost Connection')
                if event.value == 1:
                    if event.code == evdev.ecodes.KEY_ENTER:
                        if len(barcode) > 0:
                            print("Read: " + barcode)
                            serverIPRegister = parseIPtoRegister()
                            IPlist = client.read_holding_registers(1051, 26)
                            QRregister = None
                            for IP in IPlist:
                                if IP == serverIPRegister:
                                    QRregister = IPlist.index(IP)
                            dt = datetime.datetime.now()
                            if client.read_holding_registers(QRregister * 10, 1) != barcode:
                                client.write_multiple_registers(QRregister * 10, [int(barcode), dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second])
                            barcode = ""
                    else:
                        barcode += str(evdev.ecodes.bytype[evdev.ecodes.EV_KEY][event.code]).replace("KEY_", "")
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        # When retry event is set, stop and retry
        retry_event.set()

def checkForUpdates(client):
    while True:
        try:
            print("In the checkForUpdates")
            if client.read_holding_registers(1000) == 1:
                response = requests.get(URL)
                if response.status_code == 200:
                    with open(SAVE_AS, 'wb') as f:
                        f.write(response.content)
                    print(f"File downloaded and saved as '{SAVE_AS}'")
                else:
                    print(f"Failed to download file. Server responded with status code {response.status_code}")
            result = subprocess.run(["ip addr show eth0 | grep 'inet ' | awk '{print$2}' | cut -d/ -f1"], shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            ip_address = result.stdout.strip()
            time.sleep(5)
            #print(ip_address)
            #Why was this return here?
            #return ip_address
        except Exception as Ex:
            print(f"Error in findIP(): {Ex}")
            time.sleep(2)




def continuousRun():
    while True:
        # Create queues and event flags
        scanner_queue = queue.Queue()
        client_queue = queue.Queue()

        # Create and start threads for devices and server connection
        server_thread = threading.Thread(target=getConnectedToServer, args=(client_queue,))
        server_thread.start()

        device_thread = threading.Thread(target=getDevices, args=(scanner_queue,))
        device_thread.start()

        # Wait for both threads to finish
        server_thread.join()
        device_thread.join()

        # Retrieve scanner and client objects
        scanner = scanner_queue.get()
        client = client_queue.get()

        # Start the pulse and barcode threads
        pulse_thread = threading.Thread(target=sendPulse, args=(client,))
        update_server_thread = threading.Thread(target=updateServerBarcodeRegisters, args=(scanner, client))
        change_project_revision = threading.Thread(target=checkForUpdates, args=(client,))

        pulse_thread.start()
        update_server_thread.start()
        change_project_revision.start()

        # Wait for the barcode and pulse threads to complete
        pulse_thread.join()
        update_server_thread.join()
        change_project_revision.join()

        # If retry_event is set, exit and restart the loop
        if retry_event.is_set():
            print("Restarting due to error.")
            retry_event.clear()  # Reset the retry event
            continue  # Restart the loop


if __name__ == "__main__":
    continuousRun()
