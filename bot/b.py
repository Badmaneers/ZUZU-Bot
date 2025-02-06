import telebot

BOT_TOKEN = "7518347090:AAFUtResdhXudyuhcI-19B7bnSwGZ4z3D-g"
bot = telebot.TeleBot(BOT_TOKEN)

bot.remove_webhook()
print("Webhook removed successfully!")
