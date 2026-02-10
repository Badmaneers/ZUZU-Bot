import telebot
import os
import time
import random
import logging
import traceback
from openai import OpenAI
from core.helper import load_from_file
import core.memory as memory
from config import (
    OPENROUTER_API_KEY, AI_MODEL, TEMPERATURE, TOP_P, MAX_RETRIES, 
    MEMORY_LIMIT, PROMPT_FILE
)
from core.bot_instance import bot

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


# ========== Helper for specific requests ==========
def get_ai_reply(system_msg, user_msg, max_tokens=150):
    """
    Generates a single AI response without memory context.
    Useful for one-off commands like /roast or /motivate.
    """
    try:
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
            temperature=0.8, # Slightly creative
            max_tokens=max_tokens
        )
        
        if response.choices:
            return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error in get_ai_reply: {e}")
    
    return None

# ========== AI Response Handling ==========
def process_ai_response(message, group_id=None, message_text=None):
    # Remove @mention from text if present
    clean_text = ""
    if message and hasattr(message, 'text') and message.text:
        clean_text = message.text.strip()
    
    message_thread_id = None

    # Handle scheduled messages sent to groups
    if group_id is not None and message_text is not None:
        chat_id = group_id
        chat_type = "group" # Assume group for scripted messages
        user_id = None
        user_name = "System"
        clean_text = message_text
        is_private = False
    else:
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        chat_type = message.chat.type
        is_private = chat_type == "private"
        message_thread_id = message.message_thread_id if hasattr(message, 'message_thread_id') and message.chat.is_forum else None

    # Define wake words
    wake_words = ["zuzu", "zuzu-bot", "bot", "assistant"]
    message_text_lower = clean_text.lower()
    
    try:
        # Rate limiting logic using helper if needed, or simple check?
        # Keeping it simple as before
        pass

        # Check if any wake word is present anywhere in the message
        is_mentioned = any(wake in message_text_lower for wake in wake_words)


        is_reply_to_bot = (
            message.reply_to_message and
            message.reply_to_message.from_user.id == bot.get_me().id
        ) if hasattr(message, 'reply_to_message') and message.reply_to_message else False

        # In groups, only respond to mentions or replies
        # Exception: if group_id is provided, we force send
        if group_id is None and not is_private and not (is_reply_to_bot or is_mentioned):
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
                        message_thread_id=message_thread_id,
                        reply_to_message_id=message.message_id if hasattr(message, 'message_id') and not is_private else None
                    )

                    logging.info(f"AI response sent to {'user' if is_private else 'group'} {chat_id}")
                    return

            except Exception as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.error(f"AI backend error: {e}, retrying in {wait_time:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)

        if group_id is None: # Only complain if prompted by user
            bot.send_message(chat_id, "Ugh, my brain lagged out. Try again later! 😭")
        logging.error(f"All {MAX_RETRIES} attempts failed for chat {chat_id}")

    except Exception as e:
        try:
            if hasattr(message, 'chat'):
                bot.send_message(message.chat.id, "Oops, something went wrong.")
            logging.error(f"AI response error: {e}")
            logging.error(traceback.format_exc())
        except:
            logging.critical("Critical error in error handler")

logging.info("Zuzu is online and ready to slay!")
