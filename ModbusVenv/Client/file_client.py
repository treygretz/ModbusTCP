import requests
import os
from config import TARGET_FILENAME, FLASK_HOST, FLASK_PORT

TEMP_SCRIPT = "client_script_new.py"

def download_update():
    try:
        print("Downloading updated script...")
        r = requests.get("http://" + FLASK_HOST + ":" + str(FLASK_PORT) + "/scripts/client_script.py")
        r.raise_for_status()

        with open(TEMP_SCRIPT, "wb") as f:
            f.write(r.content)
        
        print("Replacing old script...")
        os.replace(TEMP_SCRIPT, TARGET_FILENAME)  # Overwrites the current file safely
        print("Update complete. Please restart the script manually.")
    except Exception as e:
        print(f"Update failed: {e}")

download_update()
