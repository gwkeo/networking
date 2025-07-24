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
    add_mock_users = "ADD_MOCK_USERS"

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
        total_users = len([user for user in self.users.values() 
            if user.user_state == models.UserState.registered.value or user.user_state == models.UserState.ready.value])
        return (ready_users, total_users)

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

    def remove_buttons_for_unready_users(self):
        """Убирает кнопки у пользователей, которые не отметились готовыми"""
        unready_users = [user_id for user_id, user_info in self.users.items() 
            if user_info.user_state == models.UserState.registered.value and not user_info.is_mock]
        return unready_users

    def start_round(self, bot: telebot.TeleBot):
        """Запускает раунд и обновляет сообщения пользователям"""
        ready_users = [user_id for user_id, user_info in self.users.items() 
            if user_info.user_state == models.UserState.ready.value]
        ready_users_info = [self.users[user_id] for user_id in ready_users]

        try:
            self.app_service.update_users(users=ready_users_info)
        except Exception as e:
            print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

        # Обновляем сообщение админу
        message_id = update_message_by_chat_and_message_id(
            bot=bot,
            chat_id=self.admin_chat_id,
            message_id=self.admin_chat_last_message_id,
            text=texts.round_started
        )
        self.admin_chat_last_message_id = message_id

        # Сообщение готовым участникам
        for participant_id in ready_users:
            if not self.users[participant_id].is_mock:
                message_id = update_message_by_chat_and_message_id(
                    bot=bot,
                    message_id=self.users[participant_id].message_id,
                    chat_id=participant_id,
                    text=texts.round_started
                )
                self.users[participant_id].message_id = message_id

        # Убираем кнопки у неготовых участников
        unready_users = self.remove_buttons_for_unready_users()
        for participant_id in unready_users:
            message_id = update_message_by_chat_and_message_id(
                bot=bot,
                message_id=self.users[participant_id].message_id,
                chat_id=participant_id,
                text=texts.round_started_without_you
            )
            self.users[participant_id].message_id = message_id

        # Обновляем метрики перед запуском таймера
        try:
            session_stats = self.session.get_session_stats()
            round_num = session_stats['total_rounds']
            
            # Формируем информацию о текущих столах
            current_tables = {}
            for user_id, user_info in self.users.items():
                if user_info.table_num > 0:  # Пропускаем пользователей без стола
                    table_idx = user_info.table_num - 1  # Преобразуем в 0-based индекс
                    if table_idx not in current_tables:
                        current_tables[table_idx] = []
                    current_tables[table_idx].append(user_id)

            print(f"[DEBUG] Отправка метрик в start_round:")
            print(f"[DEBUG] session_stats: {session_stats}")
            print(f"[DEBUG] current_tables: {current_tables}")
            print(f"[DEBUG] round_num: {round_num}")

            metrics_data = {
                **session_stats,
                'current_round_tables': current_tables
            }

            self.app_service.send_metrics(
                stats=metrics_data,
                round_time=self.settings.round_time,
                break_time=self.settings.break_time,
                round_num=round_num
            )
        except Exception as e:
            print(f"[DEBUG] {texts.unable_to_update_metrics(str(e))}")

        # Запускаем таймер
        try:
            self.app_service.start_session()
        except Exception as e:
            print(f"[DEBUG] Error while starting session timer: {str(e)}")

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
        # Проверяем, не является ли пользователь моковым
        ctx : AppContext = bot.context
        if chat_id in ctx.users and ctx.users[chat_id].is_mock:
            return message_id  # Для моковых пользователей просто возвращаем старый message_id
            
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


