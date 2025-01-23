import telebot
import openai
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
)

# Check if values are loaded correctly
if not BOT_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENAI_API_KEY is not set or couldn't be loaded from .env file.")

openai.api_key = OPENAI_API_KEY
bot = telebot.TeleBot(BOT_TOKEN)

# Function to load data from files
def load_from_file(filename, default_list=None):
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_list or []

# Load content from external files
roasts = load_from_file("roasts.txt", default_list=[
    "You're like a software update: Nobody wants you, but we’re stuck with you.",
    "Your secrets are safe with me. I never even listen when you tell me them.",
])
motivations = load_from_file("motivations.txt", default_list=[
    "Keep shining like the star you are!",
    "Believe in yourself; you’re doing great!"
])
badwords = load_from_file("badwords.txt", default_list=[
    "badword1", "badword2", "badword3"
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

@bot.message_handler(func=lambda message: message.text and message.text.strip() != "")
def auto_moderate(message):
    user_id = message.from_user.id

    # Spam detection with a timeout
    current_time = time.time()
    if current_time - message_timestamps[user_id] > 60:  # Reset counter after 60 seconds
        user_messages[user_id] = 0
    message_timestamps[user_id] = current_time

    user_messages[user_id] += 1

    # Check for spam
    if user_messages[user_id] > 5:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"Chill {message.from_user.first_name}, spamming isn't cute 😤")
        user_messages[user_id] = 0  # Reset after warning
        return

    # Check for bad words
    if any(badword in message.text.lower() for badword in badwords):
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, f"Uh-oh, watch your language {message.from_user.first_name}!")
        print(f"Deleted message from {message.from_user.username}: {message.text}")
        return

    # Process message only if bot is mentioned or replied to
    if (message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id) or \
       (f"@{bot.get_me().username.lower()}" in message.text.lower()):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": message.text}
                ]
            )
            bot.send_message(message.chat.id, response.choices[0].message['content'])
        except openai.OpenAIError as e:
            bot.send_message(message.chat.id, f"Oops, there was an error processing your request. Please try again later!")
            print(f"OpenAI error: {e}")
            
# Greet new members
@bot.message_handler(content_types=['new_chat_members'])
def greet_new_member(message):
    for member in message.new_chat_members:
        bot.reply_to(message, f"OMG {member.first_name}, welcome! Hope you can keep up with our vibes! ✨")

# Run the bot
print("Sassy Telegram bot is running...")
bot.polling()