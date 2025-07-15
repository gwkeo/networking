from telebot.util import quick_markup
from enum import Enum, auto


class CallbackTypes(Enum):
    register = "REGISTER"
    leave_session = "LEAVESESSION"
    accept_new_user = "ACCEPTNEWUSER"
    deny_new_user = "DENYNEWUSER"
    user_ready = "USERREADY"


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