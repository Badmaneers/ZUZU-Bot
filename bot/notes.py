import os
import json
import telebot

NOTES_FILE = "notes.json"
notes_enabled = True  # Default to enabled

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
    global notes_enabled

    @bot.message_handler(commands=['toggle_notes'])
    def toggle_notes(message):
        """Enable or disable the notes feature (Admins only)."""
        global notes_enabled
        notes_enabled = not notes_enabled
        status = "enabled" if notes_enabled else "disabled"
        bot.reply_to(message, f"📝 Notes feature has been {status}!")

    @bot.message_handler(commands=['save'])
    def save_note_handler(message):
        """Saves a note."""
        if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return
        
        notes = load_notes()
        chat_id = str(message.chat.id)
        parts = message.text.split(" ", 2)

        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Usage: `/save <title> <content>`")
            return

        title, content = parts[1].strip(), parts[2].strip()

        if chat_id not in notes:
            notes[chat_id] = {}
        notes[chat_id][title] = {"text": content}
        save_notes(notes)
        bot.reply_to(message, f"✅ Note '{title}' saved successfully!")

    @bot.message_handler(commands=['note'])
    def get_note_handler(message):
        """Retrieves a note."""
        if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return

        notes = load_notes()
        chat_id = str(message.chat.id)
        parts = message.text.split(" ", 1)

        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/note <title>`")
            return

        title = parts[1].strip()
        if chat_id in notes and title in notes[chat_id]:
            bot.reply_to(message, notes[chat_id][title]["text"], parse_mode="MarkdownV2")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['delnote'])
    def delete_note_handler(message):
        """Deletes a saved note."""
        notes = load_notes()
        chat_id = str(message.chat.id)
        parts = message.text.split(" ", 1)

        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/delnote <title>`")
            return

        title = parts[1].strip()
        if chat_id in notes and title in notes[chat_id]:
            del notes[chat_id][title]
            save_notes(notes)
            bot.reply_to(message, f"🗑️ Note '{title}' deleted successfully!")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['notes'])
    def list_notes_handler(message):
     if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return
            
     """Lists all saved notes."""
     notes = load_notes()
     chat_id = str(message.chat.id)

     if chat_id in notes and notes[chat_id]:
        note_titles = "\n".join(f"- `{title}`" for title in notes[chat_id])  # No need to escape backticks
        bot.reply_to(
            message, 
            f"📝 Saved Notes:\n\n{note_titles}\n\nTap and copy the note title and use `/note example_note`.", 
            parse_mode="Markdown"  # Switch to legacy Markdown
        )
     else:
        bot.reply_to(message, "📭 No saved notes found!")

    print("✅ Notes handlers registered.")
