import os
import logging
import telebot
import memory  # Import memory first to initialize database
from ai_response import process_ai_response
from fortune import fortune
from moderations import greet_new_member, moderation_commands, auto_moderate
from fun import register_fun_handlers
from owner import register_owner_commands, fetch_existing_groups
import notes

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
if not BOT_TOKEN:
    raise ValueError("Error: BOT_TOKEN is not set.")
    
bot = telebot.TeleBot(BOT_TOKEN)

# Configure logging
logging.basicConfig(
    filename="bot.log", 
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Basic Commands ---
@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.reply_to(message, f"Hey {message.from_user.first_name}! Your fave admin is here. Type /help to see what I can do!")

@bot.message_handler(commands=['contribute'])
def contribute(message):
    bot.reply_to(
        message,
        ("Want to contribute to my sass and moderation skills? 🛠️\n\n"
         "Check out my GitHub repository: [https://github.com/Badmaneers/ZUZU-Bot]\n"
         "Feel free to submit issues, suggest new features, or fork the repo and make pull requests!\n\n"
         "Every contribution helps make me even better! 🚀")
    )

@bot.message_handler(commands=['tea'])
def spill_tea(message):
    bot.reply_to(message, "Sis, you know I can’t gossip in public... but DM me 😉")

@bot.message_handler(commands=['rules'])
def group_rules(message):
    bot.reply_to(message, "Rule #1: No spam. Rule #2: Be respectful. Rule #3: Have fun, but don’t test me. 😉")

@bot.message_handler(commands=['help'])
def help_message(message):
    help_text = (
        "Heyy, here's what I can do:\n\n"
        "<b>🎭 Fun Commands:</b>\n"
        "/roast - Want some spicy burns? 🔥\n"
        "/motivate - Get a pep talk! 💪\n"
        "/tea - Spill some gossip 😉\n"
        "/rules - See the group rules 📜\n"
        "/fortune - Talk to my fortune teller side! 🥠\n\n"
        "<b>🔨 Moderation Commands:</b>\n"
        "/warn - To warn users 👹\n"
        "/ban - Remove someone from the group 💥\n"
        "/mute - Shut someone's mouth 🤐\n"
        "/unmute - Open someone's mouth again 👄\n\n"
        "<b>📜 Notes Commands:</b>\n"
        "/save &lt;title&gt; &lt;content&gt; - Save a note 💾\n"
        "/delnote &lt;title&gt; - Delete a note ❌\n"
        "/notes - List all notes 📜\n"
        "/toggle_notes - Enable/Disable notes in the group 📝\n\n"
        "<b>🛠 Contribute:</b>\n"
        "/contribute - Contribute to my sass!!\n"
    )
    if message.from_user.id == OWNER_ID:
        help_text += (
            "\n<b>👑 Owner Commands:</b>\n"
            "/broadcast &lt;message&gt; - Send a message to all groups\n"
            "/restart - Restart the bot\n"
            "/logs - Fetch the last 10 logs\n"
        )
    bot.reply_to(message, help_text, parse_mode="HTML")
    
# ---- Fun handler ----
register_fun_handlers(bot)
# ----- Fortune handler -----
bot.message_handler(commands=['fortune'])(fortune)

# --- Register Other Handlers ---
notes.register_notes_handlers(bot)
fetch_existing_groups()
register_owner_commands(bot)
bot.message_handler(content_types=['new_chat_members'])(greet_new_member)
bot.message_handler(commands=['mute', 'unmute', 'warn', 'ban'])(moderation_commands)
# --- AI Response Handler ---
@bot.message_handler(func=lambda message: message.text is not None)
def handle_text(message):  
    process_ai_response(message)

# This should be registered AFTER all other command handlers
bot.message_handler(func=lambda message: message.text is not None)(auto_moderate)


# --- Start the Bot ---
if __name__ == "__main__":
    logging.info("Bot is starting...")
    bot.infinity_polling()
