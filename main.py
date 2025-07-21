from typing import Dict
import telebot
from telebot import types
import json
import bin.texts as texts, bin.markups as markups
import bin.session as session
from bin import models
from enum import Enum
from bin.service import AppService
import math


config_file = open('config.json', 'r')
config = json.loads(config_file.read())
config_file.close()


class State(Enum):
    default = ""
    change_tables_count = "CHANGETABLESCOUNT"
    change_seats_count = "CHANGESEATSCOUNT"
    change_round_time = "CHANGEROUNDTIME"

class UserState(Enum):
    default = ""
    waiting_for_name = "WAITINGFORNAME"


class AppContext:
    def __init__(self, config):
        self.users = []                # Список ID активных пользователей
        self.usernames = dict()        # {user_id: UserInfo}
        self.admin_chat_id = config['telegram']['admin_chat_id']
        self.session_started = False   # Флаг активной сессии
        self.settings = models.Settings(5, 4, 10)
        self.states = dict()           # {user_id: State} для всех пользователей включая админа
        self.scheduler = session.SessionScheduler(self.users, 1, 1)
        self.app_service = AppService()
        self.ready_state = {           # Структура для управления готовностью
            'users': set(),            # Множество готовых пользователей
            'counter_msg_id': None     # ID сообщения-счетчика
        }


bot = telebot.TeleBot(token=config['telegram']['api_token'])
bot.context = AppContext(config)


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    ctx : AppContext = bot.context
    if message.chat.id == ctx.admin_chat_id:
        bot.send_message(
            chat_id=ctx.admin_chat_id, 
            text=texts.welcome_admin(message.chat.first_name), 
            reply_markup=markups.admin_main)
        return
    bot.send_message(
        chat_id=message.chat.id, 
        text=texts.start, 
        reply_markup=markups.register_markup)

