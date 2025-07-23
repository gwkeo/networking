from telebot.util import quick_markup
from enum import Enum, auto
from telebot import types


class CallbackTypes(Enum):
    register = "REGISTER"
    leave_session = "LEAVESESSION"
    accept_new_user = "ACCEPTNEWUSER"
    deny_new_user = "DENYNEWUSER"
    user_ready = "USERREADY"
    admin_round_start = "ADMIN_ROUND_START"

class AdminButtons(Enum):
    show_settings = "Показать настройки ⚙️"
    change_settings = "Изменить настройки ✏️"
    start_session = "Начать сессию 🚦"
    next_round = "Следующий раунд ⏭️"
    show_users = "Показать участников 👥"
    ideal_parameters = "Идеальные параметры 💡"
    finish_session = "Закончить сессию 🛑"

    @classmethod
    def to_array(cls):
        return [member.value for member in cls]

register_markup = quick_markup({
    'Зарегистрироваться': {'callback_data': CallbackTypes.register.value}
}, row_width=2)


leave_session = quick_markup({
    'Выйти': {'callback_data': CallbackTypes.leave_session.value}
}, row_width=2)


def request_actions(id: int):
    return quick_markup({
        'Принять': {
            'callback_data': f"{CallbackTypes.accept_new_user.value}:{id}"
        },
        'Отклонить': {
            'callback_data': f"{CallbackTypes.deny_new_user.value}:{id}"
        }
    }, row_width=2)


user_ready = quick_markup({
    'Готов': {
        'callback_data': f"{CallbackTypes.user_ready.value}"
    },
    'Выйти': {
        'callback_data': f"{CallbackTypes.leave_session.value}"
    }
}, row_width=2)


admin_main = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
admin_main.add(
    types.KeyboardButton('Показать настройки ⚙️'),
    types.KeyboardButton('Изменить настройки ✏️'),
    types.KeyboardButton('Начать сессию 🚦'),
    types.KeyboardButton('Следующий раунд ⏭️'),
    types.KeyboardButton('Показать участников 👥'),
    types.KeyboardButton('Идеальные параметры 💡'),
    types.KeyboardButton('Закончить сессию 🛑')
)

start_session = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
start_session.add(types.KeyboardButton('Старт'))

start_session_inline = quick_markup({
    'Старт': {'callback_data': CallbackTypes.admin_round_start.value}
}, row_width=1)

start_session_before_everyone_ready = quick_markup({
    'Стартовать сразу': {'callback_data': CallbackTypes.admin_round_start.value}
}, row_width=1)

if __name__ == "__main__":
    a = AdminButtons.to_array()
    print(a)