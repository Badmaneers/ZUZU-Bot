import os
import json
import random
import time
import telebot
from helper import load_from_file

# ——— Bot Initialization ———————————————————————————————
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ——— Rate‑Limit Tracker & Config —————————————————————————
# Structure: { chat_id: { user_id: [timestamps] } }
rate_limit_tracker = {}

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        # default: 3 uses per 300 seconds (5 minutes)
        return {"max_usage": 3, "timeout": 300}

config = load_config()

def check_rate_limit(chat_id, user_id):
    now = time.time()
    chat_limits = rate_limit_tracker.setdefault(str(chat_id), {})
    times = chat_limits.setdefault(str(user_id), [])
    # purge old entries
    times[:] = [t for t in times if now - t < config["timeout"]]
    if len(times) >= config["max_usage"]:
        return False
    times.append(now)
    return True

# ——— Load Content ————————————————————————————————————————
roasts      = load_from_file("bot/roasts.txt",      ["No roast available right now."])
motivations = load_from_file("bot/motivations.txt", ["No motivation available right now."])

# ——— Handlers Registration ——————————————————————————————

def register_fun_handlers(bot):
    @bot.message_handler(commands=['roast'])
    def roast_cmd(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Rate‑limit in groups
        if message.chat.type != "private" and not check_rate_limit(chat_id, user_id):
            return bot.reply_to(
                message,
                f"🐢 Slow down! You get {config['max_usage']} roasts every {config['timeout']//60} min."
            )

        # Determine target
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        target_id   = target.id
        target_name = target.first_name

        # Build mention
        if message.chat.type == "private":
            mention = target_name
        else:
            mention = f'<a href="tg://user?id={target_id}">{target_name}</a>'

        # Pick and send
        text = random.choice(roasts)
        bot.send_message(chat_id, f"{mention}, {text}", parse_mode="HTML")

    @bot.message_handler(commands=['motivate'])
    def motivate_cmd(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Rate‑limit in groups
        if message.chat.type != "private" and not check_rate_limit(chat_id, user_id):
            return bot.reply_to(
                message,
                f"🐢 Slow down! You get {config['max_usage']} motivations every {config['timeout']//60} min."
            )

        # Determine target
        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        target_id   = target.id
        target_name = target.first_name

        # Build mention
        if message.chat.type == "private":
            mention = target_name
        else:
            mention = f'<a href="tg://user?id={target_id}">{target_name}</a>'

        # Pick and send
        text = random.choice(motivations)
        bot.send_message(chat_id, f"{mention}, {text}", parse_mode="HTML")

    print("✅ Fun handlers registered.")

# ——— Register on Import ——————————————————————————————————
register_fun_handlers(bot)
