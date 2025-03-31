from helper import load_from_file
import random
import os
import telebot
import time

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Store last message timestamps for rate limiting (per group)
rate_limit_tracker = {}

# Load roasts and motivations
roasts = load_from_file("bot/roasts.txt", ["You're like a software update: Nobody wants you, but we’re stuck with you."])
motivations = load_from_file("bot/motivations.txt", ["Keep shining like the star you are!"])

def register_fun_handlers(bot):
    """Registers /roast and /motivate commands to the bot instance"""
    @bot.message_handler(commands=['roast', 'motivate'])
    def fun(message):
        chat_id = message.chat.id
        is_private = message.chat.type == "private"
        now = time.time()

        # Rate limit: Allow only 3 messages per 5 minutes in groups
        if not is_private:
            if chat_id not in rate_limit_tracker:
                rate_limit_tracker[chat_id] = []
            
            # Remove expired timestamps (older than 5 minutes)
            rate_limit_tracker[chat_id] = [t for t in rate_limit_tracker[chat_id] if now - t < 300]

            if len(rate_limit_tracker[chat_id]) >= 3:
                bot.reply_to(message, "Slow down! You can only use /roast or /motivate 3 times every 5 minutes.")
                return

            # Add current timestamp
            rate_limit_tracker[chat_id].append(now)

        # Determine target (either replied user or sender)
        target = message.reply_to_message or message
        target_name = target.from_user.first_name
        target_id = target.from_user.id
        
        # Handle mentions if in group and bot is not an admin
        if not is_private and message.reply_to_message is None:
            mention = f'<a href="tg://user?id={target_id}">{target_name}</a>'
        else:
            mention = target_name  # Use direct name in DMs or replies

        # Send the response
        if message.text.startswith("/roast"):
            bot.send_message(chat_id, f"{mention}, {random.choice(roasts)}", parse_mode="HTML")

        elif message.text.startswith("/motivate"):
            bot.send_message(chat_id, f"{mention}, {random.choice(motivations)}", parse_mode="HTML")
