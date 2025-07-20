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
    waiting_for_name = "WAITINGFORNAME"


class AppContext:
    def __init__(self, config):
        self.users = []
        self.usernames = dict()
        self.last_users = []
        self.admin_chat_id = config['telegram']['admin_chat_id']
        self.session_started = False
        self.settings = models.Settings(5, 4, 10)
        self.state = State.default
        self.scheduler = session.SessionScheduler(self.users, 1, 1)
        self.bots_count = 0
        self.app_service = AppService()



bot = telebot.TeleBot(token=config['telegram']['api_token'])
bot.context = AppContext(config)


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    ctx : AppContext = bot.context
    if message.chat.id == ctx.admin_chat_id:
        bot.send_message(chat_id=ctx.admin_chat_id, text=texts.welcome_admin(message.chat.first_name), reply_markup=markups.admin_main)
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


@bot.message_handler(commands=['addparticipant'])
def handle_add_participant(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    
    ctx.users.append(str(ctx.bots_count))
    ctx.bots_count += 1

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
        ctx.scheduler.remove_participant(removed_user)
        bot.send_message(
            chat_id=message.chat.id,
            text=f"Участник {removed_user} удален"
        )

@bot.message_handler(func=lambda m: m.chat.id == bot.context.admin_chat_id and m.text in [
    'Показать настройки ⚙️',
    'Изменить настройки ✏️',
    'Начать сессию 🚦',
    'Следующий раунд ⏭️',
    'Показать участников 👥',
    'Идеальные параметры 💡',
    'Закончить сессию 🛑'
])
def handle_admin_buttons(message: types.Message):
    ctx : AppContext = bot.context
    def get_ideal_tables_and_seats(n):
        best_tables = 1
        best_seats = n
        min_diff = n
        for tables in range(1, n+1):
            if n % tables == 0:
                seats = n // tables
                diff = abs(seats - tables)
                if diff < min_diff:
                    min_diff = diff
                    best_tables = tables
                    best_seats = seats
        return best_tables, best_seats
    count = len(ctx.users)
    tables, seats = get_ideal_tables_and_seats(count) if count > 0 else (0, 0)
    rounds = math.ceil((count-1) / (seats-1)) if count > 1 and seats > 1 else 1
    if message.text == 'Показать настройки ⚙️':
        bot.send_message(message.chat.id, texts.current_settings(settings=ctx.settings), reply_markup=markups.admin_main)
    elif message.text == 'Изменить настройки ✏️':
        bot.send_message(message.chat.id, texts.change_tables_count, reply_markup=None)
        bot.send_message(
            message.chat.id,
            f"Идеально: {tables} стол(а/ов) по {seats} мест\n"
            f"Минимальное число раундов для покрытия всех пар: {rounds}",
            reply_markup=None
        )
        ctx.state = State.change_tables_count.value
    elif message.text == 'Начать сессию 🚦':
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
            ctx.usernames[participant].table = table + 1
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
            f"Готовы: 0 из {len(ctx.users)}",
            reply_markup=None
        )
        ctx.ready_counter_msg_id = msg.message_id
        stats = ctx.scheduler.get_session_stats()
        # Отправляем метрики при начале сессии
        ctx.app_service.send_metrics(stats, ctx.settings)
    elif message.text == 'Следующий раунд ⏭️':
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
            message.chat.id,
            f"Готовы: 0 из {len(ctx.users)}",
            reply_markup=None
        )
        ctx.ready_counter_msg_id = msg.message_id
        bot.send_message(message.chat.id, ctx.scheduler.get_session_stats(), reply_markup=markups.admin_main)
        ctx.last_users = ctx.users.copy()
    elif message.text == 'Показать участников 👥':
        bot.send_message(
            message.chat.id,
            f"Количество участников: {count}",
            reply_markup=markups.admin_main
        )
    elif message.text == 'Идеальные параметры 💡':
        bot.send_message(
            message.chat.id,
            f"Идеально: {tables} стол(а/ов) по {seats} мест\n"
            f"Минимальное число раундов для покрытия всех пар: {rounds}",
            reply_markup=markups.admin_main
        )
    elif message.text == 'Закончить сессию 🛑':
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
        
        bot.send_message(message.chat.id, 'Сессия завершена. Все данные сброшены.', reply_markup=markups.admin_main)
        # Оповещаем всех участников
        for user_id in all_participants:
            try:
                bot.send_message(chat_id=int(user_id), text='Нетворкинг сессия завершена, спасибо за участие!')
            except Exception:
                pass

