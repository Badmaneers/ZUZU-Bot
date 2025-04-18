import os
import json
import telebot

NOTES_DIR = "notes"
notes_enabled = True

if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

def get_notes_file(chat_id):
    return os.path.join(NOTES_DIR, f"{chat_id}.json")

def load_notes(chat_id):
    file_path = get_notes_file(chat_id)
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({"notes": {}, "pinned": None}, f)
    with open(file_path, "r") as f:
        return json.load(f)

def save_notes(chat_id, data):
    file_path = get_notes_file(chat_id)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def register_notes_handlers(bot):
    global notes_enabled

    @bot.message_handler(commands=['toggle_notes'])
    def toggle_notes(message):
        global notes_enabled
        notes_enabled = not notes_enabled
        status = "enabled" if notes_enabled else "disabled"
        bot.reply_to(message, f"📝 Notes feature has been {status}!")

    @bot.message_handler(commands=['save'])
    def save_note_handler(message):
        if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return

        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            bot.reply_to(message, "⚠️ Usage: `/save <title> <content>`")
            return

        chat_id = str(message.chat.id)
        title, content = parts[1].strip(), parts[2].strip()
        data = load_notes(chat_id)
        data["notes"][title] = content
        save_notes(chat_id, data)
        bot.reply_to(message, f"✅ Note '{title}' saved successfully!")

    @bot.message_handler(commands=['note'])
    def get_note_handler(message):
        if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return

        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/note <title>`")
            return

        chat_id = str(message.chat.id)
        title = parts[1].strip()
        data = load_notes(chat_id)

        if title in data["notes"]:
            bot.reply_to(message, data["notes"][title], parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['delnote'])
    def delete_note_handler(message):
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/delnote <title>`")
            return

        chat_id = str(message.chat.id)
        title = parts[1].strip()
        data = load_notes(chat_id)

        if title in data["notes"]:
            del data["notes"][title]
            if data["pinned"] == title:
                data["pinned"] = None
            save_notes(chat_id, data)
            bot.reply_to(message, f"🗑️ Note '{title}' deleted successfully!")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['notes'])
    def list_notes_handler(message):
        if not notes_enabled:
            bot.reply_to(message, "⚠️ Notes feature is disabled!")
            return

        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        if data["notes"]:
            note_titles = "\n".join(f"- `{title}`" for title in data["notes"])
            bot.reply_to(
                message,
                f"📝 Saved Notes:\n\n{note_titles}\n\nUse `/note <title>` to retrieve a note.",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, "📭 No saved notes found!")

    @bot.message_handler(commands=['pinnote'])
    def pin_note_handler(message):
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/pinnote <title>`")
            return

        chat_id = str(message.chat.id)
        title = parts[1].strip()
        data = load_notes(chat_id)

        if title in data["notes"]:
            data["pinned"] = title
            save_notes(chat_id, data)
            bot.reply_to(message, f"📌 Note '{title}' has been pinned!")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['pinned'])
    def get_pinned_note(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)

        if data["pinned"] and data["pinned"] in data["notes"]:
            title = data["pinned"]
            bot.reply_to(message, f"📌 *Pinned Note* `{title}`:\n\n{data['notes'][title]}", parse_mode="Markdown")
        else:
            bot.reply_to(message, "📭 No pinned note found.")

    print("✅ Notes handlers registered.")
