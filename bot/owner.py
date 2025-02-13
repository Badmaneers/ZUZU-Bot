import telebot
import os
import subprocess
import sys
import logging
import threading
from ai_response import process_ai_response
import time
import random

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
OWNER_ID = int(os.getenv("OWNER_ID"))


# ✅ Configure Logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Ensure OWNER_ID is an integer
OWNER_ID = int(OWNER_ID) if OWNER_ID else None

# ✅ Ensure groups.txt exists
GROUPS_FILE = "bot/groups.txt"
if not os.path.exists(GROUPS_FILE):
    open(GROUPS_FILE, "w").close()

# ✅ Fetch All Group IDs on Bot Start
def fetch_groups():
    """Fetch all group and supergroup IDs where the bot is present and save them to groups.txt without replacing old values."""
    try:
        updates = bot.get_updates(timeout=10)
        existing_group_ids = set()
        
        # ✅ Load existing groups to avoid duplicates
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, "r") as file:
                existing_group_ids.update(line.strip() for line in file.readlines())

        new_group_ids = set()
        
        for update in updates:
            chat = None
            if hasattr(update, "message") and update.message:
                chat = update.message.chat
            elif hasattr(update, "edited_message") and update.edited_message:
                chat = update.edited_message.chat
            elif hasattr(update, "channel_post") and update.channel_post:
                chat = update.channel_post.chat
            elif hasattr(update, "callback_query") and update.callback_query:
                chat = update.callback_query.message.chat

            if chat and chat.type in ["group", "supergroup", "channel"]:
                new_group_ids.add(str(chat.id))

        all_group_ids = existing_group_ids.union(new_group_ids)

        with open(GROUPS_FILE, "w") as file:
            for group_id in all_group_ids:
                file.write(f"{group_id}\n")
        
        logging.info(f"Fetched and saved {len(new_group_ids)} new group IDs. Total groups stored: {len(all_group_ids)}")
    except Exception as e:
        logging.error(f"Error fetching group IDs: {e}")



# ✅ Owner-Only Decorator
def owner_only(func):
    def wrapper(message):
        if message.from_user.id == OWNER_ID:
            return func(message)
        else:
            bot.reply_to(message, "🚫 You don’t have permission to use this command!")
    return wrapper

# ✅ Send AI-Generated Quotes to All Groups
def send_ai_generated_quote():
    """Send AI-generated motivation/roast to all registered groups."""
    try:
        with open(GROUPS_FILE, "r") as file:
            group_ids = [line.strip() for line in file.readlines()]
        
        if not group_ids:
            logging.warning("No groups found to send AI-generated messages.")
            return
        
        for group_id in group_ids:
            user_id = str(group_id)
            message = type("Message", (object,), {
                "text": "Give me an original motivational quote or a savage roast.",
                "message_id": 0,
                "from_user": type("User", (object,), {"id": group_id, "first_name": "Group Chat"})()
            })()
            process_ai_response(message, user_id, group_id)
    except Exception as e:
        logging.error(f"Error sending AI-generated messages: {e}")

# ✅ Schedule AI Messages Automatically
def schedule_ai_quotes():
    while True:
        send_ai_generated_quote()
        sleep_time = random.randint(3*60*60, 24*60*60)  # Random time between 2 hours and 24 hours
        time.sleep(sleep_time)

def start_ai_quote_scheduler():
    thread = threading.Thread(target=schedule_ai_quotes)
    thread.daemon = True
    thread.start()

# ✅ Register All Owner Commands
def register_owner_commands(bot):
    @bot.message_handler(commands=['broadcast'])
    @owner_only
    def broadcast(message):
        text = message.text.replace("/broadcast", "").strip()
        if not text:
            bot.reply_to(message, "📢 Please provide a message to broadcast.")
            return
        
        try:
            with open(GROUPS_FILE, "r") as file:
                group_ids = file.readlines()
            
            if not group_ids:
                bot.reply_to(message, "🚫 No groups found to broadcast.")
                return
            
            for group_id in group_ids:
                try:
                    bot.send_message(group_id.strip(), f"📢 Broadcast from the owner:\n\n{text}")
                    logging.info(f"Broadcast sent to {group_id.strip()}")
                except Exception as e:
                    logging.error(f"Failed to send to {group_id.strip()}: {e}")

            bot.reply_to(message, "✅ Broadcast sent successfully!")
        except FileNotFoundError:
            bot.reply_to(message, "🚫 `groups.txt` not found. Add groups first.")

    @bot.message_handler(commands=['restart'])
    @owner_only
    def restart_bot(message):
        bot.reply_to(message, "♻️ Restarting bot...")
        logging.info("Bot is restarting...")
        os.execv(sys.executable, ['python3'] + sys.argv)

    @bot.message_handler(commands=['logs'])
    @owner_only
    def fetch_logs(message):
        try:
            with open("bot.log", "r") as log_file:
                logs = log_file.readlines()[-10:]  # Get last 10 log lines
            bot.reply_to(message, f"📜 Last 10 log entries:\n\n" + "".join(logs))
        except Exception as e:
            logging.error(f"Error reading logs: {e}")
            bot.reply_to(message, f"❌ Error reading logs: {e}")

# ✅ Fetch groups when the bot starts
fetch_groups()
start_ai_quote_scheduler()