import telebot
import random
import json
import time
import threading
from datetime import datetime, timedelta
from openai import OpenAI
from config import OPENROUTER_API_KEY, AI_MODEL
from core.bot_instance import bot
from core.helper import load_from_file

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
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=[{"role": "system", "content": "You are a fortune teller"},
                  {"role": "user", "content": question}]
    )
    answer = response.choices[0].message.content.strip()
    bot.reply_to(message, answer)