from json import load
from enum import Enum
from typing import Dict, List, Tuple

from bin import texts, models, markups, session, service

import telebot
from telebot import types

with open("config.json", "r") as config_file:
    config = load(config_file)

class AdminState(Enum):
    default = "DEFAULT"
    change_tables_count = "CHANGE_TABLES_COUNT"
    change_seats_count = "CHANGE_SEATS_COUNT"
    change_round_time = "CHANGE_ROUND_TIME"
    change_attempts_number = "CHANGE_ATTEMPTS_NUMBER"

class AppContext:
    def __init__(self, config: Dict):
        self.users = dict()
        self.admin_chat_id = config['telegram']['admin_chat_id']
        self.session = session.SessionScheduler(
            participants=[], 
            n=1, 
            m=1
        )
        self.admin_chat_state = AdminState.default.value
        self.session_started = False
        self.admin_chat_last_message_id = 0
        self.app_service = service.AppService(
            base_url=f"http://{config['server']['host']}:{config['server']['port']}/api"
        )
        self.settings = models.Settings(
            tables_count=1,
            seats_count=1,
            round_time=3,
            break_time=1
        )

    def get_user_info(self, user_id: int):
        """Получает информацию о пользователе из соответствующего словаря"""
        return self.users.get(user_id)

    def update_user_table(self, user_id: int, table_num: int):
        """Обновляет номер стола для пользователя"""
        if user_id in self.users:
            self.users[user_id].table_num = table_num

    def get_ready_users_count(self) -> Tuple[int, int]:
        """
        Возвращает количество готовых пользователей и общее количество
        :return: (количество готовых, общее количество)
        """
        ready_users = len([user for user in self.users.values() 
                          if user.user_state == models.UserState.ready.value])
        return (ready_users, len(self.users))

    def are_all_users_ready(self) -> bool:
        """Проверяет, готовы ли все пользователи к следующему раунду"""
        ready_count, total_count = self.get_ready_users_count()
        return ready_count == total_count

    def get_users(self):
        """Возвращает список всех пользователей"""
        return [user_info.to_dict() for _, user_info in self.users.items()]

    def start_new_round(self):
        """Подготовка к новому раунду"""
        for user in self.users.values():
            user.user_state = models.UserState.registered.value

           
def update_message(
        bot: telebot.TeleBot, 
        message: types.Message, 
        text: str, 
        keyboard: types.ReplyKeyboardMarkup = None) -> int:
    try:
        if message.content_type == 'text':
            msg = bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.id,
                text=text,
                reply_markup=keyboard
            )
            return msg.message_id
        else:
            bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.id)
            msg = bot.send_message(
                chat_id=message.chat.id,
                text=text,
                reply_markup=keyboard
            )
            return msg.message_id
    except:
        msg = bot.send_message(
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard
        )
        return msg.message_id
    

def update_message_by_chat_and_message_id(
        bot: telebot.TeleBot,
        message_id: int,
        chat_id: int,
        text: str,
        keyboard: types.ReplyKeyboardMarkup = None
) -> int:
        
    try:
        bot.delete_message(
            chat_id=chat_id,
            message_id=message_id)
        msg = bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard
        )
        return msg.message_id
    except:
        try:
            msg = bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard
            )
            return msg.message_id
        except Exception as e:
            print(f"[DEBUG] Не удалось отправить сообщение пользователю {chat_id}: {str(e)}")
            return message_id


bot = telebot.TeleBot(
        token=config['telegram']['api_token']
    )
bot.context = AppContext(config)

@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    ctx : AppContext = bot.context
    if message.chat.id == ctx.admin_chat_id:
        update_message(
            bot=bot,
            message=message,
            text=texts.welcome_admin(message.chat.first_name),
            keyboard=markups.admin_main
        )

        print(ctx.get_users())

        return

    update_message(
        bot=bot,
        message=message,
        text=texts.start,
        keyboard=markups.register_markup
    )


