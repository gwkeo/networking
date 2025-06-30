from telebot.util import quick_markup
from enum import Enum


class CallbackTypes(Enum):
    register = "REGISTER"
    leave_session = "LEAVE_SESSION"


register_markup = quick_markup({
    'Зарегистрироваться': {'callback_data': CallbackTypes.register.value}
}, row_width=2)


active_session_markup = quick_markup({
    'Выйти': {'callback_data': CallbackTypes.leave_session.value}
}, row_width=2)