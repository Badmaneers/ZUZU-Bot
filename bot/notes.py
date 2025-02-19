import os
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

NOTES_FILE = "notes.json"

# Ensure notes file exists
def load_notes():
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w") as f:
            json.dump({}, f)
    with open(NOTES_FILE, "r") as f:
        return json.load(f)

def save_notes(notes):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=4)

def register_notes_handlers(bot):
    notes = load_notes()

    @bot.message_handler(commands=['save'])
    def save_note(message):
        """Saves a note with a title, supporting text, media, and inline buttons."""
        chat_id = str(message.chat.id)

        if message.reply_to_message:
            parts = message.text.split(" ", 1)
            if len(parts) < 2:
                bot.reply_to(message, "⚠️ Usage: Reply to a message with `/save <title>`")
                return
            title = parts[1].strip()

            # Handling text messages
            if message.reply_to_message.content_type == "text":
                content = message.reply_to_message.text
                buttons = extract_buttons(content)

                # ✅ If only buttons exist, set the title as the message in **bold**
                text_content = remove_button_text(content)
                if not text_content:
                    text_content = f"*{title}*"

                note_data = {"text": text_content, "buttons": buttons}

            else:
                # Handling media messages
                file_info = {
                    "file_id": getattr(message.reply_to_message, message.reply_to_message.content_type).file_id,
                    "content_type": message.reply_to_message.content_type,
                    "caption": message.reply_to_message.caption or ""
                }
                buttons = extract_buttons(file_info["caption"])

                # ✅ If only buttons exist, set the title as the message in **bold**
                text_content = remove_button_text(file_info["caption"])
                if not text_content:
                    text_content = f"*{title}*"

                note_data = {"text": text_content, "buttons": buttons, "file": file_info}

        else:
            # Handling text-based saves
            parts = message.text.split(" ", 2)
            if len(parts) < 3:
                bot.reply_to(message, "⚠️ Usage: `/save <title> <content>` or reply to a message with `/save <title>`")
                return
            
            title = parts[1].strip()
            content = parts[2].strip()
            buttons = extract_buttons(content)

            # ✅ If only buttons exist, set the title as the message in **bold**
            text_content = remove_button_text(content)
            if not text_content:
                text_content = f"*{title}*"

            note_data = {"text": text_content, "buttons": buttons}

        if chat_id not in notes:
            notes[chat_id] = {}
        notes[chat_id][title] = note_data
        save_notes(notes)
        bot.reply_to(message, f"✅ Note '{title}' saved successfully! Use `/note {title}` to view it.", parse_mode="Markdown")

    @bot.message_handler(commands=['note'])
    def get_note(message):
     """Retrieves a saved note and replies to the user with buttons if available."""
     parts = message.text.split(" ", 1)
     if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: `/note <title>`")
        return
    
     title = parts[1].strip()
     chat_id = str(message.chat.id)

     if chat_id in notes and title in notes[chat_id]:
        note = notes[chat_id][title]
        markup = InlineKeyboardMarkup()
        for btn in note.get("buttons", []):
            markup.add(InlineKeyboardButton(btn["text"], url=btn["url"]))

        text = note["text"].strip() if note["text"].strip() else f"*{title}*"

        # ✅ Reply to the original command instead of sending a new message
        if "file" in note:
            file_info = note["file"]
            content_type = file_info["content_type"]
            caption = text  # Use the processed text

            if content_type == "photo":
                bot.send_photo(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup, parse_mode="Markdown", reply_to_message_id=message.message_id)
            elif content_type == "audio":
                bot.send_audio(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup, parse_mode="Markdown", reply_to_message_id=message.message_id)
            elif content_type == "video":
                bot.send_video(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup, parse_mode="Markdown", reply_to_message_id=message.message_id)
            elif content_type == "document":
                bot.send_document(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup, parse_mode="Markdown", reply_to_message_id=message.message_id)
            elif content_type == "voice":
                bot.send_voice(message.chat.id, file_info["file_id"], reply_markup=markup, reply_to_message_id=message.message_id)
            else:
                bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, text, reply_markup=markup, parse_mode="Markdown")
     else:
        bot.reply_to(message, "❌ Note not found! Use `/save` to create one.")


    def extract_buttons(text):
        """Extracts inline buttons from text and ensures correct Telegram button format."""
        buttons = []
        lines = text.split("\n")
        for line in lines:
            if "](" in line:  # Ensures correct button format
                try:
                    start = line.find("[")
                    mid = line.find("](", start)
                    end = line.find(")", mid)
                    if start != -1 and mid != -1 and end != -1:
                        btn_text = line[start+1:mid]
                        btn_url = line[mid+2:end]
                        if btn_url.startswith("http://") or btn_url.startswith("https://"):  # Ensure valid URL
                            buttons.append({"text": btn_text.strip(), "url": btn_url.strip()})
                except Exception:
                    continue
        return buttons

    def remove_button_text(text):
        """Removes button formatting from saved note content."""
        lines = text.split("\n")
        processed_lines = [line for line in lines if not ("](" in line and ("http://" in line or "https://" in line))]
        return "\n".join(processed_lines).strip()

    @bot.message_handler(commands=['delnote'])
    def delete_note(message):
        """Deletes a saved note."""
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/delnote <title>`")
            return
        title = parts[1].strip()
        chat_id = str(message.chat.id)

        if chat_id in notes and title in notes[chat_id]:
            del notes[chat_id][title]
            save_notes(notes)
            bot.reply_to(message, f"🗑️ Note '{title}' deleted successfully!")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['notes'])
    def list_notes(message):
        """Lists all saved notes."""
        chat_id = str(message.chat.id)
        if chat_id in notes and notes[chat_id]:
            note_titles = "\n".join(f"📌 {title}" for title in notes[chat_id])
            bot.reply_to(message, f"📝 Saved Notes:\n\n{note_titles}")
        else:
            bot.reply_to(message, "📭 No saved notes found!")

