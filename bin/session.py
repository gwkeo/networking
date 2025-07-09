import random
import itertools
from typing import List, Dict, Set, FrozenSet, Tuple


random_seed_num = 42



def generate_next_round(
    participants: List[int],
    n: int,
    m: int,
    met_pairs: Set[FrozenSet[int]],
    attempts: int = 100,
) -> Tuple[Dict[int, int], Set[FrozenSet[int]]]:
    """
    Генерирует следующий раунд рассадки за столами так, чтобы участники по максимуму
    взаимодействовали с новыми людьми.

    :param participants: список текущих участников
    :param n: число столов
    :param m: мест за столом
    :param met_pairs: множество уже встречавшихся пар (frozenset)
    :param attempts: сколько случайных рассадок пробовать
    :param seed: сид для генератора случайностей
    :return: кортеж (раунд, обновлённое множество met_pairs)
    """

    if random_seed_num is not None:
        random.seed(random_seed_num)

    best_tables = None
    best_new_pairs = -1

    for _ in range(attempts):
        random.shuffle(participants)
        tables = [participants[i*m:(i+1)*m] for i in range(n)]
        new_pairs = set()

        for table in tables:
            for i in range(len(table)):
                for j in range(i+1, len(table)):
                    pair = frozenset([table[i], table[j]])
                    if pair not in met_pairs:
                        new_pairs.add(pair)

        if len(new_pairs) > best_new_pairs:
            best_new_pairs = len(new_pairs)
            best_tables = tables

        if best_new_pairs == n * (m * (m-1)) // 2:
            break  # максимум новых знакомств за один раунд

    # Собираем результат
    round_dict = {}
    for table_idx, table in enumerate(best_tables):
        for participant in table:
            round_dict[participant] = table_idx
        for i in range(len(table)):
            for j in range(i+1, len(table)):
                met_pairs.add(frozenset([table[i], table[j]]))

    return round_dict, met_pairs


# def get_max_rounds(tables_num: int, seats_num: int):
#     limit_of_people = tables_num * seats_num
#     return 10 * ((limit_of_people - 1) // (seats_num - 1) + 2)

# def process_round(participants: List[int], tables_num: int, seats_num: int):

#     random.seed(random_seed_num)




def generate_greedy_full_coverage_schedule(participants: List[int], n: int, m: int, attempts: int = 100, max_rounds_override: int = None) -> List[Dict[int, int]]:
    p = n * m
    all_pairs = set(frozenset(pair) for pair in itertools.combinations(participants, 2))
    met_pairs = set()
    rounds = []
    if max_rounds_override is not None:
        max_rounds = max_rounds_override
    else:
        max_rounds = 10 * ((p-1) // (m-1) + 2)  # запас по раундам
    random.seed(42)
    for _ in range(max_rounds):
        best_tables = None
        best_new_pairs = -1
        # Пробую несколько случайных рассадок и выбираю лучшую
        for _ in range(attempts):
            random.shuffle(participants)
            tables = [participants[i*m:(i+1)*m] for i in range(n)]
            new_pairs = set()
            for table in tables:
                for i in range(len(table)):
                    for j in range(i+1, len(table)):
                        pair = frozenset([table[i], table[j]])
                        if pair not in met_pairs:
                            new_pairs.add(pair)
            if len(new_pairs) > best_new_pairs:
                best_new_pairs = len(new_pairs)
                best_tables = tables
            if best_new_pairs == n * (m * (m-1)) // 2:
                break
        # Формирую раунд по лучшей рассадке
        round_dict = {}
        for table_idx, table in enumerate(best_tables):
            for participant in table:
                round_dict[participant] = table_idx
            for i in range(len(table)):
                for j in range(i+1, len(table)):
                    met_pairs.add(frozenset([table[i], table[j]]))
        rounds.append(round_dict)
        if len(met_pairs) == len(all_pairs):
            break
    return rounds


if __name__ == "__main__":
    participants = [1, 2, 3, 4, 5, 6]
    n = 3
    m = 2
    met_pairs = set()
    all_rounds = []

    for _ in range(5):
        new_round, met_pairs = generate_next_round(participants, n, m, met_pairs)
        all_rounds.append(new_round)
        print(f"Раунд {len(all_rounds)}: {new_round}")