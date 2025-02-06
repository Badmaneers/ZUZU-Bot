import telebot
import os
import random
from dotenv import load_dotenv
import re
from openai import OpenAI
from collections import defaultdict
import time

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Check if values are loaded correctly
if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENROUTER_API_KEY is not set.")

bot = telebot.TeleBot(BOT_TOKEN)

# Function to load data from files
def load_from_file(filename, default_list=None):
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_list or []

# Function to load the system prompt from prompt.txt
def load_prompt():
    try:
        with open("bot/prompt.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error loading prompt.txt: {e}")
        return "You are a helpful and engaging assistant."
        
# Load content from external files
roasts = load_from_file("bot/roasts.txt", default_list=[
    "You're like a software update: Nobody wants you, but we’re stuck with you.",
    "Your secrets are safe with me. I never even listen when you tell me them.",
])
motivations = load_from_file("bot/motivations.txt", default_list=[
    "Keep shining like the star you are!",
    "Believe in yourself; you’re doing great!"
])
badwords = load_from_file("bot/badwords.txt", default_list=[
    "Nigga", "Ching Chong", "MC"
])

# Spam tracking with reset
user_messages = defaultdict(int)
message_timestamps = defaultdict(float)

# Custom welcome message
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.reply_to(message, f"Hey {message.from_user.first_name}! Your fave admin is here. Type /help to see what I can do!")

# Handle '/help' command
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.reply_to(message, "Heyy, here's what I can do:\n"
                          "/roast - Want some spicy burns? 🔥\n"
                          "/motivate - Get a pep talk! 💪\n"
                          "/tea - Spill some gossip 😉\n"
                          "/rules - See the group rules 📜\n"
                          "/contribute - Help make me better! 🛠️")

# Roast command
@bot.message_handler(commands=['roast'])
def roast_user(message):
    if roasts:
        bot.reply_to(message, f"{message.from_user.first_name}, {random.choice(roasts)}")
    else:
        bot.reply_to(message, "Oops, I'm out of roasts for now! Try again later.")

# Motivation command
@bot.message_handler(commands=['motivate'])
def motivate_user(message):
    if motivations:
        bot.reply_to(message, f"{message.from_user.first_name}, {random.choice(motivations)}")
    else:
        bot.reply_to(message, "Oops, I'm out of motivation for now! Try again later.")

# Spill the tea
@bot.message_handler(commands=['tea'])
def spill_tea(message):
    bot.reply_to(message, "Sis, you know I can’t gossip in public... but DM me 😉")

# Group rules
@bot.message_handler(commands=['rules'])
def group_rules(message):
    bot.reply_to(message, "Rule #1: No spam. Rule #2: Be respectful. Rule #3: Have fun, but don’t test me. 😉")

# Help contribute
@bot.message_handler(commands=['contribute'])
def contribute(message):
    bot.reply_to(message, 
                 "Want to contribute to my sass and moderation skills? 🛠️\n\n"
                 "Check out my GitHub repository: [https://github.com/Badmaneers/Mod-Queen-Bot]\n"
                 "Feel free to submit issues, suggest new features, or fork the repo and make pull requests!\n\n"
                 "Every contribution helps make me even better! 🚀")

# Load prompt at startup
system_prompt = load_prompt()

# Store chat history for each user
chat_memory = defaultdict(list)

@bot.message_handler(func=lambda message: message.text and message.text.strip() != "")
def auto_moderate(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Spam detection with a timeout
    current_time = time.time()
    if current_time - message_timestamps[user_id] > 60:  # Reset counter after 60 seconds
        user_messages[user_id] = 0
        chat_memory[user_id] = []  # Reset chat memory after inactivity

    message_timestamps[user_id] = current_time
    user_messages[user_id] += 1

    # Check for spam
    if user_messages[user_id] > 5:
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"Chill {message.from_user.first_name}, spamming isn't cute 😤")
        user_messages[user_id] = 0  # Reset after warning
        return

    # Check for bad words
    if any(badword in message.text.lower() for badword in badwords):
        bot.delete_message(chat_id, message.message_id)
        bot.send_message(chat_id, f"Uh-oh, watch your language {message.from_user.first_name}!")
        return

    # Add user message to memory
    chat_memory[user_id].append({"role": "user", "content": message.text})

    # Keep only the last 15 messages (to avoid sending too much data)
    chat_memory[user_id] = chat_memory[user_id][-15:]

    # Process AI response only if bot is mentioned or replied to
    if (message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id) or \
       (f"@{bot.get_me().username.lower()}" in message.text.lower()):
        try:
            # Create conversation history
            conversation = [{"role": "system", "content": system_prompt}] + chat_memory[user_id]

            # Get AI response using the correct DeepSeek model
            response = client.chat.completions.create(
                model="meta-llama/llama-3.1-405b-instruct:free",
                messages=conversation
            )

            # Extract AI response
            ai_reply = response.choices[0].message.content.strip() if response.choices else "Sorry, I have no response."

            if not ai_reply:
                ai_reply = "Hmm, I don't know what to say."

            # Save AI response in memory
            chat_memory[user_id].append({"role": "assistant", "content": ai_reply})

            # Reply to user
            bot.reply_to(message, ai_reply)

        except Exception as e:
            bot.send_message(chat_id, "Oops, there was an error processing your request. Please try again later!")
            print(f"DeepSeek API error: {e}")



            
# Greet new members
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    for member in message.new_chat_members:
        bot.reply_to(message, f"OMG {member.first_name}, welcome! Hope you can keep up with our vibes! ✨")

# Run the bot
print("Sassy Telegram bot is running...")
bot.infinity_polling()  # Ensures auto-reconnection on failure
