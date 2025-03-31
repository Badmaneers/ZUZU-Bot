from helper import load_from_file
import random
import telebot

# Remove bot initialization, it will be passed from main.py
roasts = load_from_file("bot/roasts.txt", ["You're like a software update: Nobody wants you, but we’re stuck with you."])
motivations = load_from_file("bot/motivations.txt", ["Keep shining like the star you are!"])

def register_fun_handlers(bot):
    """Registers /roast and /motivate commands to the bot instance"""
    @bot.message_handler(commands=['roast', 'motivate'])
    def fun(message):
        target = message.reply_to_message or message  # Defaults to sender if no reply
        target_user = target.from_user  # The user to whom the bot will reply

        if message.text.startswith("/roast"):
            bot.reply_to(target, f"{target_user.first_name}, {random.choice(roasts)}")

        elif message.text.startswith("/motivate"):
            bot.reply_to(target, f"{target_user.first_name}, {random.choice(motivations)}")
