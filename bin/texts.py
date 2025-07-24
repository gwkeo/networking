from bin import models

start = "Нажмите на кнопку для регистрации на нетворкинг сессию\n\nНажимая на кнопку, вы соглашаетесь на предоставление персональных данных"
registration_request_sent = 'Ваша заявка будет рассмотрена администратором. Пожалуйста, подождите'
session_already_started = "Сессия уже началась, регистрация закрыта"
user_left_session = "Вы покинули нетворкинг сессию"
registration_denied = "Ваш запрос был отклонен"
change_tables_count = "Введите число столов"
change_seats_count = "Введите число мест за столом"
change_round_time = "Введите время раунда в минутах:"
invalid_num_value = "Введенное значение не является числовым. Введите число"
user_is_happy = "Вы зарегистрированы на мероприятие"
unavailable_session = "Сессия недоступна"
unable_to_start_session = "Не удалось начать сессию"
unable_to_start_next_round = "Не удалось начать следующий раунд"
round_started = "Раунд начался!"
round_started_without_you = "Раунд начался без вас, так как вы не успели отметиться готовым. Ожидайте следующего раунда."
no_users_to_remove = "Нет участников для удаления"
enter_name_surname = "Пожалуйста, введите ваше имя и фамилию (через пробел):"
session_finished = "Сессия завершена. Все данные сброшены."
session_finished_thanks = "Нетворкинг сессия завершена, спасибо за участие!"
all_users_ready_start = "Все участники готовы! Можно начинать раунд."
all_users_ready_next = "Все участники готовы! Можно начинать следующий раунд."
wait_for_next_round = "Вы добавлены, ожидайте следующего раунда."
you_left = "Вы вышли"

mock_help_message = """
Использование команды /mock:

/mock add [количество] - добавить мок-пользователей (по умолчанию 1)
/mock remove - удалить всех мок-пользователей
/mock list - показать список активных мок-пользователей
"""

def show_users_count(users_count: int):
    return f"Количество участников: {users_count}"

def unable_to_update_users(error: str):
    return f"Не удалось обновить пользователей: {error}"

def unable_to_update_metrics(error: str):
    return f"Не удалось обновить метрики: {error}"

def show_ideal_tables_and_seats(tables: int, seats: int, rounds: int):
    return f"Идеально: {tables} стол(а/ов) по {seats} мест\nМинимальное число раундов для покрытия всех пар: {rounds}"

def show_ready_users(count: int, all_users: int):
    return f"Готовы: {count} из {all_users}"

def show_users_current_table_num(table_num: int, round_num: int = 1):
    return f"Раунд {round_num}. Подходите к столу №{table_num + 1}\n"

def welcome_admin(name: str):
    return f"Добро пожаловать в админ-панель"

def admin_chat_new_request(name: str):
    return f"Пользователь {name} пытается присоединиться к нетворкинг сессии"

def current_settings(settings: models.Settings):
    return f"Количество столов: {settings.tables_count}\nЧисло мест за столом: {settings.seats_count}\nВремя раунда: {settings.round_time} минут"

def user_accepted_log(message: str):
    return f"{message}. Принят"

def user_declined_log(message: str):
    return f"{message}. Отклонен"

def user_left_session_log(name: str):
    return f"{name} покинул сессию"

def user_removed(user_id: str):
    return f"Участник {user_id} удален"

def user_added(user_id: str):
    return f"Участник {user_id} добавлен"

def user_registered_during_session(user_id: str):
    return f"Пользователь {user_id} зарегистрирован во время сессии и будет включён в следующий раунд."