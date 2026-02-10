import requests
import time
from telebot.types import Message


def imagine(bot, message: Message):
    prompt = message.text.replace("/imagine", "", 1).strip()
    if not prompt:
        bot.reply_to(message, "Hit me with a prompt, and I shall paint it! 🎨")
        return

    bot.send_chat_action(message.chat.id, 'upload_photo')

    payload = {
        "prompt": prompt,
        "params": {
            "n": 1,
            "width": 512,
            "height": 512,
            "steps": 20,
            "sampler_name": "k_euler",
            "cfg_scale": 7,
            "seed": "0",
            "karras": True
        },
        "nsfw": True,
        "censor_nsfw": False
    }

    headers = {
        "apikey": "0000000000"  # anonymous access
    }

    try:
        res = requests.post("https://stablehorde.net/api/v2/generate/async", json=payload, headers=headers)
        if res.status_code != 202:
            bot.reply_to(message, f"I said no 🙇🏻\nStatus: {res.status_code}\n{res.text}")
            return

        gen_id = res.json().get("id")
        status_msg = bot.reply_to(message, f"🛠️ Working on it... (ID: `{gen_id}`)", parse_mode="Markdown")

        while True:
            time.sleep(5)
            status = requests.get(f"https://stablehorde.net/api/v2/generate/status/{gen_id}").json()
            if status.get("done"):
                images = status.get("generations", [])
                if images:
                    image_url = images[0]["img"]
                    bot.send_photo(message.chat.id, image_url, caption=f"🌀 Dummy Here is You Image you begged for it - *{prompt}*", parse_mode="Markdown")
                    # Delete the status message
                    try:
                        bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
                    except:
                        pass
                else:
                    bot.reply_to(message, "I am not in the mood 😞")
                break

    except Exception as e:
        bot.reply_to(message, f"My skills choked 😩\n{e}")
