import json
from enum import Enum

class Settings:

    def __init__(self, tables_count: int, seats_count: int, round_time: int, break_time: int = 1):
        self.tables_count = tables_count
        self.seats_count = seats_count
        self.round_time = round_time
        self.break_time = break_time


class UserState(Enum):
    default = "DEFAULT"
    waiting_for_name = "WAITING_FOR_NAME"
    registered = "REGISTERED"
    ready = "READY"


class UserInfo:
    '''
    :param username: Имя пользователя
    :param table: Стол, за которым пользователь сидит
    :param message_id: ID последнего сообщения с номером стола
    :param is_mock: Флаг, указывающий является ли пользователь моком
    '''
    def __init__(self, table_num: int = 0, username: str = None, user_state : UserState = UserState.default.value, message_id: int = None, is_mock: bool = False):
        self.username = username
        self.table_num = table_num
        self.message_id = message_id
        self.is_mock = is_mock
        self.user_state : UserState = user_state

        if self.username != None:
            if len(username.split(' ')) > 1:
                self.initials = username.split(' ')[0][0] + username.split(' ')[-1][0]
            else:
                self.initials = username[0]

    def to_dict(self):
        return {
            "name": self.username,
            "initials": self.initials,
            "table_index": self.table_num,
            "is_mock": self.is_mock
        }
    
    def is_ready(self) -> bool:
        return True if self.user_state == UserState.ready.value else False

class MockUserInfo(UserInfo):
    '''
    Класс для мок-пользователей, которые используются для тестирования
    '''
    def __init__(self, username: str, table_num: int = 0):
        super().__init__(username=username, table_num=table_num, message_id=None, is_mock=True)


class Metrics:
    def __init__(self, persent_unique_meetings: int, round_num: int, 
                 people_num: int, tables: int, seats: list):
        self.persent_unique_meetings = persent_unique_meetings
        self.round_num = round_num
        self.people_num = people_num
        self.tables = tables
        self.seats = seats


if __name__ == '__main__':
    ui = UserInfo("Rakhman Imanov", 2)
    d = {1: ui, 2: ui}

    print(json.dumps([val.to_dict() for key, val in d.items()]))
