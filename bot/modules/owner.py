import telebot
import os
import subprocess
import sys
import logging
import threading
from core.ai_response import process_ai_response
import time
import random
from modules.moderations import is_admin
from modules.notes import load_notes, save_notes_to_file
from config import BASE_DIR, OWNER_ID
from core.bot_instance import bot

# Define paths
GROUPS_FILE = os.path.join(os.path.dirname(BASE_DIR), "bot", "groups.txt")
NOTES_DIR = os.path.join(os.path.dirname(BASE_DIR), "notes")

# Ensure groups.txt exists
if not os.path.exists(GROUPS_FILE):
    with open(GROUPS_FILE, "w") as f:
        pass

# ✅ Save Group ID When Bot Joins a Group
def save_group_id(message):
    """Saves group ID when the bot is added to a new group."""
    chat_id = str(message.chat.id)
    
    try:
        with open(GROUPS_FILE, "r") as file:
            existing_groups = {line.strip() for line in file.readlines()}
    except FileNotFoundError:
        existing_groups = set()
    
    if chat_id not in existing_groups:
        with open(GROUPS_FILE, "a") as file:
            file.write(f"{chat_id}\n")
        logging.info(f"Added new group ID: {chat_id}")

# ✅ Fetch and Save IDs from Existing Joined Groups
def fetch_existing_groups():
    """Fetches groups the bot is already a member of and saves their IDs."""
    try:
        # Note: get_updates is not reliable for fetching past groups on restart if offset consumed
        # detailed implementation requires persistent storage, but we'll adapt existing logic
        if os.path.exists(GROUPS_FILE):
           return # Skip to avoid blocking startup if file exists
           
        logging.info("Groups file checked.")
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
            return
        
        prompt = "Give me an original motivational quote or a savage roast."
        
        for group_id in group_ids:
            if not group_id: continue
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
        sleep_time = random.randint(3*60*60, 24*60*60)
        send_ai_generated_quote()
        time.sleep(sleep_time)

def start_ai_quote_scheduler():
    thread = threading.Thread(target=schedule_ai_quotes)
    thread.daemon = True
    thread.start()

# ✅ Register All Owner Commands
def register_owner_commands(bot):
    # Register the save_group_id handler here
    bot.register_message_handler(save_group_id, content_types=['new_chat_members'])

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
        # Simple check if this is a reply to the import command could be added, 
        # but for now we trust the user knows what they are doing or we check file name closely.
        if not message.document.file_name.endswith(".json"):
             # Ignore non-json files or logging
             return

        # Ideally, we should check if the user is owner/admin before accepting override
        if not is_admin(message.chat.id, message.from_user.id):
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

            # Reload notes after import (optional if load_notes reads from file every time)
            load_notes(chat_id)
            bot.reply_to(message, f"✅ Notes imported successfully for group {chat_id}!")
        except Exception as e:
            bot.reply_to(message, f"❌ Error importing notes: {e}")

    @bot.message_handler(commands=['broadcast'])
    def broadcast(message):
      """Broadcasts a message to all groups with an optional flag to remove header."""
      # Check owner inside
      if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "🚫 Only owner can use this command!")
        return
        
      text = message.text.replace("/broadcast", "").strip()
      if not text:
        bot.reply_to(message, "📢 Please provide a message to broadcast.")
        return
    
      remove_header = "--no-header" in text
      if remove_header:
        text = text.replace("--no-header", "").strip()
    
      try:
        with open(GROUPS_FILE, "r") as file:
            group_ids = file.readlines()
        
        if not group_ids:
            bot.reply_to(message, "🚫 No groups found to broadcast.")
            return
        
        for group_id in group_ids:
            gid = group_id.strip()
            if not gid: continue
            try:
                broadcast_text = text if remove_header else f"📢 Broadcast from the owner:\n\n{text}"
                bot.send_message(gid, broadcast_text)
            except Exception as e:
                logging.error(f"Failed to send to {gid}: {e}")

        bot.reply_to(message, "✅ Broadcast sent successfully!")
      except FileNotFoundError:
        bot.reply_to(message, "🚫 `groups.txt` not found.")

    @bot.message_handler(commands=['restart'])
    @owner_only
    def restart_bot(message):
        bot.reply_to(message, "♻️ Restarting bot...")
        logging.info("Bot is restarting...")
        # Start new process then exit
        os.execv(sys.executable, ['python3'] + sys.argv)

    @bot.message_handler(commands=['logs'])
    @owner_only
    def fetch_logs(message):
        try:
            log_path = os.path.join(os.path.dirname(BASE_DIR), "bot.log") # Assuming log in root
            if not os.path.exists(log_path):
                 log_path = "bot.log"
                 
            with open(log_path, "r") as log_file:
                logs = log_file.readlines()[-15:]  # Get last 15 log lines
            
            # chunking if needed
            msg = "📜 Last logs:\n\n" + "".join(logs)
            if len(msg) > 4000: msg = msg[-4000:]
            bot.reply_to(message, msg)
        except Exception as e:
            bot.reply_to(message, f"❌ Error reading logs: {e}")
    
    @bot.message_handler(commands=['register'])
    def register_group(message):
        chat_id = str(message.chat.id)
        # Append only if not exists
        try:
            lines = []
            if os.path.exists(GROUPS_FILE):
                with open(GROUPS_FILE, "r") as f: lines = f.read().splitlines()
            
            if chat_id not in lines:
                with open(GROUPS_FILE, "a") as file:
                    file.write(f"{chat_id}\n")
                bot.reply_to(message, "✅ This group has been registered successfully!")
            else:
                bot.reply_to(message, "✅ Already registered.")
        except Exception as e:
            bot.reply_to(message, f"Error: {e}")

# ✅ Initialize Scheduler
start_ai_quote_scheduler()
