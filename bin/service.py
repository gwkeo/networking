import requests
import json
from typing import List
from bin.models import UserInfo
import math

class AppService:
    def __init__(self, base_url = "http://api:5050/api"):
        self.base_url = base_url
    

    def update_users(self, users: List[UserInfo]):
        request_body = json.dumps([user.to_dict() for user in users])

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        try:
            response = requests.post(
                url = self.base_url + '/users',
                data = request_body,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            return response.json() if response.content else {"status": "success"}
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Ошибка при отправке данных: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка при обработке JSON ответа: {str(e)}")

    def clear_users(self):
        """Отправляет пустой массив пользователей для очистки дашборда"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        request_body = json.dumps([])

        try:
            response = requests.post(
                url = self.base_url + '/users',
                data = request_body,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            return response.json() if response.content else {"status": "success"}
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Не удалось очистить пользователей: {e}")
        except json.JSONDecodeError as e:
            print(f"[DEBUG] Ошибка при обработке JSON ответа: {e}")

    def clear_metrics(self):
        """Отправляет пустые метрики для очистки дашборда"""
        empty_metrics = {
            "current_round": 0,
            "total_rounds": 0,
            "round_time_minutes": 0,
            "break_time_minutes": 0,
            "strangers_num": 0
        }
        
        try:
            response = requests.post(
                url = self.base_url + "/metrics", 
                json=empty_metrics
            )
            response.raise_for_status()
        except Exception as e:
            print(f"[DEBUG] Не удалось очистить метрики: {e}")

    def clear_dashboard(self):
        """Очищает весь дашборд - отправляет пустые данные для пользователей и метрик"""
        self.clear_users()
        self.clear_metrics()

    def calculate_total_rounds(self, total_participants: int, seats_per_table: int) -> int:
        """
        Вычисляет необходимое количество раундов для того, чтобы каждый участник встретился со всеми.
        
        Args:
            total_participants (int): Общее количество участников
            seats_per_table (int): Количество мест за одним столом
            
        Returns:
            int: Необходимое количество раундов
        """
        if total_participants <= 1 or seats_per_table <= 1:
            return 1
            
        # За один раунд участник встречается с (seats_per_table-1) новыми людьми
        # Всего нужно встретиться с (total_participants-1) людьми
        return math.ceil((total_participants - 1) / (seats_per_table - 1))

    def send_metrics(self, stats, round_time, break_time):
        # Вычисляем необходимое количество раундов
        total_rounds = self.calculate_total_rounds(
            total_participants=stats['total_participants'],
            seats_per_table=stats['seats_per_table']
        )

        # Если текущее количество раундов больше расчетного, используем его
        # Это может произойти, если часть участников покинула сессию
        if stats['total_rounds'] > total_rounds:
            total_rounds = stats['total_rounds']
        
        metrics_json = {
            "current_round": stats['total_rounds'],
            "total_rounds": total_rounds,
            "round_time_minutes": round_time,
            "break_time_minutes": break_time,
            "strangers_num": stats['total_participants'] - stats['met_users']
        }

        try:
            requests.post(
                url = self.base_url + "/metrics", 
                json=metrics_json
            )

        except Exception as e:
            print(f"[DEBUG] Не удалось отправить метрики: {e}: {metrics_json}")

    def start_session(self):
        requests.post(
            url = self.base_url + "/start"
        )

    def stop_session(self):
        requests.post(
            url = self.base_url + "/stop"
        )