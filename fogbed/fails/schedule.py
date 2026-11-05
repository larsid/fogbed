import math
import random
from typing import List, Optional, Sequence, Set

from fogbed.fails.models import as_fraction


class NodeAvailabilitySchedule:
    def __init__(self, availability: float):
        ratio = as_fraction(availability)
        self.on_slots   = ratio.numerator
        self.cycle_size = ratio.denominator

    def is_on(self, slot: int) -> bool:
        return slot % self.cycle_size < self.on_slots


class InstanceAvailabilitySchedule:
    def __init__(self, nodes: Sequence[str], availability: float, seed: Optional[str] = None):
        self.nodes: List[str] = list(nodes)
        self.seed = seed
        self.down_ratio = len(self.nodes) * (1 - as_fraction(availability))
        self._rng = random.Random()

    def down_amount(self, slot: int) -> int:
        return math.floor((slot + 1) * self.down_ratio) - math.floor(slot * self.down_ratio)

    def down_nodes(self, slot: int) -> Set[str]:
        rng = self._rng if(self.seed is None) else random.Random(f'{self.seed}:{slot}')
        return set(rng.sample(self.nodes, self.down_amount(slot)))
