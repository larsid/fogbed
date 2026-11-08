import math
import random
from typing import List, Sequence

from fogbed.fails.models import SelectionMethod, SplitMethod, as_fraction


def split_amount(total: int, fail_rate: float, split_method: SplitMethod, rng: random.Random) -> int:
    exact = total * as_fraction(fail_rate)
    lower = math.floor(exact)

    if(split_method == SplitMethod.DOWN):
        return lower
    if(split_method == SplitMethod.UP):
        return math.ceil(exact)

    remainder = exact - lower
    return lower + 1 if(rng.random() < remainder) else lower


def select_nodes(names: Sequence[str], amount: int, selection_method: SelectionMethod, rng: random.Random) -> List[str]:
    amount = max(0, min(amount, len(names)))

    if(selection_method == SelectionMethod.SEQUENTIAL):
        return list(names[:amount])

    selected = set(rng.sample(range(len(names)), amount))
    return [name for index, name in enumerate(names) if index in selected]