@bot.message_handler(func=lambda m: m.chat.id == bot.context.admin_chat_id and m.text in markups.AdminButtons.to_array())
def handle_admin_buttons(message: types.Message):
    ctx : AppContext = bot.context
    
    count = len(ctx.users)
    tables, seats = session.get_ideal_tables_and_seats(count) if count > 0 else (0, 0)
    rounds = math.ceil((count-1) / (seats-1)) if count > 1 and seats > 1 else 1

    match(message.text):
        case markups.AdminButtons.show_settings.value:
            bot.send_message(
                chat_id=message.chat.id, 
                text=texts.current_settings(settings=ctx.settings),
                reply_markup=markups.admin_main)
        case markups.AdminButtons.change_settings.value:
            bot.send_message(
                chat_id=message.chat.id,
                text=texts.change_tables_count,
                reply_markup=None
            )
            bot.send_message(
                chat_id=message.chat.id,
                text=texts.show_ideal_tables_and_seats(tables, seats, rounds),
                reply_markup=None
            )
            ctx.state = State.change_tables_count.value
        case markups.AdminButtons.start_session.value:
            ctx.session_started = False  # сбрасываем флаг перед первым раундом
            ctx.scheduler = session.SessionScheduler(
                participants=ctx.users,
                n=ctx.settings.tables_count,
                m=ctx.settings.seats_count
            )
            round_dict = ctx.scheduler.generate_next_round()
            if round_dict is None:
                bot.send_message(message.chat.id, texts.unable_to_start_session, reply_markup=markups.admin_main)
                return
            if not hasattr(ctx, 'user_table_msgs'):
                ctx.user_table_msgs = {}
            round_num = len(ctx.scheduler.rounds) + 1

            for participant, table in round_dict.items():
                ctx.usernames[str(participant)].table = table + 1
                # Если уже есть сообщение — редактируем, иначе отправляем и сохраняем id
                pid = str(participant)
                if pid in ctx.user_table_msgs:
                    try:
                        bot.edit_message_text(
                            chat_id=int(participant),
                            message_id=ctx.user_table_msgs[pid],
                            text=texts.show_users_current_table_num(table_num=table + 1, round_num=round_num),
                            reply_markup=markups.user_ready
                        )
                    except Exception:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text=texts.show_users_current_table_num(table_num=table, round_num=round_num),
                            reply_markup=markups.user_ready
                        )
                        ctx.user_table_msgs[pid] = msg.message_id
                else:
                    msg = bot.send_message(
                        chat_id=int(participant),
                        text=texts.show_users_current_table_num(table_num=table, round_num=round_num),
                        reply_markup=markups.user_ready
                    )
                    ctx.user_table_msgs[pid] = msg.message_id
            ctx.last_users = ctx.users.copy()
            ctx.ready_users = set()
            msg = bot.send_message(
                message.chat.id,
                texts.show_ready_users(
                    count=0, 
                    all_users=len(ctx.users)),
                reply_markup=None
            )
            ctx.ready_counter_msg_id = msg.message_id
            stats = ctx.scheduler.get_session_stats()
            # Отправляем метрики при начале сессии

            ctx.app_service.update_users(ctx.usernames)
            ctx.app_service.send_metrics(stats, ctx.settings)
        case markups.AdminButtons.next_round.value:
            round_dict = ctx.scheduler.generate_next_round()
            if round_dict is None:
                bot.send_message(message.chat.id, texts.unable_to_start_session, reply_markup=markups.admin_main)
                return
            if not hasattr(ctx, 'user_table_msgs'):
                ctx.user_table_msgs = {}
            round_num = len(ctx.scheduler.rounds) + 1
            for participant, table in round_dict.items():
                pid = str(participant)
                if pid in ctx.user_table_msgs:
                    try:
                        bot.edit_message_text(
                            chat_id=int(participant),
                            message_id=ctx.user_table_msgs[pid],
                            text=texts.show_users_current_table_num(table_num=table, round_num=round_num),
                            reply_markup=markups.user_ready
                        )
                    except Exception:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text=texts.show_users_current_table_num(table_num=table, round_num=round_num),
                            reply_markup=markups.user_ready
                        )
                        ctx.user_table_msgs[pid] = msg.message_id
                else:
                    msg = bot.send_message(
                        chat_id=int(participant),
                        text=texts.show_users_current_table_num(table_num=table, round_num=round_num),
                        reply_markup=markups.user_ready
                    )
                    ctx.user_table_msgs[pid] = msg.message_id
            ctx.ready_users = set()
            msg = bot.send_message(
                chat_id=message.chat.id,
                text=texts.show_ready_users(
                    count=0, 
                    all_users=len(ctx.users)),
                reply_markup=None
            )
            ctx.ready_counter_msg_id = msg.message_id
            bot.send_message(message.chat.id, ctx.scheduler.get_session_stats(), reply_markup=markups.admin_main)
            ctx.last_users = ctx.users.copy()
            ctx.app_service.update_users(ctx.usernames)

        case markups.AdminButtons.show_users.value:
            bot.send_message(
                message.chat.id,
                f"Количество участников: {count}",
                reply_markup=markups.admin_main
            )
        case markups.AdminButtons.ideal_parameters.value:
            bot.send_message(
                chat_id=message.chat.id,
                text=texts.show_ideal_tables_and_seats(tables, seats, rounds),
                reply_markup=markups.admin_main
            )
        case markups.AdminButtons.finish_session.value:
            ctx.session_started = False
            # Сохраняем id всех участников до очистки
            all_participants = ctx.users.copy()
            ctx.users.clear()
            ctx.last_users.clear()
            ctx.ready_users = set()
            ctx.user_table_msgs = {}
            ctx.scheduler = session.SessionScheduler([], 1, 1)
            
            # Очищаем дашборд - отправляем пустые данные на сервер
            ctx.app_service.clear_dashboard()
            
            bot.send_message(message.chat.id, texts.session_finished, reply_markup=markups.admin_main)
            # Оповещаем всех участников
            for user_id in all_participants:
                try:
                    bot.send_message(chat_id=int(user_id), text=texts.session_finished_thanks)
                except Exception:
                    pass

