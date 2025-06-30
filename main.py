import telebot
import json
import texts, markups


config_file = open('config.json', 'r')
config = json.loads(config_file.read())
config_file.close()


bot = telebot.TeleBot(token=config['api_token'])
users = []
session_started = False


@bot.message_handler(commands=['start'])
def handle_start(message):
    print(markups.register_markup)
    bot.send_message(chat_id=message.chat.id, text=texts.start, reply_markup=markups.register_markup)


@bot.callback_query_handler()
def handle_callback_query(callback):
    match(callback.data):
        case markups.CallbackTypes.register.value:
            if not session_started:
                bot.edit_message_text(
                    chat_id=callback.message.chat.id, 
                    message_id=callback.message.id,
                    text=texts.current_settings(len(users)),
                    reply_markup=markups.active_session_markup
                )

            else:
                bot.edit_message_text(
                    chat_id=callback.message.chat.id, 
                    message_id=callback.message.id,
                    text=texts.sessiong_already_started
                )

        case markups.CallbackTypes.leave_session.value:
            bot.edit_message_text(
                chat_id=callback.message.chat.id, 
                message_id=callback.message.id,
                text=texts.user_left_session, 
                reply_markup=markups.register_markup
            )


bot.infinity_polling()