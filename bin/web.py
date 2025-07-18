import socketio
from types import List, Dict

class Server:
    def __init__(self):
        self.sio = socketio.Client()

        try:
            self.sio.connect('http://localhost:5000')
            print("Подключено к WebSocket серверу")
        except Exception as e:
            print(f"Ошибка подключения к WebSocket: {e}")


    def send_users_list(self, users: Dict[int, int]):
        result = []
        for users, table in users:
            result.append({
                'table_index': table
            })

        self.sio.emit('users_info', result)