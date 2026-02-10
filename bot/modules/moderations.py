import telebot
import random
import time
import json
import os
import threading
from datetime import datetime, timedelta
from core.helper import load_from_file
from core.bot_instance import bot
from config import BADWORDS_FILE

muted_users = {}
user_messages = {}
message_timestamps = {}
user_warnings = {}

# Load global badwords (defaults)
global_badwords = load_from_file(BADWORDS_FILE)

# Configuration for Welcome/Moderation settings
MOD_CONFIG_FILE = "moderation_config.json"

def load_mod_config():
    if not os.path.exists(MOD_CONFIG_FILE):
        return {}
    try:
        with open(MOD_CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_mod_config(config):
    with open(MOD_CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_effective_badwords(chat_id):
    conf = load_mod_config()
    chat_conf = conf.get(str(chat_id), {})
    if "badwords" in chat_conf:
        return chat_conf["badwords"]
    return global_badwords

def is_admin(chat_id, user_id):
    """Check if a user is an admin."""
    try:
        chat_admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == user_id for admin in chat_admins)
    except Exception:
        return False

def bot_is_admin(chat_id):
    """Check if the bot is admin."""
    try:
        if chat_id > 0: # User ID (DMs)
            return False
            
        bot_id = bot.get_me().id
        chat_admins = bot.get_chat_administrators(chat_id)
        return any(admin.user.id == bot_id for admin in chat_admins)
    except Exception:
        return False

def check_perm(message):
    """Checks if command user is admin."""
    if message.chat.type == "private":
        return True
    return is_admin(message.chat.id, message.from_user.id)

def register_moderation_handlers(bot):
    
    # --- Welcome Handling ---
    @bot.message_handler(content_types=['new_chat_members'])
    def greet_new_member(message):
        chat_id = str(message.chat.id)
        try:
             # Skip if bot not admin or can't write (optional check, but good for logs)
             pass 
        except:
            return

        conf = load_mod_config()
        chat_conf = conf.get(chat_id, {})
        
        # Check if welcome is disabled
        if not chat_conf.get("welcome_enabled", True):
            return

        new_members = message.new_chat_members
        custom_text = chat_conf.get("welcome_text")

        for user in new_members:
            if user.id == bot.get_me().id:
                bot.reply_to(message, "💅 The queen has arrived. Make way!")
                continue

            name = user.first_name
            username = f"@{user.username}" if user.username else name
            
            if custom_text:
                # Rose-like placeholders: {name}, {username}, {chatname}
                welcome_msg = custom_text.format(
                    name=name,
                    username=username,
                    chatname=message.chat.title,
                    id=user.id
                )
            else:
                defaults = [
                    f"🎉 Hey {name}, welcome to the jungle!",
                    f"🔥 {name} just joined. Play nice!",
                    f"👀 {name} is here. Don't be shy."
                ]
                welcome_msg = random.choice(defaults)

            try:
                bot.send_message(message.chat.id, welcome_msg)
            except Exception as e:
                print(f"Failed to send welcome: {e}")

    # --- Configuration Commands ---
    @bot.message_handler(commands=['welcome'])
    def toggle_welcome(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return

        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/welcome <on/off>`")
            return
            
        state = args[1].lower()
        enable = state == "on"
        
        conf = load_mod_config()
        chat_id = str(message.chat.id)
        if chat_id not in conf: conf[chat_id] = {}
        
        conf[chat_id]["welcome_enabled"] = enable
        save_mod_config(conf)
        
        bot.reply_to(message, f"✅ Welcome messages {'enabled' if enable else 'disabled'}.")

    @bot.message_handler(commands=['setwelcome'])
    def set_welcome(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return

        text = message.text.replace("/setwelcome", "", 1).strip()
        if not text:
            bot.reply_to(message, "⚠️ Usage: `/setwelcome <message>`\nVariables: `{name}`, `{username}`, `{chatname}`, `{id}`")
            return
            
        conf = load_mod_config()
        chat_id = str(message.chat.id)
        if chat_id not in conf: conf[chat_id] = {}
        
        conf[chat_id]["welcome_text"] = text
        save_mod_config(conf)
        
        bot.reply_to(message, "✅ Custom welcome message saved!")

    # --- Moderation Actions ---
    @bot.message_handler(commands=['kick'])
    def kick_user(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return
        
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Reply to someone to kick them.")
            return
            
        target = message.reply_to_message.from_user
        if is_admin(message.chat.id, target.id):
             bot.reply_to(message, "🚫 I can't kick an admin.")
             return
             
        try:
            bot.unban_chat_member(message.chat.id, target.id) # Unban immediately kicks without perma-ban
            bot.reply_to(message, f"👢 {target.first_name} has been kicked.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed: {e}")

    @bot.message_handler(commands=['ban'])
    def ban_user(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return
            
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Reply to someone to ban them.")
            return

        target = message.reply_to_message.from_user
        if is_admin(message.chat.id, target.id):
             bot.reply_to(message, "🚫 I can't ban an admin.")
             return
             
        try:
            bot.ban_chat_member(message.chat.id, target.id)
            bot.reply_to(message, f"⛔ {target.first_name} banned.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed: {e}")

    @bot.message_handler(commands=['mute'])
    def mute_user(message):
        if not check_perm(message):
            return # Silent fail if not admin or reply?
        
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Reply to user.")
            return
            
        target = message.reply_to_message.from_user
        if is_admin(message.chat.id, target.id):
            bot.reply_to(message, "🚫 Can't mute admins.")
            return
            
        duration = 300 # 5 min default
        args = message.text.split()
        if len(args) > 1 and args[1].isdigit():
            duration = int(args[1]) * 60
            
        try:
            bot.restrict_chat_member(message.chat.id, target.id, until_date=time.time()+duration, can_send_messages=False)
            bot.reply_to(message, f"🤐 {target.first_name} muted for {duration//60} mins.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed: {e}")

    @bot.message_handler(commands=['unmute'])
    def unmute_user(message):
        if not check_perm(message): return
        
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Reply to user.")
            return
            
        target = message.reply_to_message.from_user
        try:
            bot.restrict_chat_member(message.chat.id, target.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
            bot.reply_to(message, f"🗣️ {target.first_name} unmuted.")
        except Exception as e:
            bot.reply_to(message, f"❌ Failed: {e}")

    @bot.message_handler(commands=['purge'])
    def purge_messages(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return
            
        try:
            args = message.text.split()
            count = int(args[1]) if len(args) > 1 else 10
            if count > 100: count = 100 # Safe limit
            
            message_ids = [k for k in range(message.message_id - count, message.message_id + 1)]
            # Needs delete_messages (plural) or loop
            # Telebot might not support plural delete easily in older versions, loop is safer
            for mid in message_ids:
                try:
                    bot.delete_message(message.chat.id, mid)
                except:
                    pass
            
            confirm = bot.send_message(message.chat.id, f"🗑️ Purged {count} messages.")
            time.sleep(3)
            bot.delete_message(message.chat.id, confirm.message_id)
        except Exception as e:
             bot.reply_to(message, f"❌ Error: {e}")

    @bot.message_handler(commands=['pin'])
    def pin_message(message):
        if not check_perm(message): return
        
        if not message.reply_to_message:
            bot.reply_to(message, "⚠️ Reply to a message to pin it.")
            return
            
        try:
            bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
            bot.reply_to(message, "📌 Pinned.")
        except Exception as e:
             bot.reply_to(message, f"❌ Failed: {e}")
             
    @bot.message_handler(commands=['addbw', 'filter'])
    def add_badword_command(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return

        chat_id = str(message.chat.id)
        args = message.text.split(None, 1)
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/addbw <word>`")
            return

        word = args[1].lower().strip()
        conf = load_mod_config()
        if chat_id not in conf: conf[chat_id] = {}
        
        # Initialize with global if first time
        if "badwords" not in conf[chat_id]:
            conf[chat_id]["badwords"] = global_badwords.copy()
            
        if word in conf[chat_id]["badwords"]:
            bot.reply_to(message, "⚠️ Word already in filter list.")
            return

        conf[chat_id]["badwords"].append(word)
        save_mod_config(conf)
        bot.reply_to(message, f"✅ `{word}` added to this group's bad words list.", parse_mode="Markdown")

    @bot.message_handler(commands=['rmbw', 'unfilter'])
    def remove_badword_command(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Admins only.")
            return

        chat_id = str(message.chat.id)
        args = message.text.split(None, 1)
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/rmbw <word>`")
            return

        word = args[1].lower().strip()
        conf = load_mod_config()
        if chat_id not in conf: conf[chat_id] = {}
        
        # Materialize list if needed so we can remove from defaults
        if "badwords" not in conf[chat_id]:
            conf[chat_id]["badwords"] = global_badwords.copy()

        if word not in conf[chat_id]["badwords"]:
            bot.reply_to(message, "⚠️ Word not in filter list.")
            return

        conf[chat_id]["badwords"].remove(word)
        save_mod_config(conf)
        bot.reply_to(message, f"✅ `{word}` removed from this group's bad words list.", parse_mode="Markdown")

# Auto-moderation (Logic Refined)
def auto_moderate(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    # Skip for admins or private chats
    if message.chat.type == "private": return False
    
    now = time.time()
    last_time = message_timestamps.get(user_id, 0)
    
    # 1. Spam Filter (Simple: < 0.7s between messages)
    if now - last_time < 0.7:
        if not is_admin(chat_id, int(user_id)):
            try:
                bot.delete_message(chat_id, message.message_id)
                # Don't warn every time, just delete
                return True
            except:
                pass
    
    message_timestamps[user_id] = now
    
    # 2. Bad Words (Group Specific)
    if not message.text: return False
    
    current_badwords = get_effective_badwords(chat_id)
    text_lower = message.text.lower()
    
    # Check whole words better? For now simple inclusion
    if any(w in text_lower for w in current_badwords):
        if not is_admin(chat_id, int(user_id)):
            try:
                bot.delete_message(chat_id, message.message_id)
                bot.send_message(chat_id, f"🚫 Watch your language, {message.from_user.first_name}!")
                return True
            except:
                pass
                
    return False

print("✅ Moderation handlers registered.")
