import requests
import json
from typing import Dict, Tuple
from bin.models import UserInfo
import math

class AppService:
    def __init__(self, base_url = "http://api:5000/api"):
        self.base_url = base_url
    

    def update_users(self, users: Dict[int, UserInfo]):
        request_body = json.dumps([val.to_dict() for key, val in users.items()])

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

        request_body = json.dumps([{}])

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
            response = requests.post("http://localhost:5000/api/metrics", json=empty_metrics)
            response.raise_for_status()
        except Exception as e:
            print(f"[DEBUG] Не удалось очистить метрики: {e}")

    def clear_dashboard(self):
        """Очищает весь дашборд - отправляет пустые данные для пользователей и метрик"""
        self.clear_users()
        self.clear_metrics()

    def send_metrics(self, stats, settings=None):
        total_rounds = math.ceil((stats['total_participants']-1) / (stats['seats_per_table']-1)) if stats['total_participants'] > 1 and stats['seats_per_table'] > 1 else 1

        # Используем настройки для времени, если они переданы
        round_time = getattr(settings, 'round_time', 2) if settings else 2
        break_time = getattr(settings, 'break_time', 1) if settings else 1

        metrics_json = {
            "current_round": stats['total_rounds'],
            "total_rounds": total_rounds,
            "round_time_minutes": round_time,
            "break_time_minutes": break_time,
            "strangers_num": stats['met_pairs'] if stats['met_pairs'] > 0 else 0
        }
        try:
            requests.post("http://localhost:5000/api/metrics", json=metrics_json)
        except Exception as e:
            print(f"[DEBUG] Не удалось отправить метрики: {e}")