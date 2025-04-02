import os
import json
import sqlite3
import signal
import sys
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========== Database Configuration ========== #
DB_FILE = "bot_memory.db"
DB_CONN = None
DB_LOCK = threading.Lock()

def init_db():
    """Initialize the database and create tables if they don't exist"""
    global DB_CONN
    with DB_LOCK:
        try:
            DB_CONN = sqlite3.connect(DB_FILE, check_same_thread=False)
            cursor = DB_CONN.cursor()
            
            # Create memory table with context-aware structure
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_memory (
                memory_key TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            DB_CONN.commit()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise e

# Initialize database on module import
init_db()

# ========== Memory Operations ========== #
def get_user_memory(memory_key):
    """Get memory for a specific user+context"""
    with DB_LOCK:
        try:
            cursor = DB_CONN.cursor()
            cursor.execute("SELECT messages FROM chat_memory WHERE memory_key = ?", (memory_key,))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result[0])
            return []
        except Exception as e:
            logging.error(f"Error getting memory for key {memory_key}: {e}")
            return []

def save_user_memory(memory_key, messages):
    """Save memory for a specific user+context"""
    with DB_LOCK:
        try:
            cursor = DB_CONN.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO chat_memory (memory_key, messages, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (memory_key, json.dumps(messages))
            )
            DB_CONN.commit()
            return True
        except Exception as e:
            logging.error(f"Error saving memory for key {memory_key}: {e}")
            DB_CONN.rollback()
            return False

def get_all_memory_keys():
    """Get all memory keys in the database"""
    with DB_LOCK:
        try:
            cursor = DB_CONN.cursor()
            cursor.execute("SELECT memory_key FROM chat_memory")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting memory keys: {e}")
            return []

# ========== Memory Management Class ========== #
class MemoryManager:
    def __init__(self):
        self.memory_cache = {}
        
    def get(self, user_id, chat_id=None, chat_type="private", default=None):
        """Get memory with context awareness
           - For private chats: user-specific memory
           - For groups: shared group memory"""
        if chat_type != "private" and chat_id:
            # Group chats use shared memory: "group:{chat_id}"
            memory_key = f"group:{chat_id}"
        else:
            # Private chats use user-specific memory: "{user_id}:dm"
            memory_key = f"{user_id}:dm"
            
        if memory_key not in self.memory_cache:
            self.memory_cache[memory_key] = get_user_memory(memory_key)
        return self.memory_cache[memory_key] if self.memory_cache[memory_key] else default or []
    
    def save(self, memory_key):
        """Save a specific memory context"""
        if memory_key in self.memory_cache:
            return save_user_memory(memory_key, self.memory_cache[memory_key])
        return False
    
    def save_all(self):
        """Save all memories in the cache"""
        success = True
        for memory_key in list(self.memory_cache.keys()):
            if not self.save(memory_key):
                success = False
        return success
    
    def __getitem__(self, key_info):
        """Support for both old and new access methods"""
        if isinstance(key_info, tuple) and len(key_info) >= 2:
            # New format: (user_id, chat_id, chat_type)
            user_id, chat_id = key_info[0], key_info[1]
            chat_type = key_info[2] if len(key_info) > 2 else "private"
            
            # Create appropriate memory key
            if chat_type != "private" and chat_id:
                memory_key = f"group:{chat_id}"
            else:
                memory_key = f"{user_id}:dm"
                
            return self.memory_cache.get(memory_key, [])
        else:
            # Old format: just user_id (assume DMs)
            memory_key = f"{key_info}:dm"
            return self.memory_cache.get(memory_key, [])
    
    def __setitem__(self, key_info, messages):
        """Support for both old and new access methods"""
        if isinstance(key_info, tuple) and len(key_info) >= 2:
            # New format: (user_id, chat_id, chat_type)
            user_id, chat_id = key_info[0], key_info[1]
            chat_type = key_info[2] if len(key_info) > 2 else "private"
            
            # Create appropriate memory key
            if chat_type != "private" and chat_id:
                memory_key = f"group:{chat_id}"
            else:
                memory_key = f"{user_id}:dm"
        else:
            # Old format: just user_id (assume DMs)
            memory_key = f"{key_info}:dm"
            
        self.memory_cache[memory_key] = messages

# Create global memory manager instance
chat_memory = MemoryManager()

# Backward compatibility function
def save_memory():
    """Save all memory to database"""
    return chat_memory.save_all()  # This was calling save_all() which didn't exist

# ========== Migrate from old format ========== #
def migrate_from_json():
    """Migrate data from old JSON format to SQLite"""
    old_file = "chat_memory.json"
    if os.path.exists(old_file):
        try:
            logging.info("Migrating old memory data to SQLite...")
            with open(old_file, "r", encoding="utf-8") as file:
                raw_data = file.read().strip()
                
            if raw_data:
                try:
                    # Try to parse the old format
                    old_data = json.loads(raw_data)
                    
                    # Transfer to new database with context separation
                    for user_id, messages in old_data.items():
                        # Put old memories in both DM and group contexts for continuity
                        save_user_memory(f"{user_id}:dm", messages)
                    
                    # Rename the old file as backup
                    os.rename(old_file, f"{old_file}.bak")
                    logging.info("Migration completed successfully")
                except Exception as e:
                    logging.error(f"Error during migration: {e}")
        except Exception as e:
            logging.error(f"Failed to open old memory file: {e}")

# Try to migrate on first run
try:
    migrate_from_json()
except Exception as e:
    logging.error(f"Migration error: {e}")

# ========== Auto-Save Memory Every 60 Seconds ========== #
def auto_save_memory():
    while True:
        try:
            success = save_memory()
            if success:
                logging.info("Auto-saved memory to database")
            else:
                logging.warning("Failed to auto-save memory")
        except Exception as e:
            logging.error(f"Error in auto-save: {e}")
        time.sleep(60)  # Wait 60 seconds before saving again

# Start auto-save thread
auto_save_thread = threading.Thread(target=auto_save_memory, daemon=True)
auto_save_thread.start()

# ========== Cleanup ========== #
def handle_exit(signal_number, frame):
    logging.info("Saving memory before exit...")
    save_memory()
    if DB_CONN:
        DB_CONN.close()
    logging.info("Database connection closed")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

logging.info("Memory system initialized with SQLite backend")
