import random
import itertools
from typing import List, Dict, Set, FrozenSet, Optional
import math


random_seed_num = 42

def split_into_tables(participants: List[int], num_tables: int, seats_per_table: int) -> List[List[int]]:
    """
    Распределяет участников по столам с учетом ограничений:
    - За каждым столом должно быть минимум 2 человека
    - За столом не должно быть больше seats_per_table человек
    - Распределение должно быть максимально равномерным
    
    :param participants: Список участников
    :param num_tables: Максимальное количество столов
    :param seats_per_table: Количество мест за столом
    :return: Список столов с участниками
    """
    if not participants or len(participants) < 2:
        return []
        
    total_participants = len(participants)
    
    # Вычисляем оптимальное количество столов
    # Учитываем, что за столом должно быть минимум 2 человека
    max_possible_tables = min(num_tables, total_participants // 2)
    if max_possible_tables == 0:
        return []
        
    # Создаем пустые столы
    tables = [[] for _ in range(max_possible_tables)]
    remaining_participants = participants.copy()
    
    # Сначала обеспечиваем минимум 2 человека за каждым столом
    for table in tables:
        if len(remaining_participants) >= 2:
            # Добавляем двух случайных участников
            for _ in range(2):
                participant = random.choice(remaining_participants)
                table.append(participant)
                remaining_participants.remove(participant)
        else:
            break
    
    # Удаляем столы, где не набралось 2 человека
    tables = [table for table in tables if len(table) >= 2]
    
    # Распределяем оставшихся участников
    while remaining_participants:
        # Находим столы с наименьшим количеством участников
        min_size = min(len(table) for table in tables)
        available_tables = [i for i, table in enumerate(tables) if len(table) < seats_per_table and len(table) == min_size]
        
        if not available_tables:
            # Если все столы заполнены до максимума, но есть минимум 2 участника,
            # создаем новый стол (если не превышен лимит столов)
            if len(remaining_participants) >= 2 and len(tables) < num_tables:
                new_table = []
                for _ in range(2):
                    participant = random.choice(remaining_participants)
                    new_table.append(participant)
                    remaining_participants.remove(participant)
                tables.append(new_table)
                continue
            else:
                # Добавляем оставшихся участников к существующим столам
                for participant in remaining_participants[:]:
                    for table in tables:
                        if len(table) < seats_per_table:
                            table.append(participant)
                            remaining_participants.remove(participant)
                            break
                break
        
        # Выбираем случайный стол из доступных
        table_idx = random.choice(available_tables)
        participant = random.choice(remaining_participants)
        tables[table_idx].append(participant)
        remaining_participants.remove(participant)
    
    return tables

class SessionScheduler:
    def __init__(self, participants: List[int], n: int, m: int):
        """
        Инициализация планировщика сессии
        
        :param participants: Список участников
        :param n: Количество столов
        :param m: Количество мест за столом
        """
        self.participants = participants.copy()
        self.n = n
        self.m = m
        self.p = n * m
        self.met_pairs = set()
        self.rounds = []
        self._max_rounds = get_max_rounds(len(participants), m)  # Сохраняем максимальное количество раундов
        random.seed(random_seed_num)
    
    def add_participant(self, new_participant: int):
        self.participants.append(new_participant)
        self.p = len(self.participants)
        # Обновляем максимальное количество раундов при добавлении участника
        new_max_rounds = get_max_rounds(len(self.participants), self.m)
        self._max_rounds = max(self._max_rounds, new_max_rounds)
    
    def add_participants(self, new_participants: List[int]):
        """
        Добавить новых участников в сессию
        
        :param new_participants: Список новых участников
        """
        self.participants.extend(new_participants)
        self.p = len(self.participants)
        # Обновляем максимальное количество раундов при добавлении участников
        new_max_rounds = get_max_rounds(len(self.participants), self.m)
        self._max_rounds = max(self._max_rounds, new_max_rounds)
    
    def remove_participant(self, participant: int):
        self.participants.remove(participant)
        self.p = len(self.participants)

    def get_all_pairs(self) -> Set[FrozenSet[int]]:
        """
        Получить все возможные пары участников
        
        :return: Множество всех возможных пар
        """
        return set(frozenset(pair) for pair in itertools.combinations(self.participants, 2))
    
    def _get_unpaired_participants(self) -> Set[FrozenSet[int]]:
        """
        Возвращает множество пар участников, которые еще не встречались
        """
        all_pairs = self.get_all_pairs()
        return all_pairs - self.met_pairs

    def _evaluate_table_configuration(self, tables: List[List[int]]) -> int:
        """
        Оценивает конфигурацию столов по количеству новых пар и их приоритету
        
        :param tables: Список столов с участниками
        :return: Оценка конфигурации (чем выше, тем лучше)
        """
        score = 0
        new_pairs = set()
        unpaired = self._get_unpaired_participants()
        
        # Подсчитываем новые пары для каждого стола
        for table in tables:
            table_pairs = set()
            for i in range(len(table)):
                for j in range(i+1, len(table)):
                    pair = frozenset([table[i], table[j]])
                    table_pairs.add(pair)
                    if pair not in self.met_pairs:
                        new_pairs.add(pair)
                        # Даем больший вес парам, которые еще не встречались
                        score += 100
                        
        # Штрафуем за неравномерное распределение
        min_size = min(len(table) for table in tables)
        max_size = max(len(table) for table in tables)
        size_diff_penalty = (max_size - min_size) * 10
        score -= size_diff_penalty
        
        # Поощряем использование приоритетных пар
        priority_pairs = 0
        for pair in new_pairs:
            if pair in unpaired:
                priority_pairs += 1
        score += priority_pairs * 50
        
        return score

    def generate_next_round(self, attempts: int = 1000) -> Optional[Dict[int, int]]:
        """
        Генерирует следующий раунд сессии с использованием жадного алгоритма
        
        :param attempts: Количество попыток для поиска оптимальной рассадки
        :return: Словарь {участник: номер_стола} или None, если не удалось создать раунд
        """
        if len(self.participants) < 2:
            return None
            
        # Проверяем, не превышено ли максимальное количество раундов
        if len(self.rounds) >= self._max_rounds:
            print(f"DEBUG: Достигнуто максимальное количество раундов ({self._max_rounds})")
            return None
            
        all_pairs = self.get_all_pairs()
        
        # Если все пары уже встретились, возвращаем None
        if len(self.met_pairs) >= len(all_pairs):
            print(f"DEBUG: Все пары уже встретились! met_pairs={len(self.met_pairs)}, all_pairs={len(all_pairs)}")
            return None
        
        best_tables = None
        best_score = float('-inf')
        
        # Увеличиваем количество попыток для последних раундов
        remaining_pairs = len(all_pairs) - len(self.met_pairs)
        if remaining_pairs < len(all_pairs) * 0.2:  # Если осталось менее 20% пар
            attempts *= 2
        
        # Пробуем несколько случайных рассадок и выбираем лучшую
        for attempt in range(attempts):
            # Приоритизируем участников, у которых меньше встреч
            participant_meetings = {p: 0 for p in self.participants}
            for pair in self.met_pairs:
                for p in pair:
                    participant_meetings[p] += 1
                    
            # Сортируем участников по количеству встреч (меньше встреч - выше приоритет)
            shuffled_participants = sorted(
                self.participants,
                key=lambda p: (participant_meetings[p], random.random())
            )
            
            # Используем функцию распределения по столам
            tables = split_into_tables(shuffled_participants, self.n, self.m)
            
            # Оцениваем конфигурацию
            score = self._evaluate_table_configuration(tables)
            
            if score > best_score:
                best_score = score
                best_tables = tables
                
                # Если нашли идеальную конфигурацию, останавливаемся
                unpaired = self._get_unpaired_participants()
            new_pairs = set()
            for table in tables:
                for i in range(len(table)):
                    for j in range(i+1, len(table)):
                        pair = frozenset([table[i], table[j]])
                        if pair not in self.met_pairs:
                            new_pairs.add(pair)
            
                if all(pair in new_pairs for pair in unpaired):
                    break
        
        # Если не удалось найти хорошую конфигурацию
        if best_tables is None or best_score <= 0:
            print(f"DEBUG: Не удалось найти хорошую конфигурацию после {attempts} попыток. best_score={best_score}")
            return None
        
        print(f"DEBUG: Найдена конфигурация с оценкой {best_score}")
        
        # Формируем раунд по лучшей рассадке
        round_dict = {}
        new_pairs_count = 0
        for table_idx, table in enumerate(best_tables):
            for participant in table:
                round_dict[participant] = table_idx
            # Добавляем новые пары в множество встреченных
            for i in range(len(table)):
                for j in range(i+1, len(table)):
                    pair = frozenset([table[i], table[j]])
                    if pair not in self.met_pairs:
                        new_pairs_count += 1
                    self.met_pairs.add(pair)
        
        print(f"DEBUG: Добавлено {new_pairs_count} новых пар в раунде")
        self.rounds.append(round_dict)
        return round_dict
    
    def get_coverage_percentage(self) -> float:
        """
        Получить процент покрытия всех возможных пар
        
        :return: Процент покрытия от 0.0 до 1.0
        """
        all_pairs = self.get_all_pairs()
        if len(all_pairs) == 0:
            return 1.0
        return len(self.met_pairs) / len(all_pairs)
    
    def get_session_stats(self) -> Dict:
        """
        Получить статистику сессии
        
        :return: Словарь со статистикой
        """
        all_pairs = self.get_all_pairs()
        met_users = set()
        for first, second in self.met_pairs:
            if first not in met_users:
                met_users.add(first)
            if second not in met_users:
                met_users.add(second)

        return {
            'total_participants': len(self.participants),
            'total_rounds': len(self.rounds),
            'max_rounds': self._max_rounds,  # Добавляем информацию о максимальном количестве раундов
            'total_pairs': len(all_pairs),
            'met_pairs': len(self.met_pairs),
            'met_users': len(met_users),
            'coverage_percentage': self.get_coverage_percentage(),
            'tables': self.n,
            'seats_per_table': self.m
        }
    
    def check_repeated_meetings(self) -> Dict:
        """
        Проверяет повторные встречи участников
        
        :return: Словарь со статистикой повторных встреч
        """
        pair_meeting_count = {}
        repeated_meetings = []
        
        # Подсчитываем количество встреч для каждой пары
        for round_dict in self.rounds:
            # Группируем участников по столам
            tables = {}
            for participant, table_id in round_dict.items():
                if table_id not in tables:
                    tables[table_id] = []
                tables[table_id].append(participant)
            
            # Проверяем пары в каждом столе
            for table_participants in tables.values():
                for i in range(len(table_participants)):
                    for j in range(i+1, len(table_participants)):
                        pair = frozenset([table_participants[i], table_participants[j]])
                        if pair not in pair_meeting_count:
                            pair_meeting_count[pair] = 0
                        pair_meeting_count[pair] += 1
        
        # Находим повторные встречи
        for pair, count in pair_meeting_count.items():
            if count > 1:
                repeated_meetings.append({
                    'participants': list(pair),
                    'meeting_count': count
                })
        
        # Сортируем по количеству повторений (по убыванию)
        repeated_meetings.sort(key=lambda x: x['meeting_count'], reverse=True)
        
        total_repeated_pairs = len(repeated_meetings)
        total_repeated_meetings = sum(item['meeting_count'] - 1 for item in repeated_meetings)
        
        return {
            'total_pairs_checked': len(pair_meeting_count),
            'repeated_pairs': total_repeated_pairs,
            'total_repeated_meetings': total_repeated_meetings,
            'repeated_meetings_list': repeated_meetings,
            'duplicate_percentage': (total_repeated_pairs / len(pair_meeting_count) * 100) if pair_meeting_count else 0
        }
    
    def print_repeated_meetings_report(self):
        """
        Выводит отчет о повторных встречах
        """
        stats = self.check_repeated_meetings()
        
        print(f"\n=== ОТЧЕТ О ПОВТОРНЫХ ВСТРЕЧАХ ===")
        print(f"Всего проверено пар: {stats['total_pairs_checked']}")
        print(f"Пар с повторными встречами: {stats['repeated_pairs']}")
        print(f"Всего повторных встреч: {stats['total_repeated_meetings']}")
        print(f"Процент пар с повторами: {stats['duplicate_percentage']:.2f}%")
        
        if stats['repeated_meetings_list']:
            print(f"\nДетализация повторных встреч:")
            for item in stats['repeated_meetings_list']:
                participants = item['participants']
                count = item['meeting_count']
                print(f"  Участники {participants[0]} и {participants[1]} встретились {count} раз")
        else:
            print(f"\nПовторных встреч не обнаружено!")
    
    def print_coverage_debug(self):
        """
        Выводит детальную информацию о покрытии пар для отладки
        """
        all_pairs = self.get_all_pairs()
        met_pairs = self.met_pairs
        
        print(f"\n=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ О ПОКРЫТИИ ===")
        print(f"Всего возможных пар: {len(all_pairs)}")
        print(f"Встреченных пар: {len(met_pairs)}")
        print(f"Покрытие: {len(met_pairs)/len(all_pairs)*100:.2f}%")
        
        # Показываем все возможные пары
        print(f"\nВсе возможные пары:")
        for pair in sorted(all_pairs):
            pair_list = list(pair)
            status = "✓" if pair in met_pairs else "✗"
            print(f"  {status} {pair_list[0]} - {pair_list[1]}")
        
        # Показываем непокрытые пары
        uncovered_pairs = all_pairs - met_pairs
        if uncovered_pairs:
            print(f"\nНепокрытые пары ({len(uncovered_pairs)}):")
            for pair in sorted(uncovered_pairs):
                pair_list = list(pair)
                print(f"  ✗ {pair_list[0]} - {pair_list[1]}")
        else:
            print(f"\nВсе пары покрыты!")


def get_ideal_tables_and_seats(n):
    if n <= 0:
        return (0, 0)
    best_tables = 1
    best_seats = n
    min_diff = n
    for tables in range(1, n+1):
        if n % tables == 0:
            seats = n // tables
            diff = abs(seats - tables)
            if diff < min_diff:
                min_diff = diff
                best_tables = tables
                best_seats = seats
    return best_tables, best_seats

def get_max_rounds(users_count: int, seats_count: int):
    if users_count > 1 and seats_count > 1:
        return math.ceil((users_count - 1) / (seats_count - 1))
    return 1

def test_seating_configurations():
    """
    Тестирует различные конфигурации рассадки участников
    """
    test_cases = [
        {
            "name": "Полное покрытие - 6 участников, 2 стола по 3 места",
            "participants": list(range(1, 7)),
            "tables": 2,
            "seats": 3
        },
        {
            "name": "Полное покрытие - 8 участников, 3 стола по 3 места",
            "participants": list(range(1, 9)),
            "tables": 3,
            "seats": 3
        },
        {
            "name": "Полное покрытие - 9 участников, 3 стола по 3 места",
            "participants": list(range(1, 10)),
            "tables": 3,
            "seats": 3
        },
        {
            "name": "Полное покрытие - 12 участников, 4 стола по 3 места",
            "participants": list(range(1, 13)),
            "tables": 4,
            "seats": 3
        }
    ]

    for test_case in test_cases:
        print(f"\n=== {test_case['name']} ===")
        scheduler = SessionScheduler(
            participants=test_case['participants'],
            n=test_case['tables'],
            m=test_case['seats']
        )
        
        print(f"Участники: {test_case['participants']}")
        print(f"Столов: {test_case['tables']}, мест за столом: {test_case['seats']}")
        print(f"Теоретический максимум раундов: {scheduler._max_rounds}")
        
        round_num = 0
        all_pairs = scheduler.get_all_pairs()
        total_pairs = len(all_pairs)
        
        while True:
            round_dict = scheduler.generate_next_round()
            if round_dict is None:
                print(f"\nРаунд {round_num + 1}: невозможно создать новый раунд")
                break
                
            round_num += 1
            
            # Группируем участников по столам
            tables = {}
            for participant, table_idx in round_dict.items():
                if table_idx not in tables:
                    tables[table_idx] = []
                tables[table_idx].append(participant)
            
            print(f"\nРаунд {round_num}:")
            for table_idx, participants in sorted(tables.items()):
                print(f"Стол {table_idx + 1}: {sorted(participants)} ({len(participants)} человек)")
            
            # Проверяем условия
            errors = []
            for table in tables.values():
                if len(table) < 2:
                    errors.append(f"Ошибка: за столом {table} сидит менее 2 человек")
                if len(table) > test_case['seats']:
                    errors.append(f"Ошибка: за столом {table} сидит больше {test_case['seats']} человек")
            
            if errors:
                print("Найдены ошибки:")
                for error in errors:
                    print(f"- {error}")
            
            # Выводим прогресс покрытия пар
            coverage = len(scheduler.met_pairs) / total_pairs * 100
            print(f"Прогресс: {len(scheduler.met_pairs)}/{total_pairs} пар ({coverage:.1f}%)")
            
            # Если все пары встретились, можно остановиться
            if len(scheduler.met_pairs) == total_pairs:
                print("\nДостигнуто 100% покрытие пар!")
                break
        
        # Выводим итоговую статистику
        stats = scheduler.get_session_stats()
        print(f"\nИтоговая статистика:")
        print(f"- Всего раундов: {stats['total_rounds']}")
        print(f"- Процент покрытия пар: {stats['coverage_percentage']*100:.1f}%")
        print(f"- Количество встреченных пар: {stats['met_pairs']} из {stats['total_pairs']}")
        
        # Проверяем повторные встречи
        repeated = scheduler.check_repeated_meetings()
        print(f"- Пар с повторными встречами: {repeated['repeated_pairs']}")
        print(f"- Всего повторных встреч: {repeated['total_repeated_meetings']}")

if __name__ == '__main__':
    test_seating_configurations()