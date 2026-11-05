import math
import random
from typing import List, Sequence, Set

from fogbed.fails.models import as_fraction


class NodeAvailabilitySchedule:
    def __init__(self, availability: float):
        ratio = as_fraction(availability)
        self.on_slots   = ratio.numerator
        self.cycle_size = ratio.denominator

    def is_on(self, slot: int) -> bool:
        return slot % self.cycle_size < self.on_slots


class InstanceAvailabilitySchedule:
    def __init__(self, nodes: Sequence[str], availability: float, rng: random.Random):
        self.nodes: List[str] = list(nodes)
        self.rng = rng
        self.down_ratio = len(self.nodes) * (1 - as_fraction(availability))

    def down_amount(self, slot: int) -> int:
        return math.floor((slot + 1) * self.down_ratio) - math.floor(slot * self.down_ratio)

    def down_nodes(self, slot: int) -> Set[str]:
        return set(self.rng.sample(self.nodes, self.down_amount(slot)))
