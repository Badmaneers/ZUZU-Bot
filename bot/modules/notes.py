import os
import json
import re
from core.bot_instance import bot
from modules.moderations import is_admin

NOTES_DIR = "notes"

if not os.path.exists(NOTES_DIR):
    os.makedirs(NOTES_DIR)

def get_notes_file(chat_id):
    return os.path.join(NOTES_DIR, f"{chat_id}.json")

def load_notes(chat_id):
    file_path = get_notes_file(chat_id)
    if not os.path.exists(file_path):
        # Default structure with 'enabled' set to True
        return {"notes": {}, "pinned": None, "enabled": True}
        
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            # Ensure compatibility with old files
            if "enabled" not in data:
                data["enabled"] = True
            return data
    except Exception:
         return {"notes": {}, "pinned": None, "enabled": True}

def save_notes_to_file(chat_id, data):
    file_path = get_notes_file(chat_id)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def check_perm(message):
    """Returns True if user is admin or chat is private"""
    if message.chat.type == "private":
        return True
    try:
        return is_admin(message.chat.id, message.from_user.id)
    except Exception:
        # Fallback if checks fail (e.g. bot not admin so can't see admins)
        return False

def register_notes_handlers(bot):

    def send_note(chat_id, note_data, reply_to=None):
        """Helper to send a note based on its type"""
        if isinstance(note_data, str):
            # Legacy string format support
            bot.send_message(chat_id, note_data, parse_mode="Markdown", reply_to_message_id=reply_to)
            return

        msg_type = note_data.get("type", "text")
        content = note_data.get("content") or ""
        file_id = note_data.get("file_id")

        try:
            if msg_type == "text":
                bot.send_message(chat_id, content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "photo":
                bot.send_photo(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "video":
                bot.send_video(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "document":
                bot.send_document(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "sticker":
                bot.send_sticker(chat_id, file_id, reply_to_message_id=reply_to)
            elif msg_type == "animation":
                bot.send_animation(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "audio":
                bot.send_audio(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            elif msg_type == "voice":
                bot.send_voice(chat_id, file_id, caption=content, parse_mode="Markdown", reply_to_message_id=reply_to)
            else:
                 bot.send_message(chat_id, "⚠️ Content type not fully supported yet.", reply_to_message_id=reply_to)
        except Exception as e:
            bot.send_message(chat_id, f"⚠️ Failed to send note: {e}", reply_to_message_id=reply_to)
    
    @bot.message_handler(commands=['toggle_notes'])
    def toggle_notes(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 You need to be an admin to do this!")
            return
            
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        data["enabled"] = not data["enabled"]
        save_notes_to_file(chat_id, data)
        
        status = "enabled" if data["enabled"] else "disabled"
        bot.reply_to(message, f"📝 Notes feature has been {status} for this chat!")

    @bot.message_handler(commands=['save'])
    def save_note_handler(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        
        if not data["enabled"]:
            if check_perm(message):
                 # Admins can see why it failed
                 bot.reply_to(message, "⚠️ Notes are disabled in this chat. Enable them with /toggle_notes")
            return

        if not check_perm(message):
            bot.reply_to(message, "🚫 Only admins can save notes!")
            return

        args = message.text.split(None, 2)
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Usage: `/save <note_name> [content]` or reply to a message.")
            return

        note_name = args[1].lower() # Notes are lowercase
        note_content = None
        note_type = "text"
        file_id = None
        
        # Check if reply to a message
        if message.reply_to_message:
            reply = message.reply_to_message
            if reply.text:
                note_content = reply.text
                note_type = "text"
            elif reply.photo:
                note_type = "photo"
                file_id = reply.photo[-1].file_id
                note_content = reply.caption
            elif reply.video:
                note_type = "video"
                file_id = reply.video.file_id
                note_content = reply.caption
            elif reply.document:
                note_type = "document"
                file_id = reply.document.file_id
                note_content = reply.caption
            elif reply.sticker:
                note_type = "sticker"
                file_id = reply.sticker.file_id
            elif reply.animation: # GIF
                note_type = "animation"
                file_id = reply.animation.file_id
                note_content = reply.caption
            elif reply.audio:
                note_type = "audio"
                file_id = reply.audio.file_id
                note_content = reply.caption
            elif reply.voice:
                note_type = "voice"
                file_id = reply.voice.file_id
                note_content = reply.caption
            else:
                 bot.reply_to(message, "⚠️ This media type is not supported yet.")
                 return
        
        elif len(args) == 3:
            # Inline text note: /save name content...
            note_content = args[2]
            note_type = "text"
        else:
             bot.reply_to(message, "⚠️ You need to provide content or reply to a message.")
             return

        # Prepare object
        note_data = {
            "type": note_type,
            "content": note_content,
            "file_id": file_id
        }

        data["notes"][note_name] = note_data
        save_notes_to_file(chat_id, data)
        bot.reply_to(message, f"✅ Note `{note_name}` saved successfully!", parse_mode="Markdown")

    @bot.message_handler(commands=['note', 'get'])
    def get_note_handler(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        
        if not data["enabled"]:
            return

        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/note <title>`")
            return

        title = parts[1].strip().lower()

        if title in data["notes"]:
            send_note(chat_id, data["notes"][title], reply_to=message.message_id)
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['delnote', 'clear'])
    def delete_note_handler(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Only admins can delete notes!")
            return
            
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)

        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/delnote <title>`")
            return

        title = parts[1].strip().lower()

        if title == "all" and message.text.startswith("/clear"):
             data["notes"] = {}
             data["pinned"] = None
             save_notes_to_file(chat_id, data)
             bot.reply_to(message, "🗑️ All notes deleted successfully!")
             return

        if title in data["notes"]:
            del data["notes"][title]
            if data["pinned"] == title:
                data["pinned"] = None
            save_notes_to_file(chat_id, data)
            bot.reply_to(message, f"🗑️ Note `{title}` deleted successfully!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['notes'])
    def list_notes_handler(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        
        if not data["enabled"]:
            return

        if data["notes"]:
            note_len = len(data["notes"])
            # Format nicely
            note_list = sorted(data["notes"].keys())
            notes_str = "\n".join(f"- `{n}`" for n in note_list)
            
            bot.reply_to(
                message,
                f"📝 **Saved Notes** ({note_len}):\n\n{notes_str}\n\nUse `#notename` to retrieve.",
                parse_mode="Markdown"
            )
        else:
            bot.reply_to(message, "📭 No saved notes found!")

    @bot.message_handler(commands=['pinnote'])
    def pin_note_handler(message):
        if not check_perm(message):
            bot.reply_to(message, "🚫 Only admins can pin notes!")
            return

        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Usage: `/pinnote <title>`")
            return

        chat_id = str(message.chat.id)
        title = parts[1].strip().lower()
        data = load_notes(chat_id)

        if title in data["notes"]:
            data["pinned"] = title
            save_notes_to_file(chat_id, data)
            bot.reply_to(message, f"📌 Note `{title}` has been pinned!", parse_mode="Markdown")
        else:
            bot.reply_to(message, "❌ Note not found!")

    @bot.message_handler(commands=['pinned'])
    def get_pinned_note(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)

        if data["pinned"] and data["pinned"] in data["notes"]:
            title = data["pinned"]
            send_note(chat_id, data["notes"][title], reply_to=message.message_id)
        else:
            bot.reply_to(message, "📭 No pinned note found.")

    # Hashtag handler (e.g., #rules, #welcome)
    @bot.message_handler(func=lambda msg: msg.text and msg.text.startswith("#"))
    def hashtag_note_handler(message):
        chat_id = str(message.chat.id)
        data = load_notes(chat_id)
        
        if not data["enabled"]:
            return
            
        # Extract the first hashtag word
        match = re.search(r"#(\w+)", message.text)
        if not match:
            return
            
        title = match.group(1).lower()
        
        if title in data["notes"]:
            send_note(chat_id, data["notes"][title], reply_to=message.message_id)

    print("✅ Notes handlers registered.")
