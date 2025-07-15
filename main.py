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
round_num = 1
adminchatlastmessage = 0

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
    if message.chat.id != admin_chat_id: 
        return
    
    global state
    bot.send_message(chat_id=message.chat.id, text=texts.change_tables_count)
    state = State.change_tables_count.value


@bot.message_handler(commands=['startsession'])
def handle_start_session(message: types.Message):
    if message.chat.id != admin_chat_id: 
        return
    
    global round_num
    
    scheduler = session.SessionScheduler(
        participants=users, 
        n=settings.tables_count,
        m=settings.seats_count
        )
    
    round_dict = scheduler.generate_next_round()
    print(users)

    if round_dict is None:
        bot.send_message(chat_id=admin_chat_id, text=texts.unable_to_start_session)
        return

    for participant, table in round_dict.items():
        if int(participant) == 442047289:
            bot.send_message(
                chat_id=int(participant),
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )
    
    stats = scheduler.get_session_stats()
    print(stats)

    round_num += 1


@bot.message_handler(commands=['nextround'])
def handle_next_round(message: types.Message):
    if message.chat.id != admin_chat_id:
        return
    
    global round_num
    
    scheduler = session.SessionScheduler(
        participants=users, 
        n=settings.tables_count,
        m=settings.seats_count
        )
    
    round_dict = scheduler.generate_next_round()

    if round_dict is None:
        bot.send_message(chat_id=admin_chat_id, text=texts.unable_to_start_session)
        return

    for participant, table in round_dict.items():
        if participant == 442047289:
            bot.send_message(
                chat_id=participant, 
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )

    round_num += 1

    bot.send_message(
        chat_id=admin_chat_id,
        text=scheduler.get_session_stats()
    )

@bot.message_handler(commands=['addparticipant'])
def handle_add_participant(message: types.Message):
    if message.chat.id != admin_chat_id:
        return
    
    users.append(str(int(users[-1] )+ 1))
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Участник {users[-1]} добавлен"
    )

@bot.message_handler(commands=['showparticipants'])
def handle_show_participants(message: types.Message):
    if message.chat.id != admin_chat_id:
        return
    
    bot.send_message(chat_id=message.chat.id, text=f"Участники: {users}")


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

            bot.send_message(
                chat_id=admin_chat_id,
                text=texts.user_left_session_log(callback.message.chat.first_name)
            )

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
        case markups.CallbackTypes.user_ready.value:
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=callback.message.text,
                reply_markup=None
            )

            bot.send_message(
                chat_id=admin_chat_id,
                text='user ready'
            )


bot.infinity_polling()