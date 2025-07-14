import random
import itertools
from typing import List, Dict, Set, FrozenSet, Tuple, Optional


random_seed_num = 42

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
        random.seed(random_seed_num)
    
    def add_participants(self, new_participants: List[int]):
        """
        Добавить новых участников в сессию
        
        :param new_participants: Список новых участников
        """
        self.participants.extend(new_participants)
        self.p = len(self.participants)
    
    def get_all_pairs(self) -> Set[FrozenSet[int]]:
        """
        Получить все возможные пары участников
        
        :return: Множество всех возможных пар
        """
        return set(frozenset(pair) for pair in itertools.combinations(self.participants, 2))
    
    def generate_next_round(self, attempts: int = 100) -> Optional[Dict[int, int]]:
        """
        Генерирует следующий раунд сессии
        
        :param attempts: Количество попыток для поиска оптимальной рассадки
        :return: Словарь {участник: номер_стола} или None, если не удалось создать раунд
        """
        if len(self.participants) < 2:
            return None
            
        all_pairs = self.get_all_pairs()
        
        # Если все пары уже встретились, возвращаем None
        if len(self.met_pairs) >= len(all_pairs):
            print(f"DEBUG: Все пары уже встретились! met_pairs={len(self.met_pairs)}, all_pairs={len(all_pairs)}")
            return None
        
        best_tables = None
        best_new_pairs = -1
        
        # Пробуем несколько случайных рассадок и выбираем лучшую
        for attempt in range(attempts):
            shuffled_participants = self.participants.copy()
            random.shuffle(shuffled_participants)
            
            # Создаем столы
            tables = [shuffled_participants[i*self.m:(i+1)*self.m] for i in range(self.n)]
            
            # Подсчитываем новые пары
            new_pairs = set()
            for table in tables:
                for i in range(len(table)):
                    for j in range(i+1, len(table)):
                        pair = frozenset([table[i], table[j]])
                        if pair not in self.met_pairs:
                            new_pairs.add(pair)
            
            if len(new_pairs) > best_new_pairs:
                best_new_pairs = len(new_pairs)
                best_tables = tables
                
            # Если нашли максимально возможное количество новых пар, останавливаемся
            if best_new_pairs == self.n * (self.m * (self.m-1)) // 2:
                break
        
        # Если не удалось найти новые пары, возвращаем None
        if best_tables is None or best_new_pairs <= 0:
            print(f"DEBUG: Не удалось найти новые пары после {attempts} попыток. best_new_pairs={best_new_pairs}")
            return None
        
        print(f"DEBUG: Найдено {best_new_pairs} новых пар в раунде")
        
        # Формируем раунд по лучшей рассадке
        round_dict = {}
        for table_idx, table in enumerate(best_tables):
            for participant in table:
                round_dict[participant] = table_idx
            # Добавляем новые пары в множество встреченных
            for i in range(len(table)):
                for j in range(i+1, len(table)):
                    self.met_pairs.add(frozenset([table[i], table[j]]))
        
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
        return {
            'total_participants': len(self.participants),
            'total_rounds': len(self.rounds),
            'total_pairs': len(all_pairs),
            'met_pairs': len(self.met_pairs),
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


def generate_greedy_full_coverage_schedule(participants: List[int], n: int, m: int, attempts: int = 100, max_rounds_override: Optional[int] = None) -> List[Dict[int, int]]:
    """
    Генерирует полное расписание сессии (для обратной совместимости)
    
    :param participants: Список участников
    :param n: Количество столов
    :param m: Количество мест за столом
    :param attempts: Количество попыток для поиска оптимальной рассадки
    :param max_rounds_override: Максимальное количество раундов
    :return: Список раундов
    """
    scheduler = SessionScheduler(participants, n, m)
    
    if max_rounds_override is not None:
        max_rounds = max_rounds_override
    else:
        max_rounds = 10 * ((scheduler.p-1) // (m-1) + 2)
    
    for _ in range(max_rounds):
        round_dict = scheduler.generate_next_round(attempts)
        if round_dict is None:
            break
    
    return scheduler.rounds


# Пример использования:
if __name__ == "__main__":
    # Создаем планировщик сессии
    participants = [1, 2, 3, 4, 5, 6, 7, 8]
    scheduler = SessionScheduler(participants, n=2, m=4)
    
    print("Начальная сессия:")
    print(f"Участники: {scheduler.participants}")
    print(f"Столы: {scheduler.n}, мест за столом: {scheduler.m}")
    
    # Показываем начальное состояние
    scheduler.print_coverage_debug()
    
    # Генерируем раунды по одному
    round_num = 1
    while True:
        if round_num == 3:
            print(f"\nДобавляем новых участников...")
            scheduler.add_participants([9, 10])
            print(f"Новые участники: {scheduler.participants}")
            scheduler.print_coverage_debug()

        round_dict = scheduler.generate_next_round()
        if round_dict is None:
            print(f"\nГенерация раундов завершена на раунде {round_num-1}")
            break
        
        print(f"\nРаунд {round_num}:")
        for participant, table in round_dict.items():
            print(f"  Участник {participant} -> Стол {table}")
        
        stats = scheduler.get_session_stats()
        print(f"Покрытие: {stats['coverage_percentage']:.2%}")
        
        round_num += 1
    
    print(f"\nФинальная статистика:")
    final_stats = scheduler.get_session_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    # Показываем детальную информацию о покрытии
    scheduler.print_coverage_debug()
    
    # Проверяем повторные встречи
    scheduler.print_repeated_meetings_report()






    # Создаем планировщик сессии
    participants = [1, 2, 3, 4, 5, 6, 7, 8]
    scheduler = SessionScheduler(participants, n=2, m=4)
    
    print("Начальная сессия:")
    print(f"Участники: {scheduler.participants}")
    print(f"Столы: {scheduler.n}, мест за столом: {scheduler.m}")
    
    # Генерируем раунды по одному
    round_num = 1
    while True:
        if round_num == 2:
            print(f"\nДобавляем новых участников...")
            scheduler.add_participants([9, 10])
            print(f"Новые участники: {scheduler.participants}")

        round_dict = scheduler.generate_next_round()
        if round_dict is None:
            break
        
        print(f"\nРаунд {round_num}:")
        for participant, table in round_dict.items():
            print(f"  Участник {participant} -> Стол {table}")
        
        stats = scheduler.get_session_stats()
        print(f"Покрытие: {stats['coverage_percentage']:.2%}")
        
        round_num += 1
    
    print(f"\nФинальная статистика:")
    final_stats = scheduler.get_session_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    # Проверяем повторные встречи
    scheduler.print_repeated_meetings_report()






    # Создаем планировщик сессии
    participants = [1, 2, 3, 4, 5, 6, 7, 8]
    scheduler = SessionScheduler(participants, n=2, m=4)
    
    print("Начальная сессия:")
    print(f"Участники: {scheduler.participants}")
    print(f"Столы: {scheduler.n}, мест за столом: {scheduler.m}")
    
    # Генерируем раунды по одному
    round_num = 1
    while True:
        if round_num == 3:
            print(f"\nДобавляем новых участников...")
            scheduler.add_participants([9, 10])
            print(f"Новые участники: {scheduler.participants}")

        round_dict = scheduler.generate_next_round()
        if round_dict is None:
            break
        
        print(f"\nРаунд {round_num}:")
        for participant, table in round_dict.items():
            print(f"  Участник {participant} -> Стол {table}")
        
        stats = scheduler.get_session_stats()
        print(f"Покрытие: {stats['coverage_percentage']:.2%}")
        
        round_num += 1
    
    print(f"\nФинальная статистика:")
    final_stats = scheduler.get_session_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    # Проверяем повторные встречи
    scheduler.print_repeated_meetings_report()
    
    # Дополнительная проверка - создаем тестовый случай с повторами
    print(f"\n=== ТЕСТ С ПОВТОРАМИ ===")
    test_scheduler = SessionScheduler([1, 2, 3, 4], n=2, m=2)
    
    # Генерируем несколько раундов для маленькой группы
    for i in range(5):
        round_dict = test_scheduler.generate_next_round()
        if round_dict is None:
            break
        print(f"Раунд {i+1}: {round_dict}")
    
    test_scheduler.print_repeated_meetings_report()
