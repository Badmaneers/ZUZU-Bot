import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
LOG_FILE = "bot.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_env(key, default=None, required=False):
    value = os.getenv(key, default)
    if required and not value:
        logging.critical(f"{key} is not set. Exiting...")
        raise ValueError(f"Error: {key} is not set. Please check your .env file.")
    return value

# Bot Configuration
BOT_TOKEN = get_env("BOT_TOKEN", required=True)
OWNER_ID = int(get_env("OWNER_ID", default="0"))
ADMIN_PASSWORD = get_env("ADMIN_PASSWORD", default="admin123")
FLASK_SECRET_KEY = get_env("FLASK_SECRET_KEY", default="supersecretkey")

# Memory Security
MEMORY_ACCESS_PASSWORD = get_env("MEMORY_ACCESS_PASSWORD", default="mem123")
MEMORY_ENCRYPTION_KEY = get_env("MEMORY_ENCRYPTION_KEY", default="J5TPb34dRRw2z-YA_40rtyaZ9jfLxMeGqdq14MF5Ypg=")

# AI Configuration
OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY", required=True)
AI_MODEL = get_env("AI_MODEL", default="cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
TEMPERATURE = float(get_env("AI_TEMPERATURE", default="0.7"))
TOP_P = float(get_env("AI_TOP_P", default="0.9"))
MAX_RETRIES = int(get_env("AI_MAX_RETRIES", default="3"))
MEMORY_LIMIT = int(get_env("MEMORY_LIMIT", default="10"))

# Web Configuration
HOST_DOMAIN = get_env("HOST_DOMAIN", default=None)

# Paths
# BASE_DIR is now .../bot
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

DATA_DIR = os.path.join(ROOT_DIR, "data")
STATE_DIR = os.path.join(ROOT_DIR, "state")

# Files
PROMPT_FILE = os.path.join(DATA_DIR, "prompt.txt")
BADWORDS_FILE = os.path.join(DATA_DIR, "badwords.txt")
FUN_FILE = os.path.join(DATA_DIR, "fun.json")

# State Files
GROUPS_FILE = os.path.join(STATE_DIR, "groups.txt")
MOD_CONFIG_FILE = os.path.join(STATE_DIR, "moderation_config.json")
NOTES_DIR = os.path.join(STATE_DIR, "notes")

# Ensure state directories exist
if not os.path.exists(STATE_DIR):
    os.makedirs(STATE_DIR)
if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
