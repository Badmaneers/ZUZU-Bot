import telebot
import os
import random
from collections import defaultdict
import time
import memory
import threading
from datetime import datetime, timedelta
from ai_response import process_ai_response
from helper import load_from_file

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
muted_users = {}  # Store muted users with their unmute time
user_messages = defaultdict(int)
message_timestamps = defaultdict(float)
user_warnings = defaultdict(int)
# Load badwords list
badwords = load_from_file("bot/badwords.txt")

# Auto-Greeting New Users
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    new_user = message.new_chat_members[0]
    welcome_messages = [
        f"🎉 Hey {new_user.first_name}, welcome to the jungle! Hope you can keep up. 😏",
        f"🔥 {new_user.first_name} just walked in! Let’s see if they can survive my sass. 💅",
        f"👀 Oh snap, {new_user.first_name} is here! Play nice, or I’ll roast you. 😈"
    ]
    bot.send_message(message.chat.id, random.choice(welcome_messages))
    
def is_admin(chat_id, user_id):
    """Check if the user is an admin in the group."""
    chat_admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in chat_admins)
        
# Muting and Unmuting and Banning stuff
def mute_unmute(message):
  chat_id = message.chat.id
  user_id = message.from_user.id

  if message.text.startswith("/mute"):
    """Admin can mute users for a specified time (default: 10 minutes)."""

    # Check if chat is a supergroup
    chat = bot.get_chat(chat_id)
    if chat.type != "supergroup":
        bot.reply_to(message, "🚫 This command only works in supergroups!")
        return

    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "🚫 Only admins can use this command!")
        return

    # ✅ Fix: Check if the message has a reply properly
    if not message.reply_to_message or not message.reply_to_message.from_user:
        bot.reply_to(message, "⚠️ Reply to a valid user to mute them!")
        return

    target_id = message.reply_to_message.from_user.id

    if is_admin(chat_id, target_id):
        bot.reply_to(message, "🚫 You cannot mute an admin!")
        return

    mute_duration = 300  # Default: 5 minutes

    # ✅ Fix: Check if a duration was provided
    try:
        command_parts = message.text.split()
        if len(command_parts) > 1:
            mute_duration = int(command_parts[1]) * 60
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid time format! Use `/mute [minutes]`")

    muted_until = datetime.now() + timedelta(seconds=mute_duration)
    muted_users[target_id] = muted_until  # Store mute expiry time

    bot.restrict_chat_member(chat_id, target_id, until_date=muted_until.timestamp(), can_send_messages=False)
    bot.reply_to(message, f"🔇 User {bot.get_chat_member(chat_id, target_id).user.first_name} has been muted for {mute_duration // 60} minutes!")

# unmute stuff
  if message.text.startswith("/unmute"):
    """Admin can manually unmute users before their time expires."""
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "🚫 Only admins can use this command!")
        return

    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id

        if target_id in muted_users:
            del muted_users[target_id]  # Remove from mute list

        bot.restrict_chat_member(chat_id, target_id, can_send_messages=True)
        bot.reply_to(message, f"🔊 User {bot.get_chat_member(chat_id, target_id).user.first_name} has been unmuted!")
    else:
        bot.reply_to(message, "Reply to a user to unmute them!")

  if message.text.startswith("/warn"):
    """Warn users and mute them for a random time instead of kicking."""

    # Check if the message is a reply
    if message.reply_to_message:
        replied_user_id = message.reply_to_message.from_user.id
        
        # If the replied user is an admin, do not warn
        if is_admin(chat_id, replied_user_id):
            bot.send_message(chat_id, f"⚠️ {bot.get_chat_member(chat_id, replied_user_id).user.first_name} is an admin, so no warning. 😏")
            return  

        # Initialize warnings for the replied user if not already done
        if replied_user_id not in user_warnings:
            user_warnings[replied_user_id] = 0

        user_warnings[replied_user_id] += 1
        if user_warnings[replied_user_id] >= 3:
            mute_duration = random.randint(60, 86400)  # Random mute time (1 min - 1 day)
            muted_until = datetime.now() + timedelta(seconds=mute_duration)
            muted_users[replied_user_id] = muted_until  # Store mute expiry time

            bot.restrict_chat_member(chat_id, replied_user_id, until_date=muted_until.timestamp(), can_send_messages=False)
            bot.send_message(chat_id, f"🤐 User {bot.get_chat_member(chat_id, replied_user_id).user.first_name} has been muted for {mute_duration // 60} minutes due to spam.")
        else:
            bot.send_message(chat_id, f"⚠️ Warning {user_warnings[replied_user_id]}/3 - Stop spamming!")
    else:
        bot.send_message(chat_id, "⚠️ Please reply to a user to warn them.")
