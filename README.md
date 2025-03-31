# 👑 Sassy Telegram Bot
🚀 A fun, engaging, and feature-packed **Telegram bot** that acts as a **group admin, AI assistant, and note manager**—all with a sassy attitude! 💅

---

## ✨ Features
### 🤖 **AI-Powered Chat**
- **Sassy, confident, and playful responses** powered by AI.  
- **Remembers past conversations** for a more natural flow.  
- **Can roast, motivate, and chat like a human.**  

### 🔧 **Advanced Group Moderation**
- **Auto-moderation** to prevent spam, bad words, and excessive messages.  
- **Mute & unmute users** for a set time instead of banning.  
- **Welcome new members** with a personalized message.  

### 📌 **Smart Note Management**
- **Save & retrieve notes** with `/save` and `/note` commands.  
- **Supports inline buttons** for links.  
- **Handles all message types** (text, photos, videos, audio, documents).  

### 📢 **Broadcast System**
- **Send messages to all groups** the bot is in.  
- **Owner-only commands** for full control.  

### 🎲 **Fun & Extra Commands**
- `/roast` - Get a spicy burn 🔥  
- `/motivate` - Get an uplifting quote 💪  
- `/fortune` - Ask for a random prediction 🔮  
- `/tea` - Get the latest gossip ☕  

---

## 🛠 **Installation & Setup**
### **1️⃣ Get the Required API Keys**
- **Telegram Bot API Token**: Create a bot via [@BotFather](https://t.me/BotFather).
- **AI API Key**: Register for [OpenRouter API](https://openrouter.ai/) for AI responses.

### **2️⃣ Clone & Install Dependencies**
```sh
git clone https://github.com/Badmaneers/Mod-Queen-Bot.git
cd Mod-Queen-Bot
pip install -r requirements.txt
```

### **3️⃣ Create a .env File**
```sh
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_API_KEY=your_ai_api_key
OWNER_ID=your_telegram_user_id
```

### **4️⃣ Run the Bot**
```sh
bash run.sh
```

### 📌 General Commands
| Command  | Description |
|----------|------------|
| `/start` | Welcome message |
| `/help`  | Show available commands |
| `/fortune` | Get a random prediction |
| `/tea` | Spill some gossip in dm ☕ |

### 🔥 Fun Commands 
*Reply to a user to roast/motivate them.*
| Command  | Description |
|----------|------------|
| `/roast` | Get a savage roast 🔥 |
| `/motivate` | Get a motivational quote 💪 |

### 🔧 Admin Commands
| Command | Description |
|---------|------------|
| `/mute @user or reply <time>` | Mute a user for a set time |
| `/unmute @user or reply` | Unmute a user |
| `/ban @user or reply` | Ban a user |
| `/notes` | To list all notes 🗒️ |
| `/note <note name> ` | To get a note |
| `/save` | Save notes 📝 |
| `/delnote` | Delete a note |
| `/toggle_notes` | To enable/disable notes in a group |


### 📢 Owner Commands
| Command  | Description |
|----------|------------|
| `/broadcast <message>` | Send a message to all groups. *--no-header* to not send the header. |
| `/restart` | Restart the bot |
| `/logs` | Fetch the last 10 logs |
| `/register` | To manually register the group id |

### **🚀 Customization**
- Modify **prompt.txt** to change AI personality.
- Edit moderation settings in **moderations.py**.
- Configure note storage in **notes.py**.
---

### **🎯 Contributing **
💖 Want to improve the bot? Fork the repo, submit pull requests, or report issues.

🔗 **GitHub**: [Mod-Queen-Bot](https://github.com/Badmaneers/Mod-Queen-Bot)

---

### **🤝 Credits**
💡 Built by **Badmaneers** with ❤️ and a lot of sass!
📜 Inspired by **Rose Telegram Bot** but with a unique twist!

---

### **📢 License**
This project is *open-source* under the *MIT License*. Feel free to modify and use it!
