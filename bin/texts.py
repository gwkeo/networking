from bin import models

start = "Нажмите на кнопку для регистрации на нетворкинг сессию"
registration_request_sent = 'Ваша заявка будет рассмотрена администратором. Пожалуйста, подождите'
session_already_started = "Сессия уже началась, регистрация закрыта"
user_left_session = "Вы покинули нетворкинг сессию"
registration_denied = "Ваш запрос был отклонен"


def current_table_of_user(table_num: int):
    return f"Подходите к столу №{table_num}"


def welcome_admin(name: str):
    return f"Добро пожаловать в админ-панель.\nМеню настроек - /settings\nНачать первый раунд сессии - /startsession"


def admin_chat_new_request(name: str):
    return f"Пользователь {name} пытается присоединиться к нетворкинг сессии"


def current_settings(settings: models.Settings):
    return f"Количество столов: {settings.tables_count}\nЧисло мест за столом: {settings.seats_count}"


def user_accepted_log(message: str):
    return f"{message}. Принят"


def user_declined_log(message: str):
    return f"{message}. Отклонен"