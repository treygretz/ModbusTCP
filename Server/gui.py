# gui.py 
# Displays the main GUI interface that the server operates on where the user can interact with
import sys
import threading
from tkinter import Tk, Label, Button, filedialog
from tkinter.scrolledtext import ScrolledText

from state_manager import handle_file_upload, stop_modbus_server_thread, start_modbus_server_thread
from file_server import run_flask_server
from utils import GuiLogger

text_widget = None
flask_thread = None

# This function gets called from the main.py to initialize the main popup
def run_gui():
    global text_widget, flask_thread

    root = Tk()
    root.title("Modbus Server Interface")

    # Fixed size and center
    width, height = 975, 450
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x, y = (sw - width) // 2, (sh - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")

    # GUI layout
    Label(root, text="Modbus Server Control", font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2, sticky='w')
    Button(root, text="Start Server", background="green", command=start_modbus_server_thread).grid(row=1, column=0, sticky='w')
    Button(root, text="Stop Server", background="red", command=stop_modbus_server_thread).grid(row=1, padx=5)
    # Button(root, text="Open FTP Port", background="grey", command=start_ftp_server_thread).grid(row=1, column=1, sticky='e')
    Button(root, text="Upload Python File", command=handle_file_upload).grid(row=1, column=2, padx=5)

    text_widget = ScrolledText(root, width=100, height=20)
    text_widget.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

    # Redirect stdout
    sys.stdout = GuiLogger(text_widget)

    # Start file server
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    root.mainloop()

if __name__ == "__main__":
    run_gui()