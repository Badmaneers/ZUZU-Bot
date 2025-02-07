import telebot
import os
import random
import json
import zlib
import base64
from dotenv import load_dotenv
import re
import time
from collections import defaultdict
import signal
import sys
from openai import OpenAI
import random
from datetime import datetime, timedelta
import threading

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

muted_users = {}  # Store muted users with their unmute time
bot = telebot.TeleBot(BOT_TOKEN)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENROUTER_API_KEY is not set.")

# ========== Memory Storage ========== #
MEMORY_FILE = "chat_memory.json"

def compress_data(data):
    return base64.b64encode(zlib.compress(json.dumps(data).encode())).decode()

def decompress_data(data):
    return json.loads(zlib.decompress(base64.b64decode(data)).decode())

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                raw_data = file.read().strip()
                if raw_data:
                    return decompress_data(raw_data)
        except Exception as e:
            print(f"Error loading memory: {e}")
    return {}

def save_memory():
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            file.write(compress_data(chat_memory))
    except Exception as e:
        print(f"Error saving memory: {e}")

chat_memory = load_memory()

# Custom welcome message
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.reply_to(message, f"Hey {message.from_user.first_name}! Your fave admin is here. Type /help to see what I can do!")

# Help contribute
@bot.message_handler(commands=['contribute'])
def contribute(message):
    bot.reply_to(message, 
                 "Want to contribute to my sass and moderation skills? 🛠️\n\n"
                 "Check out my GitHub repository: [https://github.com/Badmaneers/Mod-Queen-Bot]\n"
                 "Feel free to submit issues, suggest new features, or fork the repo and make pull requests!\n\n"
                 "Every contribution helps make me even better! 🚀")

# Muting and Unmuting stuff
@bot.message_handler(commands=['mute'])
def mute_user(message):
    """Admin can mute users for a specified time (default: 10 minutes)."""
    chat_id = message.chat.id
    user_id = message.from_user.id

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

    mute_duration = 600  # Default: 10 minutes

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

# Unmute stuff here
@bot.message_handler(commands=['unmute'])
def unmute_user(message):
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

# Spill the tea
@bot.message_handler(commands=['tea'])
def spill_tea(message):
    bot.reply_to(message, "Sis, you know I can’t gossip in public... but DM me 😉")

# Group rules
@bot.message_handler(commands=['rules'])
def group_rules(message):
    bot.reply_to(message, "Rule #1: No spam. Rule #2: Be respectful. Rule #3: Have fun, but don’t test me. 😉")

# Handle '/help' command
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "Heyy, here's what I can do:\n"
                          "/roast - Want some spicy burns? 🔥\n"
                          "/motivate - Get a pep talk! 💪\n"
                          "/tea - Spill some gossip 😉\n"
                          "/rules - See the group rules 📜\n"
                          "/contribute - Help make me better! 🛠️\n"
                          "/warn - To warn users! 👹")
                          
# ========== Utility Functions ========== #
def load_from_file(filename, default_list=None):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_list or []

def load_prompt():
    try:
        with open("bot/prompt.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error loading prompt.txt: {e}")
        return "You are a sassy and engaging assistant."

roasts = load_from_file("bot/roasts.txt", ["You're like a software update: Nobody wants you, but we’re stuck with you."])
motivations = load_from_file("bot/motivations.txt", ["Keep shining like the star you are!"])
badwords = load_from_file("bot/badwords.txt", ["examplebadword1", "examplebadword2"])

# ========== Moderation System ========== #
user_messages = defaultdict(int)
message_timestamps = defaultdict(float)
user_warnings = defaultdict(int)

def is_admin(chat_id, user_id):
    """Check if the user is an admin in the group."""
    chat_admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in chat_admins)

def warn_user(user_id, chat_id):
    """Warn users and mute them for a random time instead of kicking."""
    if is_admin(chat_id, user_id):
        bot.send_message(chat_id, f"⚠️ {bot.get_chat_member(chat_id, user_id).user.first_name} is an admin, so no muting. 😏")
        return  

    user_warnings[user_id] += 1
    if user_warnings[user_id] >= 3:
        mute_duration = random.randint(60, 86400)  # Random mute time (1 min - 1 day)
        muted_until = datetime.now() + timedelta(seconds=mute_duration)
        muted_users[user_id] = muted_until  # Store mute expiry time

        bot.restrict_chat_member(chat_id, user_id, until_date=muted_until.timestamp(), can_send_messages=False)
        bot.send_message(chat_id, f"🤐 User {bot.get_chat_member(chat_id, user_id).user.first_name} has been muted for {mute_duration // 60} minutes due to spam.")
    else:
        bot.send_message(chat_id, f"⚠️ Warning {user_warnings[user_id]}/3 - Stop spamming!")



# ========== Fix /roast and /motivate to Tag Users ========== #
@bot.message_handler(commands=['roast'])
def roast_user(message):
    target = message.reply_to_message or message
    bot.reply_to(target, f"{target.from_user.first_name}, {random.choice(roasts)}")

@bot.message_handler(commands=['motivate'])
def motivate_user(message):
    target = message.reply_to_message or message
    bot.reply_to(target, f"{target.from_user.first_name}, {random.choice(motivations)}")

# ========== AI Chat System with Retries & Async Handling ========== #


system_prompt = load_prompt()

def process_ai_response(message, user_id, chat_id):
    """Handle AI responses with retries for failures."""
    try:
        conversation = [{"role": "system", "content": system_prompt}] + chat_memory.get(user_id, [])
        
        for _ in range(2):  # Retry up to 2 times
            try:
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.1-405b-instruct:free",
                    messages=conversation
                )
                if response.choices:
                    ai_reply = response.choices[0].message.content.strip()
                    chat_memory[user_id].append({"role": "assistant", "content": ai_reply})
                    save_memory()
                    bot.send_message(chat_id, ai_reply, reply_to_message_id=message.message_id)
                    return
            except Exception as e:
                print(f"AI backend error: {e}, retrying...")
                time.sleep(2)  # Wait before retrying
        bot.send_message(chat_id, "Oops, my brain lagged out. Try again later! 😭")
    
    except Exception as e:
        bot.send_message(chat_id, "Oops, something went wrong.")
        print(f"AI error: {e}")

@bot.message_handler(func=lambda message: message.text and message.text.strip() != "")
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
        return

    message_timestamps[user_id] = current_time
    user_messages[user_id] += 1

    # Bad word filtering
    if any(badword in message.text.lower() for badword in badwords):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"Uh-oh, watch your language {message.from_user.first_name}!")
        return

    # Store chat history
    if user_id not in chat_memory:
        chat_memory[user_id] = []
    chat_memory[user_id].append({"role": "user", "content": message.text})
    chat_memory[user_id] = chat_memory[user_id][-10:]  # Keep last 10 messages

# ========== Start Bot ========== #
def handle_exit(signal_number, frame):
    print("Saving memory before exit...")
    save_memory()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

print("Sassy Telegram bot is running...")
bot.infinity_polling()
