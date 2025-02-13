import telebot
import os
import subprocess
import sys
import logging

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
    """Fetch all groups where the bot is present and save them to groups.txt."""
    try:
        updates = bot.get_updates(timeout=10)  # ✅ Fetch latest updates
        group_ids = set()

        for update in updates:
            if update.message and update.message.chat.type in ["group", "supergroup"]:
                group_ids.add(update.message.chat.id)

        if group_ids:
            with open(GROUPS_FILE, "w") as file:
                for group_id in group_ids:
                    file.write(f"{group_id}\n")
            logging.info(f"Fetched and saved {len(group_ids)} group IDs.")
        else:
            logging.warning("No group IDs found.")
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
                    bot.send_message(group_id.strip(), f"📢 Broadcast from the Owner:\n\n{text}")
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
