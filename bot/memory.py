import os
import json
import zlib
import base64
import signal
import sys
import threading
import time

# ========== Memory Storage ========== #
MEMORY_FILE = "chat_memory.json"

def compress_data(data):
    return base64.b64encode(zlib.compress(json.dumps(data).encode())).decode()

def decompress_data(data):
    return json.loads(zlib.decompress(base64.b64decode(data)).decode())

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                raw_data = file.read().strip()
                if raw_data:
                    return decompress_data(raw_data)
        except Exception as e:
            print(f"Error loading memory: {e}")
    return {}

chat_memory = load_memory()

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            file.write(compress_data(chat_memory))
    except Exception as e:
        print(f"Error saving memory: {e}")

# ========== Auto-Save Memory Every 25 Seconds ========== #
def auto_save_memory():
    while True:
        save_memory()
        print("Auto-saved memory.")
        time.sleep(60)  # Wait 60 seconds before saving again

# Start auto-save thread
auto_save_thread = threading.Thread(target=auto_save_memory, daemon=True)
auto_save_thread.start()

# ========== Start Bot ========== #
def handle_exit(signal_number, frame):
    print("Saving memory before exit...")
    save_memory()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
