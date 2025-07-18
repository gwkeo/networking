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


class AppContext:
    def __init__(self, config):
        self.users = []
        self.last_users = []
        self.admin_chat_id = config['admin_chat_id']
        self.session_started = False
        self.settings = models.Settings(5, 4)
        self.state = State.default
        self.scheduler = session.SessionScheduler(self.users, 1, 1)


bot = telebot.TeleBot(token=config['api_token'])
bot.context = AppContext(config)


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    ctx = bot.context
    if message.chat.id == ctx.admin_chat_id:
        bot.send_message(chat_id=ctx.admin_chat_id, text=texts.welcome_admin(message.chat.first_name))
        return
    bot.send_message(chat_id=message.chat.id, text=texts.start, reply_markup=markups.register_markup)


@bot.message_handler(commands=['showsettings'])
def handle_show_settings(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    bot.send_message(chat_id=message.chat.id, text=texts.current_settings(settings=ctx.settings))


@bot.message_handler(commands=['changesettings'])
def handle_change_settings(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    bot.send_message(chat_id=message.chat.id, text=texts.change_tables_count)
    ctx.state = State.change_tables_count.value


@bot.message_handler(commands=['startsession'])
def handle_start_session(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    ctx.scheduler = session.SessionScheduler(
        participants=ctx.users,
        n=ctx.settings.tables_count,
        m=ctx.settings.seats_count
    )
    round_dict = ctx.scheduler.generate_next_round()
    if round_dict is None:
        bot.send_message(chat_id=ctx.admin_chat_id, text=texts.unable_to_start_session)
        return
    for participant, table in round_dict.items():
        if int(participant) == 442047289:
            bot.send_message(
                chat_id=int(participant),
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )
        print(participant, table)
    stats = ctx.scheduler.get_session_stats()
    print(stats)
    print(ctx.scheduler.get_all_pairs())
    ctx.last_users = ctx.users.copy()


@bot.message_handler(commands=['nextround'])
def handle_next_round(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    round_dict = ctx.scheduler.generate_next_round()
    if round_dict is None:
        bot.send_message(chat_id=ctx.admin_chat_id, text=texts.unable_to_start_session)
        return
    for participant, table in round_dict.items():
        if int(participant) == 442047289:
            bot.send_message(
                chat_id=int(participant),
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )
        print(participant, table)
    bot.send_message(
        chat_id=ctx.admin_chat_id,
        text=ctx.scheduler.get_session_stats()
    )
    ctx.last_users = ctx.users.copy()


@bot.message_handler(commands=['addparticipant'])
def handle_add_participant(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    if ctx.users:
        ctx.users.append(str(int(ctx.users[-1]) + 1))
    else:
        ctx.users.append('1')
    print(ctx.users)
    ctx.scheduler.add_participant(int(ctx.users[-1]))
    bot.send_message(
        chat_id=message.chat.id,
        text=f"Участник {ctx.users[-1]} добавлен"
    )

@bot.message_handler(commands=['removeparticipant'])
def handle_remove_participant(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    if ctx.users:
        removed_user = ctx.users.pop()
        ctx.scheduler.remove_participant(int(removed_user))
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Участник {removed_user} удален"
        )

@bot.message_handler(commands=['showparticipants'])
def handle_show_participants(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    bot.send_message(chat_id=message.chat.id, text=f"Количество участников: {len(ctx.users)}")

@bot.message_handler()
def handle_message(message: types.Message):
    ctx = bot.context
    match(ctx.state):
        case State.change_tables_count.value:
            try:
                ctx.settings.tables_count = int(message.text)
            except (TypeError, ValueError):
                bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                return
            bot.send_message(chat_id=message.chat.id, text=texts.change_seats_count)
            ctx.state = State.change_seats_count.value
        case State.change_seats_count.value:
            try:
                ctx.settings.seats_count = int(message.text)
            except (TypeError, ValueError):
                bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                return
            bot.send_message(chat_id=message.chat.id, text=texts.current_settings(ctx.settings))
            ctx.state = State.default.value

@bot.callback_query_handler()
def handle_callback_query(callback: types.CallbackQuery):
    ctx = bot.context
    match(callback.data.split(':')[0]):
        case markups.CallbackTypes.register.value:
            if not ctx.session_started:
                bot.send_message(
                    chat_id=ctx.admin_chat_id,
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
            ctx.users.remove(str(callback.message.chat.id))
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=texts.user_left_session,
                reply_markup=markups.register_markup
            )
            bot.send_message(
                chat_id=ctx.admin_chat_id,
                text=texts.user_left_session_log(callback.message.chat.first_name)
            )
        case markups.CallbackTypes.accept_new_user.value:
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=texts.user_accepted_log(callback.message.text),
            )
            id = callback.data.split(':')[1]
            ctx.users.append(id)
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
                chat_id=ctx.admin_chat_id,
                text='user ready'
            )

bot.infinity_polling()