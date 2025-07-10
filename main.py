import telebot
from telebot import types
import json
import bin.texts as texts, bin.markups as markups
import bin.session as session
from bin import models
from enum import Enum


config_file = open('config.json', 'r')
config = json.loads(config_file.read())
config_file.close()


class State(Enum):
    default = ""
    change_tables_count = "CHANGETABLESCOUNT"
    change_seats_count = "CHANGESEATSCOUNT"


bot = telebot.TeleBot(token=config['api_token'])
users = list()
admin_chat_id = config['admin_chat_id']
session_started = False
settings = models.Settings(5,4)
state = State.default


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    if message.chat.id == admin_chat_id:
        bot.send_message(chat_id=admin_chat_id, text=texts.welcome_admin(message.chat.first_name))
        return
    bot.send_message(chat_id=message.chat.id, text=texts.start, reply_markup=markups.register_markup)


@bot.message_handler(commands=['showsettings'])
def handle_show_settings(message: types.Message):
    if message.chat.id != admin_chat_id: 
        return
    bot.send_message(chat_id=message.chat.id, text=texts.current_settings(settings=settings))


@bot.message_handler(commands=['changesettings'])
def handle_change_settings(message: types.Message):
    global state
    if message.chat.id != admin_chat_id: 
        return
    bot.send_message(chat_id=message.chat.id, text=texts.change_tables_count)
    state = State.change_tables_count.value


@bot.message_handler(commands=['startsession'])
def handle_start_session(message: types.Message):
    if message.chat.id != admin_chat_id: 
        return
    a = session.generate_greedy_full_coverage_schedule(users, settings.tables_count, settings.seats_count)
    bot.send_message(chat_id=message.chat.id, text=str(a))
    for i in a:
        for j in users:
            bot.send_message(chat_id=j, text=texts.current_table_of_user(table_num=i[j]), reply_markup=markups.leave_session)


@bot.message_handler()
def handle_message(message: types.Message):
    global state
    match(state):
        case State.change_tables_count.value:
            try:
                settings.tables_count = int(message.text)
            except TypeError:
                bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                return

            bot.send_message(chat_id=message.chat.id, text=texts.change_seats_count)
            state = State.change_seats_count.value

        case State.change_seats_count.value:
            try:
                settings.seats_count = int(message.text)
            except TypeError:
                bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                return
            
            bot.send_message(chat_id=message.chat.id, text=texts.current_settings(settings))
            state = State.default.value


@bot.callback_query_handler()
def handle_callback_query(callback: types.CallbackQuery):
    match(callback.data.split(':')[0]):
        case markups.CallbackTypes.register.value:
            if not session_started:
                bot.send_message(
                    chat_id=admin_chat_id, 
                    text=texts.admin_chat_new_request(callback.message.chat.first_name),
                    reply_markup=markups.request_actions(callback.message.chat.id)
                )

                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=texts.registration_request_sent
                )

            else:
                bot.edit_message_text(
                    chat_id=callback.message.chat.id, 
                    message_id=callback.message.id,
                    text=texts.session_already_started
                )

        case markups.CallbackTypes.leave_session.value:

            users.remove(str(callback.message.chat.id))

            bot.edit_message_text(
                chat_id=callback.message.chat.id, 
                message_id=callback.message.id,
                text=texts.user_left_session, 
                reply_markup=markups.register_markup
            )

            bot.send_message(chat_id=admin_chat_id, text=f"Пользователь {callback.message.chat.first_name} покинул сессию")

        case markups.CallbackTypes.accept_new_user.value:
            bot.edit_message_text(
                    chat_id=callback.message.chat.id, 
                    message_id=callback.message.id,
                    text=texts.user_accepted_log(callback.message.text),
            )

            id = callback.data.split(':')[1]

            users.append(id)

            bot.send_message(
                chat_id=id,
                text=texts.user_is_happy,
                reply_markup=markups.leave_session
            )
        case markups.CallbackTypes.deny_new_user.value:
            bot.edit_message_text(
                    chat_id=callback.message.chat.id, 
                    message_id=callback.message.id,
                    text=texts.user_declined_log(callback.message.text),
            )

            id = callback.data.split(':')[1]

            bot.send_message(
                chat_id=id,
                text=texts.registration_denied,
            )


bot.infinity_polling()