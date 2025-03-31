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

def is_admin(chat_id, user_id):
    """Check if the user is an admin in the group."""
    chat_admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in chat_admins)

def bot_is_admin(chat_id):
    """Check if the bot itself is an admin."""
    bot_id = bot.get_me().id
    chat_admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == bot_id for admin in chat_admins)

# Auto-Greeting New Users
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    if not bot_is_admin(message.chat.id):
        return
    
    new_user = message.new_chat_members[0]
    welcome_messages = [
        f"🎉 Hey {new_user.first_name}, welcome to the jungle! Hope you can keep up. 😏",
        f"🔥 {new_user.first_name} just walked in! Let’s see if they can survive my sass. 💅",
        f"👀 Oh snap, {new_user.first_name} is here! Play nice, or I’ll roast you. 😈"
    ]
    bot.send_message(message.chat.id, random.choice(welcome_messages))

# Muting, Unmuting, and Banning
@bot.message_handler(commands=['mute', 'unmute', 'warn', 'ban'])
def moderation_commands(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not bot_is_admin(chat_id):
        return

    if not is_admin(chat_id, user_id):
        bot.reply_to(message, "🚫 Only admins can use this command!")
        return

    if not message.reply_to_message or not message.reply_to_message.from_user:
        bot.reply_to(message, "⚠️ Reply to a valid user to take action!")
        return

    target_id = message.reply_to_message.from_user.id

    if is_admin(chat_id, target_id):
        bot.reply_to(message, "🚫 You cannot take action against an admin!")
        return

    if message.text.startswith("/mute"):
        mute_duration = 300  # Default: 5 minutes
        try:
            command_parts = message.text.split()
            if len(command_parts) > 1:
                mute_duration = int(command_parts[1]) * 60
        except ValueError:
            bot.reply_to(message, "⚠️ Invalid time format! Use `/mute [minutes]`")
            return

        muted_until = datetime.now() + timedelta(seconds=mute_duration)
        muted_users[target_id] = muted_until

        bot.restrict_chat_member(chat_id, target_id, until_date=muted_until.timestamp(), can_send_messages=False)
        bot.reply_to(message, f"🔇 User {message.reply_to_message.from_user.first_name} has been muted for {mute_duration // 60} minutes!")

    elif message.text.startswith("/unmute"):
        if target_id in muted_users:
            del muted_users[target_id]
        bot.restrict_chat_member(chat_id, target_id, can_send_messages=True)
        bot.reply_to(message, f"🔊 User {message.reply_to_message.from_user.first_name} has been unmuted!")

    elif message.text.startswith("/warn"):
        user_warnings[target_id] += 1
        if user_warnings[target_id] >= 3:
            mute_duration = random.randint(60, 86400)
            muted_until = datetime.now() + timedelta(seconds=mute_duration)
            muted_users[target_id] = muted_until

            bot.restrict_chat_member(chat_id, target_id, until_date=muted_until.timestamp(), can_send_messages=False)
            bot.send_message(chat_id, f"🤐 User {message.reply_to_message.from_user.first_name} has been muted for {mute_duration // 60} minutes due to repeated warnings.")
        else:
            bot.send_message(chat_id, f"⚠️ Warning {user_warnings[target_id]}/3 - Stop spamming!")

    elif message.text.startswith("/ban"):
        bot.kick_chat_member(chat_id, target_id)
        bot.reply_to(message, "🚨 User has been banned!")

# Auto-moderation
@bot.message_handler(func=lambda message: message.text is not None)
def auto_moderate(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    if not bot_is_admin(chat_id):
        return

    # Anti-spam detection
    current_time = time.time()
    if current_time - message_timestamps[user_id] < 5:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"⚠️ {message.from_user.first_name}, stop spamming!")
        return

    message_timestamps[user_id] = current_time
    user_messages[user_id] += 1

    # Bad word filtering
    if any(badword in message.text.lower() for badword in badwords):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"Uh-oh, watch your language {message.from_user.first_name}!")
        return

def check_unmute():
    while True:
        now = datetime.now()
        to_unmute = [user_id for user_id, unmute_time in muted_users.items() if now >= unmute_time]

        for user_id in to_unmute:
            for chat_id in list(muted_users.keys()):
                try:
                    if bot_is_admin(chat_id):
                        bot.restrict_chat_member(chat_id, user_id, can_send_messages=True)
                        bot.send_message(chat_id, f"🔊 User {bot.get_chat_member(chat_id, user_id).user.first_name} has been auto-unmuted!")
                        del muted_users[user_id]
                except Exception as e:
                    print(f"Error unmuting user {user_id} in chat {chat_id}: {e}")

        time.sleep(60)

threading.Thread(target=check_unmute, daemon=True).start()
