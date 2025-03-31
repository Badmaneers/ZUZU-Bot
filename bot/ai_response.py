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
        return "You are a sassy and engaging assistant. Respond like a human, keep context, and use natural conversational flow."

system_prompt = load_prompt()

# ========== AI Response Handling ==========
def process_ai_response(message):
    """Handles AI responses in groups (only when replied to) and in DMs (always)."""
    try:
        chat_id = message.chat.id
        user_id = str(message.from_user.id)  # Ensure consistency in memory keys
        user_name = message.from_user.first_name
        chat_type = message.chat.type  # "private", "group", "supergroup"

        is_private = chat_type == "private"
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id if message.reply_to_message else False

        # ✅ In groups, only respond if the bot is directly replied to
        if not is_private and not is_reply_to_bot:
            return  

        # ✅ Retrieve or initialize user memory
        user_memory = memory.chat_memory.get(user_id, [])
        user_memory.append({"role": "user", "content": f"{user_name}: {message.text}"})

        # ✅ Create conversation context
        conversation = [{"role": "system", "content": f"{system_prompt} Always refer to the user by their name: {user_name}."}] + user_memory[-15:]

        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model="meta-llama/llama-3.3-70b-instruct:free",
                    messages=conversation,
                    temperature=0.9,
                    top_p=0.9
                )

                if response.choices:
                    ai_reply = response.choices[0].message.content.strip()
                    
                    # ✅ Store response in memory
                    user_memory.append({"role": "assistant", "content": ai_reply})
                    memory.chat_memory[user_id] = user_memory[-15:]  # Keep last 15 messages
                    memory.save_memory()  # Save instantly

                    # ✅ Send response, but don’t force reply in DMs
                    bot.send_message(chat_id, ai_reply, reply_to_message_id=message.message_id if not is_private else None)
                    return
                
            except Exception as e:
                print(f"AI backend error: {e}, retrying... ({attempt + 1})")
                time.sleep(2)

        bot.send_message(chat_id, "Ugh, my brain lagged out. Try again later! 😭")

    except Exception as e:
        bot.send_message(chat_id, "Oops, something went wrong.")
        print(f"AI error: {e}")

print("Zuzu is online and ready to slay!")
