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
     """
     Save a note with a title.
     - If replying to a message, the note content comes from the replied message.
     - Otherwise, expect /save <title> <content>.
     - Supports inline buttons in the format: [Button Text](https://...)
     """
     chat_id = str(message.chat.id)

     if message.reply_to_message:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: Reply to a message with `/save <title>`")
            return
        title = parts[1].strip()
        # If the replied message is text, use its text.
        if message.reply_to_message.content_type == "text":
            content = message.reply_to_message.text
            note_data = {"text": content, "buttons": extract_buttons(content)}
            note_data["text"] = remove_button_text(content)
        else:
            # For media messages, store file info.
            ctype = message.reply_to_message.content_type
            file_info = {
                "file_id": getattr(message.reply_to_message, ctype).file_id,
                "content_type": ctype,
                "caption": message.reply_to_message.caption or ""
            }
            content = file_info["caption"]
            note_data = {"text": content, "buttons": extract_buttons(content), "file": file_info}
            note_data["text"] = remove_button_text(content)
     else:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Usage: `/save <title> <content>` (or reply to a message with `/save <title>`)") 
            return
        title = parts[1].strip()
        content = parts[2].strip()
        note_data = {"text": content, "buttons": extract_buttons(content)}
        note_data["text"] = remove_button_text(content)

     if chat_id not in notes:
        notes[chat_id] = {}
     notes[chat_id][title] = note_data
     save_notes(notes)
     bot.reply_to(message, f"✅ Note '{title}' saved successfully! Use `/note {title}` to view it.")


    def extract_buttons(note_text):
     """Extracts inline buttons from note_text and returns a list of button dictionaries."""
     buttons = []
     lines = note_text.split("\n")
     for line in lines:
        if "](" in line:
            try:
                start = line.find("[")
                mid = line.find("](", start)
                end = line.find(")", mid)
                if start != -1 and mid != -1 and end != -1:
                    btn_text = line[start+1:mid]
                    btn_url = line[mid+2:end]
                    if btn_url.startswith("http://") or btn_url.startswith("https://"):
                        buttons.append({"text": btn_text.strip(), "url": btn_url.strip()})
            except Exception:
                continue
     return buttons

    def remove_button_text(note_text):
     """Removes lines that define inline buttons from note_text."""
     lines = note_text.split("\n")
     processed_lines = [line for line in lines if not ("](" in line and ("http://" in line or "https://" in line))]
     return "\n".join(processed_lines).strip()

    @bot.message_handler(commands=['note'])
    def get_note(message):
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

        # If the note only contains buttons, set a default text
        text = note["text"].strip() if note["text"].strip() else "📝 Click the buttons below:"

        # Send saved file if it's a media note
        if "file" in note:
            file_info = note["file"]
            content_type = file_info["content_type"]
            caption = text  # Use the processed text

            if content_type == "photo":
                bot.send_photo(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
            elif content_type == "audio":
                bot.send_audio(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
            elif content_type == "video":
                bot.send_video(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
            elif content_type == "document":
                bot.send_document(message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
            elif content_type == "voice":
                bot.send_voice(message.chat.id, file_info["file_id"], reply_markup=markup)
            else:
                bot.send_message(message.chat.id, text, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
      else:
        bot.reply_to(message, "❌ Note not found! Use `/save` to create one.")


    @bot.message_handler(commands=['notes'])
    def list_notes(message):
        chat_id = str(message.chat.id)
        if chat_id in notes and notes[chat_id]:
            markup = InlineKeyboardMarkup()
            for title in notes[chat_id].keys():
                markup.add(InlineKeyboardButton(title, callback_data=f"note_{title}"))
            bot.reply_to(message, "📌 **Saved Notes:**", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ No notes found! Save one using `/save`.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("note_"))
    def callback_note_handler(call):
        chat_id = str(call.message.chat.id)
        title = call.data.replace("note_", "").strip()

        if chat_id in notes and title in notes[chat_id]:
            note = notes[chat_id][title]
            markup = InlineKeyboardMarkup()
            for btn in note.get("buttons", []):
                markup.add(InlineKeyboardButton(btn["text"], url=btn["url"]))

            if "file" in note:
                file_info = note["file"]
                content_type = file_info["content_type"]
                caption = note["text"]

                if content_type == "photo":
                    bot.send_photo(call.message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
                elif content_type == "audio":
                    bot.send_audio(call.message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
                elif content_type == "video":
                    bot.send_video(call.message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
                elif content_type == "document":
                    bot.send_document(call.message.chat.id, file_info["file_id"], caption=caption, reply_markup=markup)
                elif content_type == "voice":
                    bot.send_voice(call.message.chat.id, file_info["file_id"], reply_markup=markup)
                else:
                    bot.send_message(call.message.chat.id, note["text"], reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, note["text"], reply_markup=markup)
        else:
            bot.answer_callback_query(call.id, "❌ Note not found!")

    @bot.message_handler(commands=['delnote'])
    def delete_note(message):
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


