import json

class Settings:

    def __init__(self, tables_count: int, seats_count: int, round_time: int, break_time: int = 1):
        self.tables_count = tables_count
        self.seats_count = seats_count
        self.round_time = round_time
        self.break_time = break_time


class UserInfo:
    '''
    :param username: Имя пользователя
    :param table: Стол, за которым пользователь сидит
    :param message_id: ID последнего сообщения с номером стола
    '''
    def __init__(self, username: str, table: int, message_id: int = None):
        self.username = username
        self.table = table
        self.message_id = message_id

        if len(username.split(' ')) > 1:
            self.initials = username.split(' ')[-1][0] + username.split(' ')[0][0]
        else:
            self.initials = username[0]
    
    def to_dict(self):
        return {
            'name': self.username,
            'initials': self.initials,
            'table_index': self.table
        }


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
