#This script simply checks if there was an update to a Client script
import os
import shutil

SOURCE_FILEPATH = "/home/oishii/Python/Barcode_Thread_Worker.py"
DESTINATION_FILEPATH = "/home/oishii/Python/ModbusTCPVenv/ModbusTCP/Client/Barcode_Thread_Worker.py"


def overwriteFile():
	if os.path.exists(SOURCE_FILEPATH):
		shutil.copy2(SOURCE_FILEPATH, DESTINATION_FILEPATH)
		print("File updated!\n")

	else:
		print("No Updates Avialable...\n")

if __name__ == "__main__":
	overwriteFile()
