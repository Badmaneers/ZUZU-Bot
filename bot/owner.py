import telebot
import os
import subprocess
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
OWNER_ID = int(os.getenv("OWNER_ID"))

# Save Group Id to a file
@bot.message_handler(content_types=['new_chat_members'])
def save_group_id(message):
    chat_id = message.chat.id
    with open("groups.txt", "a") as file:
        if str(chat_id) not in open("groups.txt").read():
            file.write(f"{chat_id}\n")
            

# ✅ Owner-Only Decorator (Fixed)
def owner_only(func):
    def wrapper(message):
        if message.from_user.id == OWNER_ID:
            return func(message)  # ✅ Ensure function executes
        else:
            bot.reply_to(message, "🚫 You don’t have permission to use this command!")
    return wrapper

# ✅ Register All Owner Commands Under a Single Function
def register_owner_commands(bot):
    @bot.message_handler(commands=['broadcast'])
    @owner_only
    def broadcast(message):
        text = message.text.replace("/broadcast", "").strip()
        if not text:
            bot.reply_to(message, "📢 Please provide a message to broadcast.")
            return
        
        with open("groups.txt", "r") as file:
            group_ids = file.readlines()
        
        for group_id in group_ids:
            try:
                bot.send_message(group_id.strip(), f"📢 Broadcast from the owner:\n\n{text}")
            except Exception as e:
                print(f"Failed to send to {group_id}: {e}")

        bot.reply_to(message, "✅ Broadcast sent successfully!")

    @bot.message_handler(commands=['restart'])
    @owner_only
    def restart_bot(message):
        bot.reply_to(message, "♻️ Restarting bot...")
        os.execv(sys.executable, ['python3'] + sys.argv)

    @bot.message_handler(commands=['logs'])
    @owner_only
    def fetch_logs(message):
        try:
            with open("bot.log", "r") as log_file:
                logs = log_file.readlines()[-10:]  # Get last 10 log lines
            bot.reply_to(message, f"📜 Last 10 log entries:\n\n" + "".join(logs))
        except Exception as e:
            bot.reply_to(message, f"❌ Error reading logs: {e}")
