# 👑 Sassy Telegram Bot
<div align="center">
  <img src="images/logo.jpeg" width="150" height="150" style="border-radius: 50%;">
</div>

🚀 A fun, engaging, and feature-packed **Telegram bot** that acts as a **group admin, AI assistant, and note manager**—all with a sassy attitude! 💅

---

## ✨ Features
### 🤖 **AI-Powered Chat**
- **Sassy, confident, and playful responses** powered by AI.  
- **Remembers past conversations** for a more natural flow.  
- **Smart Roasts & Motivations** generated dynamically by AI.  

### 🔧 **Advanced Group Moderation**
- **Auto-moderation** to prevent spam and excessive messages.  
- **Group-Specific Bad Words**: Admins can configure unique blocklists for their groups.
- **Mute & unmute users** for a set time instead of banning.  
- **Welcome new members** with a personalized message.  

### 📌 **Smart Note Management**
- **Save & retrieve notes** with `/save` and `/note` commands.  
- **Supports inline buttons** for links.  
- **Handles all message types** (text, photos, videos, audio, documents).  

### 📢 **Broadcast System**
- **Send messages to all groups** the bot is in.  
- **Owner-only commands** for full control.  

### 🖼️ **AI Image Generation**
- Use `/imagine <prompt>` to generate images from text using **Stable Horde**.
- No API key needed—uses anonymous access.
- **NSFW supported** (use responsibly).
- Deletes "working..." message after image is sent for a clean UX.
- Powered by distributed, open-source compute.

### 🎲 **Fun & Extra Commands**
- `/roast` - Get a spicy burn 🔥  
- `/motivate` - Get an uplifting quote 💪  
- `/fortune` - Ask for a random prediction 🔮  
- `/tea` - Get the latest gossip ☕  
- `/imagine` - Generate an image from your prompt 🎨  

### 🛡️ **Web Dashboard & Supervisor**
- **Admin Dashboard**: A secure web interface running on port 5000.
- **Supervisor Mode**: Auto-restarts the bot if it crashes.
- **Encrypted Memory Viewer**: View and edit chat history securely.
- **Memory Manipulation**: Create, Edit, and Delete AI memories directly from the dashboard.
- **Fernet Encryption**: All chat logs are AES-encrypted for privacy.

---

## 🛠 **Installation & Setup**
### **1️⃣ Get the Required API Keys**
- **Telegram Bot API Token**: Create a bot via [@BotFather](https://t.me/BotFather).
- **AI API Key**: Register for [OpenRouter API](https://openrouter.ai/) for AI responses.
- **Admin Password**: Choose a strong password for your dashboard.

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
ADMIN_PASSWORD=your_dashboard_password
MEMORY_ACCESS_PASSWORD=your_secondary_memory_password
MEMORY_ENCRYPTION_KEY=your_fernet_key_generated_by_script
```

### **4️⃣ Run the Bot**
```sh
# This script runs both the bot and the dashboard
bash run.sh
```

### 🖥️ **Accessing the Dashboard**
1. Open your browser and go to `http://localhost:5000`.
2. Login with your `ADMIN_PASSWORD`.
3. To view or edit encrypted chat data, unlock the Memory tab with `MEMORY_ACCESS_PASSWORD`.

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
| `/imagine` | Generate an AI image from text prompt 🎨 |

### 🔧 Admin Commands
| Command | Description |
|---------|------------|
| `/mute @user or reply <time>` | Mute a user for a set time (default 5m) |
| `/unmute @user or reply` | Unmute a user |
| `/ban @user or reply` | Ban a user |
| `/kick @user or reply` | Kick a user (they can rejoin) |
| `/pin` | Pin the replied message |
| `/purge <num>` | Delete last <num> messages |
| `/welcome <on/off>` | Toggle welcome messages |
| `/setwelcome <msg>` | Set custom welcome message |
| `/addbw <word>` | Add word to group's black list |
| `/rmbw <word>` | Remove word from group's black list |
| `/notes` | To list all notes 🗒️ |
| `/note <note name> ` | To get a note |
| `/save` | Save notes 📝 |
| `/delnote` | Delete a note |
| `/toggle_notes` | Enable/Disable notes in a group |


### 👑 Owner Commands
| Command  | Description |
|----------|------------|
| `/broadcast <message>` | Send a message to all groups. *--no-header* to not send the header. |
| `/dashboard` | Get the link to the Admin Dashboard (Server IP) |
| `/restart` | Restart the bot |
| `/logs` | Fetch the last 10 logs |
| `/register` | To manually register the group id |

### **📂 Project Structure**
- `bot/core/`: Essential bot logic (AI, Memory, Helper).
- `bot/modules/`: Feature plugins (Fun, Moderation, Notes, etc).
- `data/`: Static assets (AI prompt, default badwords, config).
- `state/`: Dynamic data (databases, group configs).

### **🚀 Customization**
- **AI Personality**: Edit `data/prompt.txt`.
- **Global Badwords**: Edit `data/badwords.txt`.
- **Bot Config**: Edit `bot/config.py`.
---

### **🎯 Contributing**
💖 Want to improve the bot? Fork the repo, submit pull requests, or report issues.

🔗 **GitHub**: [ZUZU-Bot](https://github.com/Badmaneers/ZUZU-Bot)

---

### **🤝 Credits**
💡 Built by **Badmaneers** with ❤️ and a lot of sass!
📜 Inspired by **Rose Telegram Bot** but with a unique twist!

---

### **📢 License**
This project is *open-source* under the *MIT License*. Feel free to modify and use it!
