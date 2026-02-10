import logging
import threading
from core.bot_instance import bot
from config import BOT_TOKEN, OWNER_ID
from core.ai_response import process_ai_response
from modules.fortune import fortune
from modules.moderations import register_moderation_handlers, auto_moderate
from modules.fun import register_fun_handlers
from modules.owner import register_owner_commands, fetch_existing_groups
from modules.notes import register_notes_handlers
import modules.image_gen as image_gen

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
        "/fortune - Talk to my fortune teller side! 🥠\n"
        "/imagine - Generate an AI image from your prompt 🎨\n\n"
        "<b>🔨 Moderation Commands:</b>\n"
        "/warn - To warn users 👹\n"
        "/ban - Remove someone from the group 💥\n"
        "/kick - Kick user (can rejoin) 👢\n"
        "/mute [min] - Mute user (default 5m) 🤐\n"
        "/unmute - Unmute user 🗣️\n"
        "/pin - Pin a message 📌\n"
        "/purge [num] - Delete messages 🗑️\n"
        "/welcome on/off - Toggle welcome msg 👋\n"
        "/setwelcome [msg] - Set custom welcome 📝\n"
        "/addbw &lt;word&gt; - Add bad word to THIS group (Admin) 🤬\n"
        "/rmbw &lt;word&gt; - Remove bad word from THIS group (Admin) 😇\n\n"
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

# --- Register Module Handlers ---
register_fun_handlers(bot)
register_notes_handlers(bot)
register_owner_commands(bot)
register_moderation_handlers(bot)

# Specific commands that were exported as functions
bot.register_message_handler(fortune, commands=['fortune'])

@bot.message_handler(commands=["imagine"])
def handle_imagine(message):
    image_gen.imagine(bot, message)

# --- Fallback & Auto-Moderation ---
# This handler catches all text messages to perform moderation AND AI response.
@bot.message_handler(func=lambda message: message.text is not None)
def handle_text(message):
    # 1. Run auto-moderation
    if auto_moderate(message):
        return

    # 2. If message survived moderation, process for AI response
    process_ai_response(message)

# --- Start Everything ---
if __name__ == "__main__":
    fetch_existing_groups()
    logging.info("Worker Process Started...")
    bot.infinity_polling()
