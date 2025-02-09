import telebot
import os
import random
import json
import time
import threading
import zlib
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

if not BOT_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Error: BOT_TOKEN or OPENROUTER_API_KEY is not set.")

# Function to load data from text files
def load_from_file(filename, default_list=None):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return default_list or []

# Magic fortune using AI
@bot.message_handler(commands=['fortune'])
def fortune(message):
    question = message.text.replace("/fortune", "").strip()
    if not question:
        bot.reply_to(message, "Ask me a question, babe! 😏")
        return
    
    response = client.chat.completions.create(
        model="meta-llama/llama-3.1-405b-instruct:free",
        messages=[{"role": "system", "content": "You are a fortune teller"},
                  {"role": "user", "content": question}]
    )
    answer = response.choices[0].message.content.strip()
    bot.reply_to(message, answer)