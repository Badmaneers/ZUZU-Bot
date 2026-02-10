import telebot
import os
import time
import random
import logging
import traceback
from openai import OpenAI
from helper import load_from_file
import memory
from config import (
    OPENROUTER_API_KEY, AI_MODEL, TEMPERATURE, TOP_P, MAX_RETRIES, 
    MEMORY_LIMIT, PROMPT_FILE
)
from bot_instance import bot

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ========== Load System Prompt ==========
def load_prompt():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    except FileNotFoundError:
        logging.warning("prompt.txt not found. Using default system prompt.")
        return "You are a sassy and engaging assistant. Respond like a human, keep context, and use natural conversational flow."
    except Exception as e:
        logging.error(f"Error loading prompt.txt: {e}")
        return "You are a sassy and engaging assistant. Respond like a human, keep context, and use natural conversational flow."

system_prompt = load_prompt()


# ========== AI Response Handling ==========
def process_ai_response(message, group_id=None, message_text=None):
    # Remove @mention from text if present
    clean_text = message.text.strip() if message.text else ""
    
    # Handle scheduled messages sent to groups
    if group_id is not None and message_text is not None:
        chat_id = group_id
        chat_type = "group"

        try:
            chat_memory = memory.chat_memory.get(None, chat_id, chat_type, [])
            conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text}
            ]

            for attempt in range(MAX_RETRIES):
                try:
                    response = client.chat.completions.create(
                        model=AI_MODEL,
                        messages=conversation,
                        temperature=TEMPERATURE,
                        top_p=TOP_P
                    )
                    if response.choices:
                        ai_reply = response.choices[0].message.content.strip()
                        bot.send_message(chat_id, ai_reply)
                        logging.info(f"Scheduled AI message sent to group {chat_id}")
                        return
                except Exception as e:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logging.error(f"AI backend error for scheduled message: {e}, retrying in {wait_time:.2f}s")
                    time.sleep(wait_time)

            logging.error(f"Failed to send scheduled AI message after {MAX_RETRIES} attempts")
            return
        except Exception as e:
            logging.error(f"Error processing scheduled AI message: {e}")
            return

    # Regular message processing
    try:
        if not message.text:
            bot.send_message(message.chat.id, "I can't respond to that kind of message. 😕")
            return

        chat_id = message.chat.id
        user_id = str(message.from_user.id)
        user_name = message.from_user.first_name
        chat_type = message.chat.type

        is_private = chat_type == "private"
        
        # Wake word triggers (no bot username checks)
        wake_words = ["zuzu", "#zuzu", "zuzu:", "zuzu,", "zuzu!"]
        message_text_lower = message.text.lower()

        # Check if any wake word is present anywhere in the message
        is_mentioned = any(wake in message_text_lower for wake in wake_words)


        is_reply_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user.id == bot.get_me().id
        )

        # In groups, only respond to mentions or replies
        if not is_private and not (is_reply_to_bot or is_mentioned):
            return

        # Choose the right memory context
        if is_private:
            chat_memory = memory.chat_memory.get(user_id, None, "private", [])
        else:
            chat_memory = memory.chat_memory.get(None, chat_id, chat_type, [])

        # Add user message
        chat_memory.append({"role": "user", "content": f"{user_name}: {clean_text}"})

        # Personalize system prompt for DMs
        system_message = system_prompt
        if is_private:
            system_message = f"{system_prompt} Always refer to the user by their name: {user_name}."

        conversation = [{"role": "system", "content": system_message}] + chat_memory[-MEMORY_LIMIT:]

        for attempt in range(MAX_RETRIES):
            try:
                response = client.chat.completions.create(
                    model=AI_MODEL,
                    messages=conversation,
                    temperature=TEMPERATURE,
                    top_p=TOP_P
                )

                if response.choices:
                    ai_reply = response.choices[0].message.content.strip()
                    chat_memory.append({"role": "assistant", "content": ai_reply})

                    if is_private:
                        memory.chat_memory[(user_id, None, "private")] = chat_memory[-MEMORY_LIMIT:]
                    else:
                        memory.chat_memory[(None, chat_id, chat_type)] = chat_memory[-MEMORY_LIMIT:]

                    memory.save_memory()

                    bot.send_message(
                        chat_id,
                        ai_reply,
                        reply_to_message_id=message.message_id if not is_private else None
                    )

                    logging.info(f"AI response sent to {'user' if is_private else 'group'} {chat_id}")
                    return

            except Exception as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.error(f"AI backend error: {e}, retrying in {wait_time:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)

        bot.send_message(chat_id, "Ugh, my brain lagged out. Try again later! 😭")
        logging.error(f"All {MAX_RETRIES} attempts failed for chat {chat_id}")

    except Exception as e:
        try:
            bot.send_message(message.chat.id, "Oops, something went wrong.")
            logging.error(f"AI response error: {e}")
            logging.error(traceback.format_exc())
        except:
            logging.critical("Critical error in error handler")

logging.info("Zuzu is online and ready to slay!")
# ========== Rate Limiting ==========