@bot.message_handler(func=lambda m: m.chat.id == bot.context.admin_chat_id and m.text in markups.AdminButtons.to_array())
def handle_admin_buttons(message: types.Message):
    ctx : AppContext = bot.context

    users_count = len(ctx.users)  # Убираем учет мок-пользователей
    tables_count, seats_count = session.get_ideal_tables_and_seats(users_count) 
    rounds = session.get_max_rounds(users_count=users_count, seats_count=seats_count)

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
                text=texts.show_ideal_tables_and_seats(tables_count, seats_count, rounds),
                reply_markup=None
            )
            ctx.admin_chat_state = AdminState.change_tables_count.value

        case markups.AdminButtons.start_session.value:
            ctx.session_started = False

            ctx.session = session.SessionScheduler(
                participants=list(ctx.users.keys()),  # Только реальные пользователи
                n=ctx.settings.tables_count,
                m=ctx.settings.seats_count
            )

            round_dict = ctx.session.generate_next_round()
            
            if round_dict is None:
                bot.send_message(message.chat.id, texts.unable_to_start_session, reply_markup=markups.admin_main)
                return
            
            for participant_id, table_num in round_dict.items():
                user_info = ctx.users[participant_id]
                user_info.table_num = table_num + 1
                message_id = update_message_by_chat_and_message_id(
                    bot=bot,
                    message_id=user_info.message_id,
                    chat_id=participant_id,
                    text=texts.show_users_current_table_num(round_num=1, table_num=table_num),
                    keyboard=markups.user_ready
                )
                user_info.message_id = message_id

            ready_count, total_count = ctx.get_ready_users_count()
            ctx.admin_chat_last_message_id = update_message(
                bot=bot,
                message=message,
                text=texts.show_ready_users(
                    count=ready_count,
                    all_users=total_count
                )
            )

            try:
                # Обновляем информацию на сервере
                all_users = {**ctx.users}
                ctx.app_service.update_users(users=all_users)
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

            try:
                ctx.app_service.send_metrics(ctx.session.get_session_stats(), round_time=ctx.settings.round_time, break_time=ctx.settings.break_time)
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_metrics(str(e))}")


        case markups.AdminButtons.next_round.value:

            try:
                ctx.app_service.stop_session()
            except Exception as e:
                print(f'[DEBUG] Error while stoping session timer: {str(e)}')

            if len(ctx.session.participants) != len(ctx.users):
                ctx.session.add_participants(ctx.new_participants)
 
            round_dict = ctx.session.generate_next_round()

            if round_dict is None:
                bot.send_message(
                    chat_id=message.chat.id, 
                    text=texts.unable_to_start_next_round, 
                    reply_markup=markups.admin_main)
                return
            
            round_num = len(ctx.session.rounds)

            for participant_id, table_num in round_dict.items():
                ctx.update_user_table(participant_id, table_num + 1)
                
                if not ctx.is_mock_user(participant_id):
                    print(ctx.users)
                    user_info = ctx.get_user_info(participant_id)
                    message_id = update_message_by_chat_and_message_id(
                        bot=bot,
                        message_id=user_info.message_id,
                        chat_id=participant_id,
                        text=texts.show_users_current_table_num(round_num=round_num, table_num=table_num),
                        keyboard=markups.user_ready
                    )
                    user_info.message_id = message_id

            # ctx.ready_users = set(ctx.mock_users.keys())  # Мок-пользователи всегда готовы
            ctx.admin_chat_last_message_id = update_message(
                bot=bot,
                message=message,
                text=texts.show_ready_users(
                    count=len(ctx.users),
                    all_users=len(ctx.session.participants)
                )
            )

            try:
                all_users = {**ctx.users}
                ctx.app_service.update_users(users=all_users)
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

            try:
                ctx.app_service.send_metrics(ctx.session.get_session_stats(), round_time=ctx.settings.round_time, break_time=ctx.settings.break_time)
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_metrics(str(e))}")

        case markups.AdminButtons.show_users.value:
            update_message_by_chat_and_message_id(
                bot=bot,
                message_id=ctx.admin_chat_last_message_id,
                chat_id=ctx.admin_chat_id,
                text=texts.show_users_count(users_count=users_count),
                keyboard=markups.admin_main
            )
        case markups.AdminButtons.ideal_parameters.value:
            update_message_by_chat_and_message_id(
                bot=bot,
                message_id=ctx.admin_chat_last_message_id,
                chat_id=ctx.admin_chat_id,
                text=texts.show_ideal_tables_and_seats(tables=tables_count, seats=seats_count, rounds=rounds),
                keyboard=markups.admin_main
            )
        case markups.AdminButtons.finish_session.value:
            ctx.session_started = False
            for user_id, user_info in ctx.users.items():
                try:
                    update_message_by_chat_and_message_id(
                        bot=bot,
                        message_id=user_info.message_id,
                        chat_id=user_id,
                        text=texts.session_finished_thanks
                    )
                except Exception as e:
                    print(f'[DEBUG] Не удалось отправить сообщение пользователю {user_info.username}: {str(e)}')
            
            ctx.users.clear()
            ctx.session = session.SessionScheduler([], 1, 1)

            try:
                ctx.app_service.clear_dashboard()
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

            update_message(
                bot=bot,
                message=message,
                text=texts.session_finished,
                keyboard=markups.admin_main
            )

