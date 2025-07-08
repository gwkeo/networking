import random
import itertools
from typing import List, Dict


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