@bot.message_handler()
def handle_message(message: types.Message):
    ctx = bot.context
    user_id = str(message.chat.id)
    
    # Обработка этапа ввода имени и фамилии
    if user_id in ctx.states and ctx.states[user_id] == UserState.waiting_for_name.value:
        fio = message.text.strip()
        if len(fio.split()) < 2:
            bot.send_message(chat_id=message.chat.id, text=texts.enter_name_surname)
            return
        ctx.states[user_id] = UserState.default.value
        # Сохраняем ФИО в ctx.usernames через models.UserInfo, table=0
        ctx.usernames[user_id] = models.UserInfo(fio, 0)
        # Отправляем заявку в админчат с ФИО
        bot.send_message(
            chat_id=ctx.admin_chat_id,
            text=texts.admin_chat_new_request(fio),
            reply_markup=markups.request_actions(message.chat.id)
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=texts.registration_request_sent
        )
        return

    if message.chat.id == bot.context.admin_chat_id and message.text in markups.AdminButtons.to_array():
        return

    # Обработка состояний админа
    if user_id == str(ctx.admin_chat_id):
        match(ctx.states.get(user_id, State.default.value)):
            case State.change_tables_count.value:
                try:
                    ctx.settings.tables_count = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(chat_id=message.chat.id, text=texts.change_seats_count)
                ctx.states[user_id] = State.change_seats_count.value
            case State.change_seats_count.value:
                try:
                    ctx.settings.seats_count = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(chat_id=message.chat.id, text=texts.change_round_time)
                ctx.states[user_id] = State.change_round_time.value
            case State.change_round_time.value:
                try:
                    ctx.settings.round_time = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.current_settings(ctx.settings),
                    reply_markup=markups.admin_main
                )
                ctx.states[user_id] = State.default.value

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(callback: types.CallbackQuery):
    ctx : AppContext = bot.context
    data = callback.data.split(':')[0]
    user_id = str(callback.message.chat.id)
    
    # --- Admin UI buttons ---
    if callback.message.chat.id == ctx.admin_chat_id:
        match(data):
            case markups.CallbackTypes.admin_show_settings.value:
                bot.answer_callback_query(callback.id)
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=texts.current_settings(settings=ctx.settings),
                    reply_markup=markups.admin_main
                )
                return
            case markups.CallbackTypes.admin_change_settings.value:
                bot.answer_callback_query(callback.id)
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=texts.change_tables_count,
                    reply_markup=None
                )
                ctx.states[user_id] = State.change_tables_count.value
                return
            case markups.CallbackTypes.admin_start_session.value:
                bot.answer_callback_query(callback.id)
                msg = bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.show_ready_users(
                        count=0, 
                        all_users=len(ctx.users)),
                    reply_markup=None
                )
                ctx.ready_state['counter_msg_id'] = msg.message_id
                ctx.scheduler = session.SessionScheduler(
                    participants=ctx.users,
                    n=ctx.settings.tables_count,
                    m=ctx.settings.seats_count
                )
                round_dict = ctx.scheduler.generate_next_round()
                if round_dict is None:
                    bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.id,
                        text=texts.unable_to_start_session,
                        reply_markup=markups.admin_main
                    )
                    return
                for participant, table in round_dict.items():
                    if int(participant) > 100:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text=texts.show_users_current_table_num(table_num=table),
                            reply_markup=markups.user_ready
                        )
                        pid = str(participant)
                        if pid in ctx.usernames:
                            ctx.usernames[pid].message_id = msg.message_id
                stats = ctx.scheduler.get_session_stats()
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=stats,
                    reply_markup=markups.admin_main
                )
                return
            case markups.CallbackTypes.admin_next_round.value:
                bot.answer_callback_query(callback.id)
                round_dict = ctx.scheduler.generate_next_round()
                if round_dict is None:
                    bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.id,
                        text=texts.unable_to_start_session,
                        reply_markup=markups.admin_main
                    )
                    return
                for participant, table in round_dict.items():
                    if int(participant) > 100:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text=texts.show_users_current_table_num(table_num=table),
                            reply_markup=markups.user_ready
                        )
                        pid = str(participant)
                        if pid in ctx.usernames:
                            ctx.usernames[pid].message_id = msg.message_id
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=ctx.scheduler.get_session_stats(),
                    reply_markup=markups.admin_main
                )
                return
            case markups.CallbackTypes.admin_add_participant.value:
                bot.answer_callback_query(callback.id)
                ctx.users.append(str(ctx.bots_count))
                ctx.bots_count += 1
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=texts.user_added(ctx.users[-1]),
                    reply_markup=markups.admin_main
                )
                return
            case markups.CallbackTypes.admin_remove_participant.value:
                bot.answer_callback_query(callback.id)
                if ctx.users:
                    removed_user = ctx.users.pop()
                    ctx.scheduler.remove_participant(int(removed_user))
                    bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.id,
                        text=texts.user_removed(removed_user),
                        reply_markup=markups.admin_main
                    )
                else:
                    bot.edit_message_text(
                        chat_id=callback.message.chat.id,
                        message_id=callback.message.id,
                        text=texts.no_users_to_remove,
                        reply_markup=markups.admin_main
                    )
                return
            case markups.CallbackTypes.admin_show_participants.value:
                bot.answer_callback_query(callback.id)
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=f"Количество участников: {len(ctx.users)}",
                    reply_markup=markups.admin_main
                )
                return
            case markups.CallbackTypes.admin_round_start.value:
                bot.answer_callback_query(callback.id)
                # Сообщение админу
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=texts.round_started,
                    reply_markup=None
                )

                # Сообщение участникам
                for participant in ctx.users:
                    pid = str(participant)
                    if pid in ctx.usernames and ctx.usernames[pid].message_id:
                        try:
                            bot.edit_message_text(
                                chat_id=int(participant),
                                message_id=ctx.usernames[pid].message_id,
                                text=texts.round_started
                            )
                        except Exception:
                            msg = bot.send_message(
                                chat_id=int(participant),
                                text=texts.round_started
                            )
                            ctx.usernames[pid].message_id = msg.message_id
                    else:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text=texts.round_started
                        )
                        if pid in ctx.usernames:
                            ctx.usernames[pid].message_id = msg.message_id
                stats = ctx.scheduler.get_session_stats()
                ctx.session_started = True  # после первого раунда больше не показываем кнопку 'Старт'
                bot.send_message(callback.message.chat.id, stats, reply_markup=markups.admin_main)
                return
            case markups.CallbackTypes.admin_finish_session.value:
                bot.answer_callback_query(callback.id)
                # Сохраняем id всех участников до очистки
                all_participants = ctx.users.copy()
                ctx.users.clear()
                ctx.ready_state['users'].clear()
                ctx.usernames.clear()
                ctx.scheduler = session.SessionScheduler([], 1, 1)
                
                # Очищаем дашборд - отправляем пустые данные на сервер
                ctx.app_service.clear_dashboard()
                
                bot.send_message(
                    chat_id=callback.message.chat.id, 
                    text=texts.session_finished, 
                    reply_markup=markups.admin_main)
                # Оповещаем всех участников
                for user_id in all_participants:
                    try:
                        bot.send_message(chat_id=int(user_id), text=texts.session_finished_thanks)
                    except Exception:
                        pass
                return

    # --- Остальные действия ---
    match(data):
        case markups.CallbackTypes.register.value:
            # Новый этап: запрашиваем имя и фамилию
            ctx.states[user_id] = UserState.waiting_for_name.value
            bot.send_message(
                chat_id=callback.message.chat.id,
                text=texts.enter_name_surname
            )
        case markups.CallbackTypes.leave_session.value:
            if user_id in ctx.users:
                ctx.users.remove(user_id)
                ctx.usernames.pop(user_id)
            try:
                ctx.scheduler.remove_participant(int(user_id))
            except ValueError:
                pass
            # Удаляем сообщение с кнопкой
            deleted = False
            try:
                bot.delete_message(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id
                )
                deleted = True
            except Exception as e:
                print(f"[DEBUG] Не удалось удалить сообщение: {e}")
            # Отправляем новое сообщение, даже если не удалось удалить старое
            bot.send_message(
                chat_id=callback.message.chat.id,
                text='Вы вышли',
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

            # Авторассылка для новых участников во время сессии
            if ctx.session_started:
                bot.send_message(
                    chat_id=id,
                    text=texts.wait_for_next_round
                )
                bot.send_message(
                    chat_id=ctx.admin_chat_id,
                    text=texts.user_registered_during_session(ctx.usernames[id].fio)
                )
            else:
                bot.send_message(
                    chat_id=id,
                    text=texts.user_is_happy,
                    reply_markup=markups.leave_session
                )
                # Отправляем гифку после успешной регистрации
                with open('cat-hyppy.mp4', 'rb') as gif_file:
                    bot.send_animation(chat_id=id, animation=gif_file)
            
            return

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
            # Проверяем, все ли участники готовы
            pid = str(callback.message.chat.id)
            ctx.ready_state['users'].add(pid)
            ready_count = len(ctx.ready_state['users'])
            total_count = len(ctx.users)
            # Обновляем сообщение-счетчик
            if ctx.ready_state['counter_msg_id']:
                try:
                    bot.edit_message_text(
                        chat_id=ctx.admin_chat_id,
                        message_id=ctx.ready_state['counter_msg_id'],
                        text=texts.show_ready_users(ready_count, total_count)
                    )
                except Exception:
                    pass
            if set(ctx.users) == ctx.ready_state['users']:
                if not ctx.session_started:
                    bot.send_message(
                        chat_id=ctx.admin_chat_id,
                        text=texts.all_users_ready_start,
                        reply_markup=markups.start_session_inline
                    )
                else:
                    bot.send_message(
                        chat_id=ctx.admin_chat_id,
                        text=texts.all_users_ready_next
                    )

bot.infinity_polling()