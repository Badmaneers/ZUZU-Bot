from helper import load_from_file
import random
import os
import telebot

# Load Roasts & Motivations
roasts = load_from_file("bot/roasts.txt", ["You're like a software update: Nobody wants you, but we’re stuck with you."])
motivations = load_from_file("bot/motivations.txt", ["Keep shining like the star you are!"])

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

def register_fun_handlers(bot):
    """Registers /roast and /motivate commands"""
    @bot.message_handler(commands=['roast', 'motivate'])
    def fun(message):
        chat_id = message.chat.id
        target = message.reply_to_message or message  # Defaults to sender if no reply
        target_name = target.from_user.first_name
        response = random.choice(roasts) if message.text.startswith("/roast") else random.choice(motivations)

        if chat_id > 0:  # Private chats (DMs have positive IDs)
            bot.send_message(chat_id, f"{target_name}, {response}")
        else:
            try:
                bot_info = bot.get_me()
                chat_member = bot.get_chat_member(chat_id, bot_info.id)
                user_id_tag = f"<a href='tg://user?id={target.from_user.id}'>{target_name}</a>"

                if chat_member.status in ['administrator', 'creator']:
                    bot.reply_to(target, f"{target_name}, {response}")
                else:
                    bot.send_message(chat_id, f"{user_id_tag}, {response}", parse_mode="HTML")

            except Exception as e:
                print(f"Error checking admin status: {e}")
                bot.send_message(chat_id, f"{user_id_tag}, {response}", parse_mode="HTML")

register_fun_handlers(bot)