import telebot
import os
import time
import random
import logging
import traceback
from openai import OpenAI
from helper import load_from_file
import memory
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="bot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Get environment variables with validation
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Validate critical environment variables before proceeding
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN is not set. Exiting...")
    raise ValueError("Error: BOT_TOKEN is not set. Please check your .env file.")

if not OPENROUTER_API_KEY:
    logging.critical("OPENROUTER_API_KEY is not set. Exiting...")
    raise ValueError("Error: OPENROUTER_API_KEY is not set. Please check your .env file.")

# Only initialize the bot after validating the token
bot = telebot.TeleBot(BOT_TOKEN)

# Load other environment variables with defaults
AI_MODEL = os.getenv("AI_MODEL")
TEMPERATURE = float(os.getenv("AI_TEMPERATURE"))
TOP_P = float(os.getenv("AI_TOP_P"))
MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES"))
MEMORY_LIMIT = int(os.getenv("MEMORY_LIMIT"))  # Number of messages to keep

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ========== Load System Prompt ==========
def load_prompt():
    try:
        with open("bot/prompt.txt", "r", encoding="utf-8") as file:
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
    """Handles AI responses in groups (only when replied to) and in DMs (always).
    
    Args:
        message: The message object from Telegram
        group_id: Optional group ID for direct AI generation to groups
        message_text: Optional message text when not using a real message object
    """
    # Special case for scheduled messages directly to groups
    if group_id is not None and message_text is not None:
        chat_id = group_id
        chat_type = "group"  # Assume group chat for scheduled messages
        
        try:
            # Get shared group memory
            chat_memory = memory.chat_memory.get(None, chat_id, chat_type, [])
            
            # Create a simplified conversation with just the system prompt and request
            conversation = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_text}
            ]
            
            # Process with AI and send
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
        # Ensure message has text
        if not message.text:
            bot.send_message(message.chat.id, "I can't respond to that kind of message. 😕")
            return
            
        # Extract message details
        chat_id = message.chat.id
        user_id = str(message.from_user.id)
        user_name = message.from_user.first_name
        chat_type = message.chat.type  # "private", "group", "supergroup"

        is_private = chat_type == "private"
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id if message.reply_to_message else False

        # In groups, only respond if the bot is directly replied to
        if not is_private and not is_reply_to_bot:
            return  

        # For private chats: use user-specific memory
        # For group chats: use shared group memory
        if is_private:
            chat_memory = memory.chat_memory.get(user_id, None, "private", [])
        else:
            # Get shared group memory instead of user-specific
            chat_memory = memory.chat_memory.get(None, chat_id, chat_type, [])
        
        # Add user's message to memory with their name
        chat_memory.append({"role": "user", "content": f"{user_name}: {message.text}"})

        # Create conversation context with system prompt
        system_message = system_prompt
        if is_private:
            # Only add name personalization in private chats
            system_message = f"{system_prompt} Always refer to the user by their name: {user_name}."
        
        conversation = [{"role": "system", "content": system_message}] + chat_memory[-MEMORY_LIMIT:]

        # Try to get response with exponential backoff
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
                    
                    # Store response in memory
                    chat_memory.append({"role": "assistant", "content": ai_reply})
                    
                    # Update memory based on chat type
                    if is_private:
                        memory.chat_memory[(user_id, None, "private")] = chat_memory[-MEMORY_LIMIT:]
                    else:
                        memory.chat_memory[(None, chat_id, chat_type)] = chat_memory[-MEMORY_LIMIT:]
                    
                    # Save to database
                    memory.save_memory()

                    # Send response
                    bot.send_message(
                        chat_id, 
                        ai_reply, 
                        reply_to_message_id=message.message_id if not is_private else None
                    )
                    
                    if is_private:
                        logging.info(f"AI response sent to user {user_id} in private")
                    else:
                        logging.info(f"AI response sent in group {chat_id}")
                    return
                
            except Exception as e:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.error(f"AI backend error: {e}, retrying in {wait_time:.2f}s (Attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait_time)

        # If all retries failed
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
