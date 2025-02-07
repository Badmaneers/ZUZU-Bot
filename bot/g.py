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

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
                          "/mute to mute a user 🤐\n"
                          "/unmute to unmute a user 👄")
                          
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

def warn_user(user_id, chat_id):
    user_warnings[user_id] += 1
    if user_warnings[user_id] >= 3:
        bot.kick_chat_member(chat_id, user_id)
        bot.send_message(chat_id, "User has been kicked for repeated violations.")
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
import threading

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
