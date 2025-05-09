from abc import ABC
from enum import Enum, auto


class FailMode(Enum):
    CRASH = auto()
    DISCONNECT = auto()
    AVAILABILITY = auto()


class FailModel(ABC):
    def __init__(self, mode: FailMode):
        self.mode = mode