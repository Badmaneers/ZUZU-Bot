import telebot
import os
from openai import OpenAI
import os
from helper import load_from_file 
import memory
import time
import sys
import signal

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENROUTER_API_KEY is not set.")
    
# ========== AI Chat System with Retries & Async Handling ========== #

def load_prompt():
    try:
        with open("bot/prompt.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error loading prompt.txt: {e}")
        return "You are a sassy and engaging assistant."
        
system_prompt = load_prompt()

def process_ai_response(message, user_id, chat_id):
    """Handle AI responses with retries for failures."""
    try:
        conversation = [{"role": "system", "content": system_prompt}] + memory.chat_memory.get(user_id, [])
        
        for _ in range(2):  # Retry up to 2 times
            try:
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.1-405b-instruct:free",
                    messages=conversation
                )
                if response.choices:
                    ai_reply = response.choices[0].message.content.strip()
                    memory.chat_memory[user_id].append({"role": "assistant", "content": ai_reply})
                    memory.save_memory()
                    bot.send_message(chat_id, ai_reply, reply_to_message_id=message.message_id)
                    return
            except Exception as e:
                print(f"AI backend error: {e}, retrying...")
                time.sleep(2)  # Wait before retrying
        bot.send_message(chat_id, "Oops, my brain lagged out. Try again later! 😭")
    
    except Exception as e:
        bot.send_message(chat_id, "Oops, something went wrong.")
        print(f"AI error: {e}")
        
                          
# ========== Start Bot ========== #
def handle_exit(signal_number, frame):
    print("Saving memory before exit...")
    memory.save_memory()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

print("Sassy Telegram bot is running...")