# Baning stuff
  if message.text.startswith("/ban"):
    """Admin can ban users from the group."""
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id

    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "🚫 Only admins can use this command!")
        return
    if is_admin(chat_id, target_id):
        bot.reply_to(message, "🚫 You cannot ban an admin!")
        return

    if message.reply_to_message:
        bot.kick_chat_member(chat_id, target_id)
        bot.reply_to(message, "🚨 User has been banned!")
    else:
        bot.reply_to(message, "Reply to a user to ban them.")
        
# Auto moderate 
def warn_user(user_id, chat_id):
    """Warn users and mute them for a random time instead of kicking."""
    if is_admin(chat_id, user_id):
        bot.send_message(chat_id, f"⚠️ {bot.get_chat_member(chat_id, user_id).user.first_name} is an admin, so no muting. 😏")
        return  

@bot.message_handler(func=lambda message: message.text is not None)
def auto_moderate(message):
    user_id = str(message.from_user.id)
    chat_id = message.chat.id
    is_private_chat = message.chat.type == "private"

    # Fix: Allow talking to the bot directly in DMs
    is_bot_mentioned = f"@{bot.get_me().username.lower()}" in message.text.lower()
    is_replying_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
    if is_private_chat or is_bot_mentioned or is_replying_to_bot:
        threading.Thread(target=process_ai_response, args=(message, user_id, chat_id)).start()
        return

    # Anti-spam detection
    current_time = time.time()
    if current_time - message_timestamps[user_id] < 5:
        warn_user(user_id, chat_id)
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"{message.from_user.first_name }Stop Spamming Cutie\nIts isn't cute")
        return

    message_timestamps[user_id] = current_time
    user_messages[user_id] += 1

    # Bad word filtering
    if any(badword in message.text.lower() for badword in badwords):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"Uh-oh, watch your language {message.from_user.first_name}!")
        return

    # Store chat history
    if user_id not in memory.chat_memory:
        memory.chat_memory[user_id] = []
    memory.chat_memory[user_id].append({"role": "user", "content": message.text})
    memory.chat_memory[user_id] = memory.chat_memory[user_id][-10:]  # Keep last 10 messages
    
# Unmute automatically after a set amount of time 
def check_unmute():
    """Check if muted users should be unmuted."""
    while True:
        now = datetime.now()
        to_unmute = [user_id for user_id, unmute_time in muted_users.items() if now >= unmute_time]

        for user_id in to_unmute:
            for chat_id in list(muted_users.keys()):  # ✅ FIX: Don't use `bot.get_updates()`
                try:
                    chat = bot.get_chat(chat_id)
                    if chat.type != "supergroup":
                        print(f"Skipping unmute for {user_id} in non-supergroup {chat_id}")
                        continue  # ✅ Skip unmuting users in non-supergroups

                    bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
                    bot.send_message(chat_id, f"🔊 User {bot.get_chat_member(chat_id, user_id).user.first_name} has been auto-unmuted!")
                    del muted_users[user_id]  # Remove user from mute list
                except Exception as e:
                    print(f"Error unmuting user {user_id} in chat {chat_id}: {e}")

        time.sleep(60)  # Check every 60 seconds

# ✅ Start auto-unmute thread
threading.Thread(target=check_unmute, daemon=True).start()