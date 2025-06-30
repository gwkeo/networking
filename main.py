import telebot
import json

config_file = open('config.json', 'r')
config = json.loads(config_file.read())

config_file.close()

bot = telebot.TeleBot(token=config['api_token'])

@bot.message_handler()
def handle_text_messages(message):
    bot.send_message(chat_id=message.chat.id, text=message.text)

bot.infinity_polling()