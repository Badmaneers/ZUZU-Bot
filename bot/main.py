import telebot
import os
from openai import OpenAI
import random
import threading
from fortune import fortune
from moderations import greet_new_member , mute_unmute , auto_moderate
from fun import register_fun_handlers
from owner import register_owner_commands, fetch_groups
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
bot = telebot.TeleBot(BOT_TOKEN)
    
# ✅ Configure Logging
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Custom start message
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
  if message.from_user.id == OWNER_ID:
    help_text=("Heyy, here's what I can do:\n"
              "/roast - Want some spicy burns? 🔥\n"
              "/motivate - Get a pep talk! 💪\n"
              "/tea - Spill some gossip 😉\n"
              "/rules - See the group rules 📜\n"
              "/contribute - Help make me better! 🛠️\n"
              "/warn - To warn users! 👹\n"
              "/ban - To remove someone from group! 💥\n"
              "/mute - To shut someone's mouth! 🤐\n"
              "/unmute - To open someone's mouth again! 👄\n"
              "/fortune - To talk to here fortune teller side! 🥠\n"
              "👑 *Owner Commands:*\n"
              "/broadcast <message> - Send a message to all groups\n"
              "/restart - Restart the bot\n"
              "/logs - Fetch the last 10 logs\n")
  else:
    help_text=("Heyy, here's what I can do:\n"
              "/roast - Want some spicy burns? 🔥\n"
              "/motivate - Get a pep talk! 💪\n"
              "/tea - Spill some gossip 😉\n"
              "/rules - See the group rules 📜\n"
              "/contribute - Help make me better! 🛠️\n"
              "/warn - To warn users! 👹\n"
              "/ban - To remove someone from group! 💥\n"
              "/mute - To shut someone's mouth! 🤐\n"
              "/unmute - To open someone's mouth again! 👄\n"
              "/fortune - To talk to here fortune teller side! 🥠")
  bot.reply_to(message, help_text, parse_mode="Markdown")

bot.message_handler(commands=['fortune'])(fortune)
register_fun_handlers(bot)
fetch_groups()
register_owner_commands(bot)
bot.message_handler(content_types=['new_chat_members'])(greet_new_member)
bot.message_handler(commands=['mute' , 'unmute' , 'warn' , 'ban'])(mute_unmute)
bot.message_handler(func=lambda message: message.text is not None)(auto_moderate)

bot.infinity_polling()
