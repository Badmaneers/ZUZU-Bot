import telebot
import os
import logging
from openai import OpenAI
from fortune import fortune
from moderations import greet_new_member, moderation_commands, auto_moderate
from fun import register_fun_handlers
from owner import register_owner_commands, fetch_existing_groups
from ai_response import process_ai_response
import notes

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Configure Logging
logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ======== Commands ======== #
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.reply_to(message, f"Hey {message.from_user.first_name}! Your fave admin is here. Type /help to see what I can do!")

@bot.message_handler(commands=['contribute'])
def contribute(message):
    bot.reply_to(message, 
                 "Want to contribute to my sass and moderation skills? 🛠️\n\n"
                 "Check out my GitHub repository: [https://github.com/Badmaneers/Mod-Queen-Bot]\n"
                 "Feel free to submit issues, suggest new features, or fork the repo and make pull requests!\n\n"
                 "Every contribution helps make me even better! 🚀")

@bot.message_handler(commands=['tea'])
def spill_tea(message):
    bot.reply_to(message, "Sis, you know I can’t gossip in public... but DM me 😉")

@bot.message_handler(commands=['rules'])
def group_rules(message):
    bot.reply_to(message, "Rule #1: No spam. Rule #2: Be respectful. Rule #3: Have fun, but don’t test me. 😉")

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = ("Heyy, here's what I can do:\n"
                 "/roast - Want some spicy burns? 🔥\n"
                 "/motivate - Get a pep talk! 💪\n"
                 "/tea - Spill some gossip 😉\n"
                 "/rules - See the group rules 📜\n"
                 "/contribute - Help make me better! 🛠️\n"
                 "/warn - To warn users! 👹\n"
                 "/ban - To remove someone from the group! 💥\n"
                 "/mute - To shut someone's mouth! 🤐\n"
                 "/unmute - To open someone's mouth again! 👄\n"
                 "/fortune - To talk to her fortune teller side! 🥠\n"
                 "/save <title> <content> - Save a note! 💾\n"
                 "/delnote <title> - Delete a note! ❌\n"
                 "/notes - List all notes! 📜\n"
                 "/toggle_notes - Enable/Disable note in the group 📝\n"
    if message.from_user.id == OWNER_ID:
        help_text += ("\n👑 *Owner Commands:*\n"
                      "/broadcast <message> - Send a message to all groups\n"
                      "/restart - Restart the bot\n"
                      "/logs - Fetch the last 10 logs")
    bot.reply_to(message, help_text, parse_mode="Markdown")

# ======== AI Response ======== #
@bot.message_handler(func=lambda message: message.chat.type == "private" or 
                                        (message.reply_to_message is not None and 
                                         message.reply_to_message.from_user.id == bot.get_me().id))
def handle_ai_response(message):
    process_ai_response(message)

# Register Handlers
bot.message_handler(commands=['fortune'])(fortune)
register_fun_handlers(bot)
notes.register_notes_handlers(bot)
fetch_existing_groups()
register_owner_commands(bot)
bot.message_handler(content_types=['new_chat_members'])(greet_new_member)
bot.message_handler(commands=['mute', 'unmute', 'warn', 'ban'])(moderation_commands)
bot.message_handler(func=lambda message: message.text is not None)(auto_moderate)

# Start the bot
bot.infinity_polling()
