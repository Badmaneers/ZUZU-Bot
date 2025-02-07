import telebot
import os
import time
from openai import OpenAI
from helper import load_from_file 
import memory

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENROUTER_API_KEY is not set.")

# ========== Load System Prompt ==========
def load_prompt():
    try:
        with open("bot/prompt.txt", "r", encoding="utf-8") as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error loading prompt.txt: {e}")
        return "You are a sassy and engaging assistant."

system_prompt = load_prompt()

# ========== AI Chat System with Faster Processing ==========
def process_ai_response(message, user_id, chat_id):
    """Handles AI responses efficiently and fixes lag issues."""
    try:
        # ✅ Step 1: Append user message to chat history FIRST
        if user_id not in memory.chat_memory:
            memory.chat_memory[user_id] = []
        memory.chat_memory[user_id].append({"role": "user", "content": message.text})

        conversation = [{"role": "system", "content": system_prompt}] + memory.chat_memory[user_id]

        for attempt in range(2):  # Retry up to 2 times
            try:
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.1-405b-instruct:free",
                    messages=conversation
                )

                if response.choices:
                    ai_reply = response.choices[0].message.content.strip()

                    # ✅ Step 2: Append AI response IMMEDIATELY to chat history
                    memory.chat_memory[user_id].append({"role": "assistant", "content": ai_reply})
                    memory.chat_memory[user_id] = memory.chat_memory[user_id][-5:]  # Keep last 5 messages
                    memory.save_memory()

                    bot.send_message(chat_id, ai_reply, reply_to_message_id=message.message_id)
                    return  # Exit after successful response
                
            except Exception as e:
                print(f"AI backend error: {e}, retrying... ({attempt + 1})")
                time.sleep(2)  # Short delay before retrying

        # If all retries fail, send an error message
        bot.send_message(chat_id, "Oops, my brain lagged out. Try again later! 😭")

    except Exception as e:
        bot.send_message(chat_id, "Oops, something went wrong.")
        print(f"AI error: {e}")

        
                       

print("Sassy Telegram bot is running...")