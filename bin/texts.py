from bin import models

start = "Нажмите на кнопку для регистрации на нетворкинг сессию"
registration_request_sent = 'Ваша заявка будет рассмотрена администратором. Пожалуйста, подождите'
session_already_started = "Сессия уже началась, регистрация закрыта"
user_left_session = "Вы покинули нетворкинг сессию"
registration_denied = "Ваш запрос был отклонен"
change_tables_count = "Введите число столов"
change_seats_count = "Введите число мест за столом"
invalid_num_value = "Введенное значение не является числовым. Введите число"
user_is_happy = "Вы зарегистрированы на мероприятие"
unavailable_session = "Сессия недоступна"
unable_to_start_session = "Не удалось начать сессию"

def show_users_current_table_num(table_num: int):
    return f"Подходите к столу №{table_num}"


def welcome_admin(name: str):
    return f"Добро пожаловать в админ-панель.\nПросмотреть текущие настройки - /showsettings\nИзменить настройки мероприятия - /changesettings\nНачать первый раунд сессии - /startsession"


def admin_chat_new_request(name: str):
    return f"Пользователь {name} пытается присоединиться к нетворкинг сессии"


def current_settings(settings: models.Settings):
    return f"Количество столов: {settings.tables_count}\nЧисло мест за столом: {settings.seats_count}"


def user_accepted_log(message: str):
    return f"{message}. Принят"


def user_declined_log(message: str):
    return f"{message}. Отклонен"

def user_left_session_log(name: str):
    return f"{name} покинул сессию"