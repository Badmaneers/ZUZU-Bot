import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="bot.log",
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

# AI Configuration
OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY", required=True)
AI_MODEL = get_env("AI_MODEL", default="cognitivecomputations/dolphin-mistral-24b-venice-edition:free")
TEMPERATURE = float(get_env("AI_TEMPERATURE", default="0.7"))
TOP_P = float(get_env("AI_TOP_P", default="0.9"))
MAX_RETRIES = int(get_env("AI_MAX_RETRIES", default="3"))
MEMORY_LIMIT = int(get_env("MEMORY_LIMIT", default="10"))

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, "prompt.txt")
BADWORDS_FILE = os.path.join(BASE_DIR, "badwords.txt")
ROASTS_FILE = os.path.join(BASE_DIR, "roasts.txt")
MOTIVATIONS_FILE = os.path.join(BASE_DIR, "motivations.txt")
