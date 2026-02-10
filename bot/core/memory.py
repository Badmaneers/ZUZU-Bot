import os
import json
import sqlite3
import signal
import sys
import threading
import time
import logging
from cryptography.fernet import Fernet
from config import MEMORY_ENCRYPTION_KEY

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ========== Database Configuration ========== #
DB_FILE="state/bot_memory.db"
DB_CONN = None
DB_LOCK = threading.Lock()
CIPHER = Fernet(MEMORY_ENCRYPTION_KEY)

def init_db():
    """Initialize the database and create tables if they don't exist"""
    global DB_CONN
    with DB_LOCK:
        try:
            DB_CONN = sqlite3.connect(DB_FILE, check_same_thread=False)
            cursor = DB_CONN.cursor()
            
            # Enable WAL mode for better concurrency and reliability
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
            # Create memory table with context-aware structure
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_memory (
                memory_key TEXT PRIMARY KEY,
                messages TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            DB_CONN.commit()
            logging.info("Database initialized successfully with WAL mode")
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise e

# Initialize database on module import
init_db()

# ========== Memory Management Class ========== #
class MemoryManager:
    def __init__(self):
        self.memory_cache = {}
        self.dirty_keys = set()
        self.cache_lock = threading.Lock()
        
    def _get_key(self, key_info):
        """Helper to resolve memory key from various input formats"""
        if isinstance(key_info, tuple) and len(key_info) >= 2:
            # New format: (user_id, chat_id, chat_type)
            user_id, chat_id = key_info[0], key_info[1]
            chat_type = key_info[2] if len(key_info) > 2 else "private"
            
            if chat_type != "private" and chat_id:
                return f"group:{chat_id}"
            else:
                return f"{user_id}:dm"
        elif isinstance(key_info, str):
            # Already a key string? or old ID?
            if ":" in key_info: return key_info
            return f"{key_info}:dm"
        return str(key_info)

    def get(self, user_id, chat_id=None, chat_type="private", default=None):
        """Get memory with context awareness"""
        if chat_type != "private" and chat_id:
            memory_key = f"group:{chat_id}"
        else:
            memory_key = f"{user_id}:dm"
            
        with self.cache_lock:
            if memory_key not in self.memory_cache:
                # Load from DB if not in cache
                try:
                    with DB_LOCK:
                        cursor = DB_CONN.cursor()
                        cursor.execute("SELECT messages FROM chat_memory WHERE memory_key = ?", (memory_key,))
                        result = cursor.fetchone()
                        if result:
                            # Decrypt data
                            try:
                                decrypted_data = CIPHER.decrypt(result[0].encode()).decode()
                                self.memory_cache[memory_key] = json.loads(decrypted_data)
                            except Exception:
                                # Fallback for unencrypted data (useful during migration)
                                try:
                                    self.memory_cache[memory_key] = json.loads(result[0])
                                except:
                                    self.memory_cache[memory_key] = []
                        else:
                            self.memory_cache[memory_key] = []
                except Exception as e:
                    logging.error(f"Error loading memory for {memory_key}: {e}")
                    self.memory_cache[memory_key] = []
                    
            return self.memory_cache[memory_key]
    
    def commit(self):
        """Save only modified (dirty) memories to database in a single transaction"""
        with self.cache_lock:
            if not self.dirty_keys:
                return True
            
            keys_to_save = list(self.dirty_keys)
            self.dirty_keys.clear()

        # Perform DB operations outside cache lock to minimize blocking
        with DB_LOCK:
            try:
                cursor = DB_CONN.cursor()
                cursor.execute("BEGIN TRANSACTION")
                
                for key in keys_to_save:
                    # Check cache for data (acquire cache lock briefly)
                    with self.cache_lock:
                        messages = self.memory_cache.get(key)
                    
                    if messages is not None:
                        # Encrypt data before saving
                        encrypted_data = CIPHER.encrypt(json.dumps(messages).encode()).decode()
                        cursor.execute(
                            "INSERT OR REPLACE INTO chat_memory (memory_key, messages, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP)",
                            (key, encrypted_data)
                        )
                
                DB_CONN.commit()
                # logging.info(f"Committed {len(keys_to_save)} modified memory contexts to database.")
                return True
            except Exception as e:
                logging.error(f"Error verifying memory batch commit: {e}")
                DB_CONN.rollback()
                # Re-add keys to dirty set so we don't lose data
                with self.cache_lock:
                    self.dirty_keys.update(keys_to_save)
                return False
    
    def __getitem__(self, key_info):
        """Support for legacy access"""
        memory_key = self._get_key(key_info)
        with self.cache_lock:
            if memory_key not in self.memory_cache:
                # Trigger a load via get logic manually or reuse
                # Simple lazy load:
                try:
                    with DB_LOCK:
                        cursor = DB_CONN.cursor()
                        cursor.execute("SELECT messages FROM chat_memory WHERE memory_key = ?", (memory_key,))
                        res = cursor.fetchone()
                        if res:
                            try:
                                self.memory_cache[memory_key] = json.loads(CIPHER.decrypt(res[0].encode()).decode())
                            except:
                                self.memory_cache[memory_key] = json.loads(res[0])
                        else:
                            self.memory_cache[memory_key] = []
                except:
                   self.memory_cache[memory_key] = []
                   
            return self.memory_cache[memory_key]
    
    def __setitem__(self, key_info, messages):
        """Update memory and mark as dirty"""
        memory_key = self._get_key(key_info)
        with self.cache_lock:
            self.memory_cache[memory_key] = messages
            self.dirty_keys.add(memory_key)

# Create global memory manager instance
chat_memory = MemoryManager()

# Backward compatibility function
def save_memory():
    """Trigger a commit of dirty memory keys"""
    return chat_memory.commit()

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
                    old_data = json.loads(raw_data)
                    # Use the manager to insert and mark dirty
                    for user_id, messages in old_data.items():
                        # We don't know if these are groups or DMs easily, 
                        # but old bot mainly did DMs or everything mixed.
                        # We'll save as DM for safety.
                        chat_memory[f"{user_id}:dm"] = messages
                    
                    chat_memory.commit()
                    
                    os.rename(old_file, f"{old_file}.bak")
                    logging.info("Migration completed successfully")
                except Exception as e:
                    logging.error(f"Error during migration: {e}")
        except Exception as e:
            logging.error(f"Failed to open old memory file: {e}")

try:
    migrate_from_json()
except Exception as e:
    logging.error(f"Migration error: {e}")

# ========== Auto-Save Memory ========== #
def auto_save_memory():
    while True:
        try:
            chat_memory.commit()
        except Exception as e:
            logging.error(f"Error in auto-save: {e}")
        time.sleep(60)

# Start auto-save thread
auto_save_thread = threading.Thread(target=auto_save_memory, daemon=True)
auto_save_thread.start()

# ========== Cleanup ========== #
def handle_exit(signal_number, frame):
    logging.info("Saving memory before exit...")
    chat_memory.commit()
    if DB_CONN:
        DB_CONN.close()
    logging.info("Database connection closed")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

logging.info("Memory system initialized with SQLite (WAL optimized)")