bot : telebot.TeleBot = telebot.TeleBot(
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

    users_count = len(ctx.users)
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

        case markups.AdminButtons.add_mock_users.value:
            bot.send_message(
                chat_id=message.chat.id,
                text="Введите количество мок-пользователей для добавления:",
                reply_markup=None
            )
            ctx.admin_chat_state = AdminState.add_mock_users.value

        case markups.AdminButtons.start_session.value:
            potentially_ready_users = [user_id for user_id, user_info in ctx.users.items() 
                if user_info.user_state == models.UserState.registered.value or user_info.user_state == models.UserState.ready.value]

            try:
                ctx.app_service.stop_session()
            except Exception as e:
                print(f'[DEBUG] Error while stoping session timer: {str(e)}')

            ctx.session_started = False
            ctx.session = session.SessionScheduler(
                participants=potentially_ready_users,
                n=ctx.settings.tables_count,
                m=ctx.settings.seats_count
            )

            round_dict = ctx.session.generate_next_round()
            
            if round_dict is None:
                bot.send_message(
                    chat_id=message.chat.id,
                    text=texts.unable_to_start_session,
                    reply_markup=markups.admin_main)
                return
            
            for participant_id, table_num in round_dict.items():
                user_info = ctx.users[participant_id]
                user_info.table_num = table_num + 1
                
                # Отправляем сообщение только реальным пользователям
                if not user_info.is_mock:
                    message = bot.send_message(
                        chat_id=participant_id,
                        text=texts.show_users_current_table_num(
                            round_num=1,
                            table_num=table_num),
                        reply_markup=markups.user_ready
                    )
                    user_info.message_id = message.message_id
                
                # Моковые пользователи автоматически становятся готовыми
                if user_info.is_mock:
                    user_info.user_state = models.UserState.ready.value

            ready_count, total_count = ctx.get_ready_users_count()
            ctx.admin_chat_last_message_id = bot.send_message(
                chat_id=ctx.admin_chat_id,
                text=texts.show_ready_users(
                    count=ready_count,
                    all_users=total_count
                ),
                reply_markup=markups.start_session_before_everyone_ready
            )

            potentially_ready_users_info = [ctx.users[user_id] for user_id in potentially_ready_users]

            try:
                ctx.app_service.update_users(users=potentially_ready_users_info)
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

            try:
                ctx.app_service.send_metrics(
                    stats={
                        **ctx.session.get_session_stats(),
                        'current_round_tables': {
                            user_id: table_num - 1  # Преобразуем номера столов в 0-based индексы
                            for user_id, user_info in ctx.users.items()
                            if user_info.table_num > 0  # Пропускаем пользователей без стола
                        }
                    },
                    round_time=ctx.settings.round_time,
                    break_time=ctx.settings.break_time
                )
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_metrics(str(e))}")

        case markups.AdminButtons.next_round.value:
            # Останавливаем таймер перед началом нового раунда
            try:
                ctx.app_service.stop_session()
            except Exception as e:
                print(f'[DEBUG] Error while stopping session timer: {str(e)}')

            # Добавляем в сессию всех готовых пользователей
            ready_users = [user_id for user_id, user_info in ctx.users.items() 
                if user_info.user_state == models.UserState.ready.value]
            
            for user_id in ready_users:
                if not ctx.users[user_id].is_mock:  # Только для реальных пользователей меняем состояние
                    ctx.session.add_participant(user_id)
                    ctx.users[user_id].user_state = models.UserState.registered.value

            # Генерируем новый раунд
            round_dict = ctx.session.generate_next_round()

            if round_dict is None:
                bot.send_message(
                    chat_id=message.chat.id, 
                    text=texts.unable_to_start_next_round, 
                    reply_markup=markups.admin_main)
                return
            
            round_num = len(ctx.session.rounds)

            # Обновляем состояния пользователей и отправляем сообщения
            for participant_id, table_num in round_dict.items():
                user_info = ctx.users[participant_id]
                ctx.update_user_table(participant_id, table_num + 1)
                
                if not user_info.is_mock:
                    message = bot.send_message(
                        chat_id=participant_id,
                        text=texts.show_users_current_table_num(
                            round_num=round_num, 
                            table_num=table_num
                        ),
                        reply_markup=markups.user_ready
                    )
                    user_info.message_id = message.message_id

            ready_count, total_count = ctx.get_ready_users_count()
            ctx.admin_chat_last_message_id = bot.send_message(
                chat_id=ctx.admin_chat_id,
                text=texts.show_ready_users(
                    count=ready_count,
                    all_users=total_count
                ),
                reply_markup=markups.start_session_before_everyone_ready
            )

            try:
                ctx.app_service.update_users(users=[ctx.users[user_id] for user_id in round_dict.keys()])
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_users(str(e))}")

            # Обновляем метрики с актуальным номером раунда
            try:
                session_stats = ctx.session.get_session_stats()
                
                # Формируем информацию о текущих столах
                current_tables = {}
                for user_id, user_info in ctx.users.items():
                    if user_info.table_num > 0:  # Пропускаем пользователей без стола
                        table_idx = user_info.table_num - 1  # Преобразуем в 0-based индекс
                        if table_idx not in current_tables:
                            current_tables[table_idx] = []
                        current_tables[table_idx].append(user_id)

                print(f"[DEBUG] Отправка метрик в next_round:")
                print(f"[DEBUG] session_stats: {session_stats}")
                print(f"[DEBUG] current_tables: {current_tables}")
                print(f"[DEBUG] round_num: {round_num}")

                metrics_data = {
                    **session_stats,
                    'current_round_tables': current_tables
                }

                ctx.app_service.send_metrics(
                    stats=metrics_data,
                    round_time=ctx.settings.round_time,
                    break_time=ctx.settings.break_time,
                    round_num=round_num
                )
            except Exception as e:
                print(f"[DEBUG] {texts.unable_to_update_metrics(str(e))}")

        case markups.AdminButtons.show_users.value:
            ready_users = [user_id for user_id, user_info in ctx.users.items() if user_info.user_state == models.UserState.ready.value]
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
                if not user_info.is_mock:  # Отправляем сообщение только реальным пользователям
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
                if ctx.session_started:
                    ctx.session.n = ctx.settings.tables_count

            case AdminState.change_seats_count.value:
                try:
                    ctx.settings.seats_count = int(message.text)
                except (TypeError, ValueError):
                    bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                    return
                bot.send_message(chat_id=message.chat.id, text=texts.change_round_time)
                ctx.admin_chat_state = AdminState.change_round_time.value
                if ctx.session_started:
                    ctx.session.m = ctx.settings.seats_count

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

            case AdminState.add_mock_users.value:
                try:
                    mock_count = int(message.text)
                    if mock_count <= 0:
                        raise ValueError("Количество должно быть положительным")
                    
                    # Создаем моковых пользователей
                    start_id = -1  # Отрицательные ID для моковых пользователей
                    for i in range(mock_count):
                        mock_id = start_id - i
                        mock_name = f"Мок Пользователь {abs(mock_id)}"
                        ctx.users[mock_id] = models.UserInfo(
                            username=mock_name,
                            table_num=0,
                            user_state=models.UserState.ready.value,  # Моковые пользователи всегда готовы
                            is_mock=True
                        )
                        # Сразу добавляем их в сессию, если она уже запущена
                        if ctx.session_started:
                            ctx.session.add_participant(mock_id)
                    
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"Добавлено {mock_count} мок-пользователей",
                        reply_markup=markups.admin_main
                    )
                except (TypeError, ValueError) as e:
                    bot.send_message(
                        chat_id=message.chat.id,
                        text=f"Ошибка: {str(e)}. Введите положительное целое число.",
                        reply_markup=markups.admin_main
                    )
                ctx.admin_chat_state = AdminState.default.value

            case AdminState.default.value:
                pass

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(callback: types.CallbackQuery):
    ctx : AppContext = bot.context
    data = callback.data.split(':')[0]
    user_id = int(callback.message.chat.id)
    
    # --- Admin UI buttons ---
    if user_id == ctx.admin_chat_id:
        match(data):
            case markups.CallbackTypes.admin_round_start.value:
                ctx.session_started = True
                ctx.start_round(bot)
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
                # # Добавляем участника в шедулер
                # ctx.session.add_participant(user_id)

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
            user_id = int(callback.message.chat.id)

            if not ctx.users[user_id].is_mock:  # Обновляем сообщение только для реальных пользователей
                update_message(
                    bot=bot,
                    message=callback.message,
                    text=callback.message.text
                )

            ctx.users[user_id].user_state = models.UserState.ready.value

            ready_count, total_count = ctx.get_ready_users_count()
            
            bot.send_message(
                chat_id=ctx.admin_chat_id,
                text=f"Готовы: {ready_count} из {total_count}"
            )

            message_id = update_message_by_chat_and_message_id(
                bot=bot,
                chat_id=ctx.admin_chat_id,
                message_id=ctx.admin_chat_last_message_id,
                text=texts.show_ready_users(ready_count, total_count),
                keyboard=markups.start_session_before_everyone_ready
            )
            ctx.admin_chat_last_message_id = message_id

            if ready_count == total_count:
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
                    ctx.start_round(bot)
                    message_id = update_message_by_chat_and_message_id(
                        bot=bot,
                        chat_id=ctx.admin_chat_id,
                        message_id=ctx.admin_chat_last_message_id,
                        text=texts.all_users_ready_next
                    )

bot.infinity_polling()