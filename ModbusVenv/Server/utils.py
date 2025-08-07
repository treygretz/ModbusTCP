# utils.py
# Use the GuiLogger object to get the print statements into the UI for the user to see
import datetime

class GuiLogger:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.insert("end", message)
        self.text_widget.see("end")

    def flush(self):
        pass

# Logs important faults to a file in the background
def writeToLog(msg):
    dt = datetime.datetime.now()
    timestamp = dt.strftime("%m/%d/%Y %H:%M:%S")
    with open("/home/oishii/Documents/ReadBarcode.log", "a") as f:
        f.write(f"{timestamp} --> {msg}\n")