@bot.message_handler()
def handle_message(message: types.Message):
    ctx : AppContext = bot.context
    user_id = int(message.chat.id)
    
    # Обработка этапа ввода имени и фамилии
    if user_id in ctx.users and ctx.users[user_id].user_state == models.UserState.waiting_for_name.value:
        fio = message.text.strip()
        if len(fio.split()) < 2:
            bot.send_message(chat_id=message.chat.id, text=texts.enter_name_surname)
            return
        ctx.users[user_id].user_state = models.UserState.registered.value
        bot.send_message(
            chat_id=ctx.admin_chat_id,
            text=texts.admin_chat_new_request(fio),
            reply_markup=markups.request_actions(message.chat.id)
        )
        message_id = update_message(
            bot=bot,
            message=message,
            text=texts.registration_request_sent
        )
        ctx.users[user_id] = models.UserInfo(
            username=fio, 
            table_num=0,
            message_id=message_id,
            user_state=models.UserState.registered.value)
        return

    if message.chat.id == ctx.admin_chat_id and message.text in markups.AdminButtons.to_array():
        return

    # Обработка состояний админа
    if user_id == ctx.admin_chat_id:
        match(ctx.admin_chat_state):
            case AdminState.change_tables_count.value:
                try:
                    ctx.settings.tables_count = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(chat_id=message.chat.id, text=texts.change_seats_count)
                ctx.admin_chat_state = AdminState.change_seats_count.value
            case AdminState.change_seats_count.value:
                try:
                    ctx.settings.seats_count = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(chat_id=message.chat.id, text=texts.change_round_time)
                ctx.admin_chat_state = AdminState.change_round_time.value
            case AdminState.change_round_time.value:
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
                ctx.admin_chat_state = AdminState.default.value

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(callback: types.CallbackQuery):
    ctx : AppContext = bot.context
    data = callback.data.split(':')[0]
    user_id = int(callback.message.chat.id)
    
    # --- Admin UI buttons ---
    if user_id == ctx.admin_chat_id:
        match(data):
            case markups.CallbackTypes.admin_round_start.value:
                message_id = update_message(
                    bot=bot,
                    message=callback.message,
                    text=texts.round_started
                )
                ctx.admin_chat_last_message_id = message_id

                # Сообщение участникам
                for participant_id, user_info in ctx.users.items():
                    message_id = update_message_by_chat_and_message_id(
                        bot=bot,
                        message_id=ctx.users[participant_id].message_id,
                        chat_id=participant_id,
                        text=texts.round_started
                    )
                    ctx.users[participant_id].message_id = message_id

                ctx.session_started = True  # после первого раунда больше не показываем кнопку 'Старт'

                try:
                    ctx.app_service.start_session()
                except Exception as e:
                    print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")
                return

    # --- Остальные действия ---
    match(data):
        case markups.CallbackTypes.register.value:
            # Новый этап: запрашиваем имя и фамилию

            message_id = update_message(
                bot=bot,
                message=callback.message,
                text=texts.enter_name_surname
            )
            ctx.users[user_id] = models.UserInfo(
                user_state=models.UserState.waiting_for_name.value,
                message_id=message_id)

        case markups.CallbackTypes.leave_session.value:
            bot.send_message(
                chat_id=ctx.admin_chat_id,
                text=texts.user_left_session_log(ctx.users[user_id].username)
            )

            if user_id in ctx.users:
                ctx.users.pop(user_id)

            if user_id in ctx.session.participants:
                ctx.session.remove_participant(user_id)
            
            message_id = update_message(
                bot=bot,
                message=callback.message,
                text=texts.you_left
            )

        case markups.CallbackTypes.accept_new_user.value:

            update_message(
                bot=bot,
                message=callback.message,
                text=texts.user_accepted_log(callback.message.text)
            )
            
            user_id = int(callback.data.split(':')[1])

            # Авторассылка для новых участников во время сессии
            if ctx.session_started:

                message_id = update_message_by_chat_and_message_id(
                    bot=bot,
                    chat_id=user_id,
                    message_id=ctx.users[user_id].message_id,
                    text=texts.wait_for_next_round
                )

                ctx.users[user_id].user_state = models.UserState.registered.value
                ctx.users[user_id].message_id = message_id

                bot.send_message(
                    chat_id=ctx.admin_chat_id,
                    text=texts.user_registered_during_session(ctx.users[user_id].username)
                )

            else:
                message_id = update_message_by_chat_and_message_id(
                    bot=bot,
                    text=texts.user_is_happy,
                    keyboard=markups.leave_session,
                    chat_id=user_id,
                    message_id=ctx.users[user_id].message_id
                )
                ctx.users[user_id].message_id = message_id

            return

        case markups.CallbackTypes.deny_new_user.value:
            update_message(
                bot=bot,
                message=callback.message,
                text=texts.user_declined_log(callback.message.text)
            )

            user_id = int(callback.data.split(':')[1])

            message_id = update_message_by_chat_and_message_id(
                bot=bot,
                chat_id=user_id,
                message_id=ctx.users[user_id].message_id,
                text=texts.registration_denied
            )

            ctx.users.pop(user_id)

        case markups.CallbackTypes.user_ready.value:

            update_message(
                bot=bot,
                message=callback.message,
                text=callback.message.text
            )

            ctx.users[callback.message.chat.id].user_state = models.UserState.ready.value
            
            ready_count, total_count = ctx.get_ready_users_count()

            message_id = update_message_by_chat_and_message_id(
                bot=bot,
                chat_id=ctx.admin_chat_id,
                message_id=ctx.admin_chat_last_message_id,
                text=texts.show_ready_users(ready_count, total_count)
            )
            ctx.admin_chat_last_message_id = message_id

            if ctx.are_all_users_ready():
                if not ctx.session_started:
                    message_id = update_message_by_chat_and_message_id(
                        bot=bot,
                        chat_id=ctx.admin_chat_id,
                        message_id=ctx.admin_chat_last_message_id,
                        text=texts.all_users_ready_start,
                        keyboard=markups.start_session_inline
                    )
                    ctx.admin_chat_last_message_id = message_id
                else:
                    message_id = update_message_by_chat_and_message_id(
                        bot=bot,
                        chat_id=ctx.admin_chat_id,
                        message_id=ctx.admin_chat_last_message_id,
                        text=texts.all_users_ready_next
                    )

                    try:
                        ctx.app_service.start_session()
                    except Exception as e:
                        print(f'[DEBUG]: error: {str(e)}')

bot.infinity_polling()