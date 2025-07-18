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
    change_round_time = "CHANGEROUNDTIME"


class AppContext:
    def __init__(self, config):
        self.users = []
        self.last_users = []
        self.admin_chat_id = config['admin_chat_id']
        self.session_started = False
        self.settings = models.Settings(5, 4)
        self.settings.round_time = 10  # default 10 min
        self.state = State.default
        self.scheduler = session.SessionScheduler(self.users, 1, 1)
        self.bots_count = 0


bot = telebot.TeleBot(token=config['api_token'])
bot.context = AppContext(config)


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    ctx = bot.context
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
        if int(participant) > 100:
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

@bot.message_handler(commands=['showparticipants'])
def handle_show_participants(message: types.Message):
    ctx = bot.context
    if message.chat.id != ctx.admin_chat_id:
        return
    bot.send_message(chat_id=message.chat.id, text=f"Количество участников: {len(ctx.users)}")

@bot.message_handler(func=lambda m: m.chat.id == bot.context.admin_chat_id and m.text in [
    'Показать настройки ⚙️',
    'Изменить настройки ✏️',
    'Начать сессию 🚦',
    'Следующий раунд ⏭️',
    'Показать участников 👥',
    'Идеальные параметры 💡'
])
def handle_admin_buttons(message: types.Message):
    ctx = bot.context
    def get_ideal_tables_and_seats(n):
        import math
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
    import math
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
        ctx.scheduler = session.SessionScheduler(
            participants=ctx.users,
            n=ctx.settings.tables_count,
            m=ctx.settings.seats_count
        )
        round_dict = ctx.scheduler.generate_next_round()
        if round_dict is None:
            bot.send_message(message.chat.id, texts.unable_to_start_session, reply_markup=markups.admin_main)
            return
        for participant, table in round_dict.items():
            bot.send_message(
                chat_id=int(participant),
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )
        ctx.last_users = ctx.users.copy()
        ctx.ready_users = set()
        msg = bot.send_message(
            message.chat.id,
            f"Готовы: 0 из {len(ctx.users)}",
            reply_markup=None
        )
        ctx.ready_counter_msg_id = msg.message_id
    elif message.text == 'Следующий раунд ⏭️':
        round_dict = ctx.scheduler.generate_next_round()
        if round_dict is None:
            bot.send_message(message.chat.id, texts.unable_to_start_session, reply_markup=markups.admin_main)
            return
        for participant, table in round_dict.items():
            bot.send_message(
                chat_id=int(participant),
                text=texts.show_users_current_table_num(table_num=table),
                reply_markup=markups.user_ready
            )
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

@bot.message_handler()
def handle_message(message: types.Message):
    ctx = bot.context
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

@bot.callback_query_handler()
def handle_callback_query(callback: types.CallbackQuery):
    ctx = bot.context
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
            # Сообщение участникам
            for participant in ctx.users:
                bot.send_message(
                    chat_id=int(participant),
                    text='Раунд начался!'
                )
            # Не дублируем рассылку столов!
            stats = ctx.scheduler.get_session_stats()
            ctx.last_users = ctx.users.copy()
            # Убираем кнопку 'Старт' (редактируем сообщение, если нужно)
            # (уже убрано выше через edit_message_text)
            # После этого админ управляет только кнопкой 'Следующий раунд'
            bot.send_message(callback.message.chat.id, stats, reply_markup=markups.admin_main)
            return
    # --- Остальные действия ---
    match(data):
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
            if str(callback.message.chat.id) in ctx.users:
                ctx.users.remove(str(callback.message.chat.id))
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
            bot.send_message(
                chat_id=id,
                text=texts.user_is_happy,
                reply_markup=markups.leave_session
            )
            # Отправляем гифку после успешной регистрации
            with open('cat-hyppy.mp4', 'rb') as gif_file:
                bot.send_animation(chat_id=id, animation=gif_file)
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
                # Показываем только сообщение о готовности, без кнопки 'Старт'
                bot.send_message(
                    chat_id=ctx.admin_chat_id,
                    text='Все участники готовы! Можно начинать раунд.'
                )

@bot.message_handler(func=lambda m: m.chat.id == bot.context.admin_chat_id and m.text == 'Старт')
def handle_start_session_button(message: types.Message):
    pass  # больше не нужен, теперь старт через инлайн-кнопку

bot.infinity_polling()