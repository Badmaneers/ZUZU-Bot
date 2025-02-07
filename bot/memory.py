import os
import json
import zlib
import base64

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

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            file.write(compress_data(chat_memory))
    except Exception as e:
        print(f"Error saving memory: {e}")

chat_memory = load_memory()