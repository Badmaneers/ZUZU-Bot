import telebot
import os
import subprocess
import sys
import logging
import threading
from ai_response import process_ai_response
import time
import random
from moderations import is_admin
from notes import load_notes, save_notes
from config import BASE_DIR, OWNER_ID
from bot_instance import bot

GROUPS_FILE = os.path.join(os.path.dirname(BASE_DIR), "bot", "groups.txt") # Assuming bot/groups.txt relative to root or make it cleaner

# Ensure groups.txt exists
if not os.path.exists(GROUPS_FILE):
    with open(GROUPS_FILE, "w") as f:
        pass

# ✅ Save Group ID When Bot Joins a Group
# This needs to be registered!
def save_group_id(message):
    """Saves group ID when the bot is added to a new group."""
    chat_id = str(message.chat.id)
    
    # ✅ Read existing group IDs
    try:
        with open(GROUPS_FILE, "r") as file:
            existing_groups = {line.strip() for line in file.readlines()}
    except FileNotFoundError:
        existing_groups = set()
    
    # ✅ Add new group ID if not already in the file
    if chat_id not in existing_groups:
        with open(GROUPS_FILE, "a") as file:
            file.write(f"{chat_id}\n")
        logging.info(f"Added new group ID: {chat_id}")
    else:
        logging.info(f"Group ID {chat_id} already exists. No action taken.")

def register_owner_commands(bot):
    # Register the save_group_id handler here
    bot.register_message_handler(save_group_id, content_types=['new_chat_members'])



# ✅ Fetch and Save IDs from Existing Joined Groups
def fetch_existing_groups():
    """Fetches groups the bot is already a member of and saves their IDs."""
    try:
        updates = bot.get_updates(timeout=9999*2)
        existing_group_ids = set()

        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, "r") as file:
                existing_group_ids.update(line.strip() for line in file.readlines())

        new_group_ids = set()

        for update in updates:
            if hasattr(update, "message") and update.message:
                chat = update.message.chat
                if chat and chat.type in ["group", "supergroup", "channel"]:
                    new_group_ids.add(str(chat.id))
        
        all_group_ids = existing_group_ids.union(new_group_ids)

        with open(GROUPS_FILE, "w") as file:
            for group_id in all_group_ids:
                file.write(f"{group_id}\n")
        
        logging.info(f"Fetched and saved {len(new_group_ids)} existing group IDs. Total groups stored: {len(all_group_ids)}")
    except Exception as e:
        logging.error(f"Error fetching existing group IDs: {e}")

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
        
        prompt = "Give me an original motivational quote or a savage roast."
        
        for group_id in group_ids:
            try:
                # Use the direct method with group_id and message_text parameters
                process_ai_response(None, group_id, prompt)
                logging.info(f"AI quote request sent to group {group_id}")
            except Exception as e:
                logging.error(f"Failed to send AI quote to group {group_id}: {e}")
                
    except Exception as e:
        logging.error(f"Error sending AI-generated messages: {e}")

# ✅ Schedule AI Messages Automatically
def schedule_ai_quotes():
    while True:
        sleep_time = random.randint(3*60*60, 24*60*60)  # Random time between 3 hours and 24 hours
        send_ai_generated_quote()
        time.sleep(sleep_time)

def start_ai_quote_scheduler():
    thread = threading.Thread(target=schedule_ai_quotes)
    thread.daemon = True
    thread.start()

# ✅ Register All Owner Commands
def register_owner_commands(bot):
    @bot.message_handler(commands=['export'])
    @owner_only
    def export_notes(message):
        """Exports the notes of a group as a .json file."""
        chat_id = str(message.chat.id)
        notes_file = os.path.join(NOTES_DIR, f"{chat_id}.json")
        
        if os.path.exists(notes_file):
            try:
                with open(notes_file, "rb") as file:
                    bot.send_document(message.chat.id, file, caption=f"📂 Here is the exported notes for group {chat_id}.")
            except Exception as e:
                bot.reply_to(message, f"❌ Error exporting notes: {e}")
        else:
            bot.reply_to(message, "❌ No notes found for this group!")

    @bot.message_handler(commands=['import'])
    @owner_only
    def request_import(message):
        """Instructs the user to upload a `.json` file."""
        bot.reply_to(message, "📥 Please send a `.json` file to import notes.")

    @bot.message_handler(content_types=['document'])
    def import_notes(message):
        """Imports a new notes file for the group when uploaded via /import."""
        file_name = message.document.file_name

        if not file_name.endswith(".json"):
            bot.reply_to(message, "⚠️ Only `.json` files are allowed for import.")
            return

        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        try:
            chat_id = str(message.chat.id)
            notes_file = os.path.join(NOTES_DIR, f"{chat_id}.json")
            
            # ✅ Save the uploaded file as the group's notes
            with open(notes_file, "wb") as file:
                file.write(downloaded_file)

            # Reload notes after import
            load_notes(chat_id)
            bot.reply_to(message, f"✅ Notes imported successfully for group {chat_id}!")
        except Exception as e:
            bot.reply_to(message, f"❌ Error importing notes: {e}")

    @bot.message_handler(commands=['broadcast'])
    # ✅ Broadcast Message with Optional Header
    def broadcast(message):
      """Broadcasts a message to all groups with an optional flag to remove header."""
      text = message.text.replace("/broadcast", "").strip()
      chat_id = message.chat.id
      user_id = message.from_user.id
      if not is_admin(chat_id, user_id):
        bot.reply_to(message, "🚫 Only admins can use this command!")
        return
    
      if not text:
        bot.reply_to(message, "📢 Please provide a message to broadcast.")
        return
    
      remove_header = False
      if "--no-header" in text:
        remove_header = True
        text = text.replace("--no-header", "").strip()
    
      try:
        with open(GROUPS_FILE, "r") as file:
            group_ids = file.readlines()
        
        if not group_ids:
            bot.reply_to(message, "🚫 No groups found to broadcast.")
            return
        
        for group_id in group_ids:
            try:
                broadcast_text = text if remove_header else f"📢 Broadcast from the owner:\n\n{text}"
                bot.send_message(group_id.strip(), broadcast_text)
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
    
    @bot.message_handler(commands=['register'])
    def register_group(message):
        chat_id = str(message.chat.id)
        with open("bot/groups.txt", "a") as file:
            if chat_id not in open("bot/groups.txt").read():
                file.write(f"{chat_id}\n")
        bot.reply_to(message, "✅ This group has been registered successfully!")

# ✅ Fetch groups when the bot starts
fetch_existing_groups()
start_ai_quote_scheduler()
