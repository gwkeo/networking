import requests
import json
from typing import List, Dict, Set, FrozenSet
from bin.models import UserInfo
import math
import itertools

class AppService:
    def __init__(self, base_url = "http://api:5050/api"):
        self.base_url = base_url
        self._met_pairs: Set[FrozenSet[int]] = set()  # Множество для хранения всех встретившихся пар
    
    def _get_all_possible_pairs(self, total_participants: int) -> Set[FrozenSet[int]]:
        """
        Вычисляет все возможные пары участников
        
        :param total_participants: Общее количество участников
        :return: Множество всех возможных пар
        """
        participants = range(1, total_participants + 1)
        return set(frozenset([i, j]) for i, j in itertools.combinations(participants, 2))

    def _update_met_pairs(self, round_tables: Dict[int, List[int]]) -> None:
        """
        Обновляет множество встретившихся пар на основе текущего раунда
        
        :param round_tables: Словарь {номер_стола: [список участников за столом]}
        """
        for table_participants in round_tables.values():
            # Добавляем все пары участников за текущим столом
            for i in range(len(table_participants)):
                for j in range(i + 1, len(table_participants)):
                    self._met_pairs.add(frozenset([table_participants[i], table_participants[j]]))

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
            # Очищаем множество встретившихся пар
            self._met_pairs.clear()
        except Exception as e:
            print(f"[DEBUG] Не удалось очистить метрики: {e}")

    def clear_dashboard(self):
        """Очищает весь дашборд - отправляет пустые данные для пользователей и метрик"""
        self.clear_users()
        self.clear_metrics()

    def send_metrics(self, stats, round_time, break_time, round_num):
        # Получаем текущие столы из stats
        current_tables = {}
        if 'current_round_tables' in stats:
            # Группируем участников по столам
            for user_id, table_idx in stats['current_round_tables'].items():
                if table_idx not in current_tables:
                    current_tables[table_idx] = []
                current_tables[table_idx].append(int(user_id))
            
            # Обновляем множество встретившихся пар
            self._update_met_pairs(current_tables)
        
        # Вычисляем все возможные пары
        all_pairs = self._get_all_possible_pairs(stats['total_participants'])
        
        # Вычисляем количество незнакомых пар
        strangers_num = len(all_pairs) - len(self._met_pairs)
        
        # Вычисляем необходимое количество раундов
        total_rounds = self.calculate_total_rounds(
            total_participants=stats['total_participants'],
            seats_per_table=stats['seats_per_table']
        )
        
        metrics_json = {
            "current_round": round_num,
            "total_rounds": total_rounds,
            "round_time_minutes": round_time,
            "break_time_minutes": break_time,
            "strangers_num": strangers_num
        }

        try:
            requests.post(
                url = self.base_url + "/metrics", 
                json=metrics_json
            )

        except Exception as e:
            print(f"[DEBUG] Не удалось отправить метрики: {e}: {metrics_json}")
            print(f"[DEBUG] Текущие столы: {current_tables}")
            print(f"[DEBUG] Всего пар: {len(all_pairs)}, встретившихся пар: {len(self._met_pairs)}")
        
        return metrics_json

    def calculate_total_rounds(self, total_participants: int, seats_per_table: int) -> int:
        """
        Вычисляет необходимое количество раундов
        
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

    def start_session(self):
        # При старте сессии очищаем множество встретившихся пар
        self._met_pairs.clear()
        requests.post(
            url = self.base_url + "/start"
        )

    def stop_session(self):
        # При остановке сессии очищаем множество встретившихся пар
        self._met_pairs.clear()
        requests.post(
            url = self.base_url + "/stop"
        )