@bot.message_handler()
def handle_message(message: types.Message):
    ctx = bot.context
    # Обработка этапа ввода имени и фамилии
    if ctx.state == State.waiting_for_name.value and hasattr(ctx, 'pending_user_id') and message.chat.id == ctx.pending_user_id:
        fio = message.text.strip()
        if len(fio.split()) < 2:
            bot.send_message(chat_id=message.chat.id, text="Пожалуйста, введите имя и фамилию через пробел.")
            return
        ctx.pending_user_fio = fio
        ctx.state = State.default.value
        # Сохраняем ФИО в ctx.usernames через models.UserInfo, table=0
        ctx.usernames[str(message.chat.id)] = models.UserInfo(fio, 0)
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
        del ctx.pending_user_id
        del ctx.pending_user_fio
        return
    if message.chat.id == bot.context.admin_chat_id and message.text in [
        'Показать настройки ⚙️',
        'Изменить настройки ✏️',
        'Начать сессию 🚦',
        'Следующий раунд ⏭️',
        'Показать участников 👥',
        'Идеальные параметры 💡'
    ]:
        return
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
            bot.send_message(chat_id=message.chat.id, text="Введите время раунда в минутах:")
            ctx.state = State.change_round_time.value
        case State.change_round_time.value:
            try:
                ctx.settings.round_time = int(message.text)
            except (TypeError, ValueError):
                bot.send_message(chat_id=message.chat.id, text=texts.invalid_num_value)
                return
            bot.send_message(
                chat_id=message.chat.id,
                text=texts.current_settings(ctx.settings) + f"\nВремя раунда: {ctx.settings.round_time} мин.",
                reply_markup=markups.admin_main
            )
            ctx.state = State.default.value

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(callback: types.CallbackQuery):
    ctx : AppContext = bot.context
    data = callback.data.split(':')[0]
    # --- Admin UI buttons ---
    if callback.message.chat.id == ctx.admin_chat_id:
        if data == 'ADMIN_SHOWSETTINGS':
            bot.answer_callback_query(callback.id)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=texts.current_settings(settings=ctx.settings),
                reply_markup=markups.admin_main
            )
            return
        elif data == 'ADMIN_CHANGESETTINGS':
            bot.answer_callback_query(callback.id)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=texts.change_tables_count,
                reply_markup=None
            )
            ctx.state = State.change_tables_count.value
            return
        elif data == 'ADMIN_STARTSESSION':
            bot.answer_callback_query(callback.id)
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
                    bot.send_message(
                        chat_id=int(participant),
                        text=texts.show_users_current_table_num(table_num=table),
                        reply_markup=markups.user_ready
                    )
            stats = ctx.scheduler.get_session_stats()

            ctx.last_users = ctx.users.copy()
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=stats,
                reply_markup=markups.admin_main
            )
            return
        elif data == 'ADMIN_NEXTRND':
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
                    bot.send_message(
                        chat_id=int(participant),
                        text=texts.show_users_current_table_num(table_num=table),
                        reply_markup=markups.user_ready
                    )
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=ctx.scheduler.get_session_stats(),
                reply_markup=markups.admin_main
            )
            ctx.last_users = ctx.users.copy()
            return
        elif data == 'ADMIN_ADDPARTICIPANT':
            bot.answer_callback_query(callback.id)
            ctx.users.append(str(ctx.bots_count))
            ctx.bots_count += 1
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=f"Участник {ctx.users[-1]} добавлен",
                reply_markup=markups.admin_main
            )
            return
        elif data == 'ADMIN_REMOVEPARTICIPANT':
            bot.answer_callback_query(callback.id)
            if ctx.users:
                removed_user = ctx.users.pop()
                ctx.scheduler.remove_participant(removed_user)
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text=f"Участник {removed_user} удален",
                    reply_markup=markups.admin_main
                )
            else:
                bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.id,
                    text="Нет участников для удаления",
                    reply_markup=markups.admin_main
                )
            return
        elif data == 'ADMIN_SHOWPARTICIPANTS':
            bot.answer_callback_query(callback.id)
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text=f"Количество участников: {len(ctx.users)}",
                reply_markup=markups.admin_main
            )
            return
        elif data == 'ADMIN_ROUND_START':
            bot.answer_callback_query(callback.id)
            # Сообщение админу
            bot.edit_message_text(
                chat_id=callback.message.chat.id,
                message_id=callback.message.id,
                text='Раунд начался!',
                reply_markup=None
            )

            request_body = dict()
            # Сообщение участникам
            for participant in ctx.users:

                pid = str(participant)
                if hasattr(ctx, 'user_table_msgs') and pid in ctx.user_table_msgs:
                    try:
                        bot.edit_message_text(
                            chat_id=int(participant),
                            message_id=ctx.user_table_msgs[pid],
                            text='Раунд начался!'
                        )
                    except Exception:
                        msg = bot.send_message(
                            chat_id=int(participant),
                            text='Раунд начался!'
                        )
                        ctx.user_table_msgs[pid] = msg.message_id
                else:
                    msg = bot.send_message(
                        chat_id=int(participant),
                        text='Раунд начался!'
                    )
                    ctx.user_table_msgs[pid] = msg.message_id
            stats = ctx.scheduler.get_session_stats()
            ctx.last_users = ctx.users.copy()
            ctx.session_started = True  # после первого раунда больше не показываем кнопку 'Старт'
            bot.send_message(callback.message.chat.id, stats, reply_markup=markups.admin_main)

            ctx.app_service.update_users(ctx.usernames)

            return
    # --- Остальные действия ---
    match(data):
        case markups.CallbackTypes.register.value:
            # Новый этап: запрашиваем имя и фамилию
            ctx.state = State.waiting_for_name.value
            ctx.pending_user_id = callback.message.chat.id
            bot.send_message(
                chat_id=callback.message.chat.id,
                text="Пожалуйста, введите ваше имя и фамилию (через пробел):"
            )
        case markups.CallbackTypes.leave_session.value:
            if str(callback.message.chat.id) in ctx.users:
                ctx.users.remove(str(callback.message.chat.id))
                ctx.usernames.pop(callback.message.chat.id)
            try:
                ctx.scheduler.remove_participant(str(callback.message.chat.id))
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
                    text='Вы добавлены, ожидайте следующего раунда.'
                )
                bot.send_message(
                    chat_id=ctx.admin_chat_id,
                    text=f'Пользователь {id} зарегистрирован во время сессии и будет включён в следующий раунд.'
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
            if not hasattr(ctx, 'ready_users'):
                ctx.ready_users = set()
            ctx.ready_users.add(str(callback.message.chat.id))
            ready_count = len(ctx.ready_users)
            total_count = len(ctx.users)
            # Обновляем сообщение-счетчик
            if hasattr(ctx, 'ready_counter_msg_id'):
                try:
                    bot.edit_message_text(
                        chat_id=ctx.admin_chat_id,
                        message_id=ctx.ready_counter_msg_id,
                        text=f"Готовы: {ready_count} из {total_count}"
                    )
                except Exception:
                    pass
            if set(ctx.users) == ctx.ready_users:
                if not ctx.session_started:
                    bot.send_message(
                        chat_id=ctx.admin_chat_id,
                        text='Все участники готовы! Можно начинать раунд.',
                        reply_markup=markups.start_session_inline
                    )
                else:
                    bot.send_message(
                        chat_id=ctx.admin_chat_id,
                        text='Все участники готовы! Можно начинать следующий раунд.'
                    )

bot.infinity_polling()