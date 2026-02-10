import json
import random
import time
import os
from config import BASE_DIR, FUN_FILE
from core.ai_response import get_ai_reply

# ——— Rate‑Limit Tracker & Config —————————————————————————
rate_limit_tracker = {}

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except:
        return {"max_usage": 3, "timeout": 300}

config = load_config()

def check_rate_limit(chat_id, user_id):
    now = time.time()
    chat_limits = rate_limit_tracker.setdefault(str(chat_id), {})
    times = chat_limits.setdefault(str(user_id), [])
    times[:] = [t for t in times if now - t < config["timeout"]]
    if len(times) >= config["max_usage"]:
        return False
    times.append(now)
    return True

# ——— Load Content (Fallback) ————————————————————————————
def load_fun_content():
    try:
        if os.path.exists(FUN_FILE):
            with open(FUN_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading fun file: {e}")
    return {
        "roasts": ["You are barely worth roasting."],
        "motivations": ["You can do it!"]
    }

fun_content = load_fun_content()
roasts = fun_content.get("roasts", ["You are barely worth roasting."])
motivations = fun_content.get("motivations", ["You can do it!"])

# ——— AI Prompts —————————————————————————————————————————
ROAST_SYSTEM = "You are a professional roaster. You are mean, funny, witty, and savage. Your goal is to absolutely destroy the person based on their name or just general insults. Keep it short (1-2 sentences) but deadly."
MOTIVATE_SYSTEM = "You are a high-energy life coach and hype man. You give aggressive, powerful, and iconic motivation. Make them feel like a god. Keep it short and punchy."

# ——— Handlers ———————————————————————————————————————————

def register_fun_handlers(bot):

    @bot.message_handler(commands=['roast'])
    def roast_cmd(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if message.chat.type != "private" and not check_rate_limit(chat_id, user_id):
            return bot.reply_to(message, f"🐢 Slow down! You get {config['max_usage']} roasts every {config['timeout']//60} min.")

        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        target_name = target.first_name

        # Try AI first
        ai_text = None
        try:
            bot.send_chat_action(chat_id, "typing")
            ai_text = get_ai_reply(ROAST_SYSTEM, f"Roast this person named {target_name}.")
        except:
            pass

        # Fallback
        text = ai_text if ai_text else random.choice(roasts)
        
        # Build mention
        if message.chat.type == "private":
            mention = target_name
        else:
            mention = f'<a href="tg://user?id={target.id}">{target_name}</a>'
            
        bot.send_message(chat_id, f"{mention}, {text}", parse_mode="HTML")

    @bot.message_handler(commands=['motivate'])
    def motivate_cmd(message):
        chat_id = message.chat.id
        user_id = message.from_user.id

        if message.chat.type != "private" and not check_rate_limit(chat_id, user_id):
            return bot.reply_to(message, f"🐢 Slow down! You get {config['max_usage']} motivations every {config['timeout']//60} min.")

        target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
        target_name = target.first_name

        # Try AI first
        ai_text = None
        try:
            bot.send_chat_action(chat_id, "typing")
            ai_text = get_ai_reply(MOTIVATE_SYSTEM, f"Motivate this person named {target_name}.")
        except:
            pass

        # Fallback
        text = ai_text if ai_text else random.choice(motivations)

        # Build mention
        if message.chat.type == "private":
            mention = target_name
        else:
            mention = f'<a href="tg://user?id={target.id}">{target_name}</a>'

        bot.send_message(chat_id, f"{mention}, {text}", parse_mode="HTML")

    print("✅ Fun handlers registered.")
