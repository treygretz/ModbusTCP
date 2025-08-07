# file_server.py
import os
from flask import Flask, send_from_directory
from config import UPLOAD_DIR, TARGET_FILENAME, FLASK_HOST, FLASK_PORT

flask_app = Flask(__name__)

@flask_app.route('/file', methods=['GET'])
def get_file():
    file_path = os.path.join(UPLOAD_DIR, TARGET_FILENAME)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_from_directory(UPLOAD_DIR, TARGET_FILENAME, as_attachment=True)

def run_flask_server():
    print(f"Flask server running at http://{FLASK_HOST}:{FLASK_PORT}/file")
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT)