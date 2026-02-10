import telebot
import random
import json
import time
import threading
from datetime import datetime, timedelta
from openai import OpenAI
from config import OPENROUTER_API_KEY, AI_MODEL, MEMORY_LIMIT
from core.bot_instance import bot
from core.helper import load_from_file
import core.memory as memory

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Magic fortune using AI
def fortune(message):
    question = message.text.replace("/fortune", "").strip()

    if not question:
        bot.reply_to(message, "Ask me a question, babe! 😏")
        return
    
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "system", "content": "You are a fortune teller"},
                  {"role": "user", "content": question}]
    )
    answer = response.choices[0].message.content.strip()
    bot.reply_to(message, f"🔮 {answer}")

    # Save to memory
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        is_private = message.chat.type == "private"
        
        mem_list = memory.chat_memory.get(user_id if is_private else None, chat_id, message.chat.type, [])
        mem_list.append({"role": "user", "content": f"{message.from_user.first_name}: /fortune {question}"})
        mem_list.append({"role": "assistant", "content": answer})
        
        key = (user_id, None, "private") if is_private else (None, chat_id, message.chat.type)
        memory.chat_memory[key] = mem_list[-MEMORY_LIMIT:]
        memory.save_memory()
    except Exception as e:
        print(f"Error saving fortune memory: {e}")
