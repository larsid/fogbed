from abc import ABC, abstractmethod
from enum import Enum
from fractions import Fraction
from typing import Any, Dict, Type


class SplitMethod(Enum):
    UP = 'up'
    DOWN = 'down'
    RANDOM = 'random'


class SelectionMethod(Enum):
    SEQUENTIAL = 'sequential'
    RANDOM = 'random'


class AvailabilityMode(Enum):
    CRASH = 'crash'
    DISCONNECT = 'disconnect'


MAX_DENOMINATOR = 1000


def as_fraction(value: float) -> Fraction:
    return Fraction(value).limit_denominator(MAX_DENOMINATOR)


def _verify_range(name: str, value: float, lower: float, upper: float):
    if(not lower <= value <= upper):
        raise ValueError(f'{name} must be between {lower} and {upper}, got {value}')


def _verify_positive(name: str, value: float):
    if(value <= 0):
        raise ValueError(f'{name} must be greater than 0, got {value}')


def _verify_non_negative(name: str, value: float):
    if(value < 0):
        raise ValueError(f'{name} must not be negative, got {value}')


class FailModel(ABC):
    kind = ''

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailModel':
        pass

    def __eq__(self, other: object) -> bool:
        if(not isinstance(other, FailModel)): return False
        return self.to_dict() == other.to_dict()

    def __repr__(self) -> str:
        fields = ', '.join(f'{key}={value}' for key, value in self.to_dict().items() if key != 'kind')
        return f'{type(self).__name__}({fields})'


class TimedFail(FailModel):
    def __init__(self,
        fail_rate: float = 0.5,
        split_method: SplitMethod = SplitMethod.UP,
        life_time: float = 30,
        selection_method: SelectionMethod = SelectionMethod.SEQUENTIAL
    ):
        _verify_range('fail_rate', fail_rate, 0, 1)
        _verify_non_negative('life_time', life_time)
        self.fail_rate        = fail_rate
        self.split_method     = SplitMethod(split_method)
        self.life_time        = life_time
        self.selection_method = SelectionMethod(selection_method)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'kind': self.kind,
            'fail_rate': self.fail_rate,
            'split_method': self.split_method.value,
            'life_time': self.life_time,
            'selection_method': self.selection_method.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimedFail':
        return cls(
            fail_rate=float(data['fail_rate']),
            split_method=SplitMethod(data['split_method']),
            life_time=float(data['life_time']),
            selection_method=SelectionMethod(data['selection_method'])
        )


class CrashFail(TimedFail):
    kind = 'crash'


class DisconnectFail(TimedFail):
    kind = 'disconnect'


class AvailabilityFail(FailModel):
    kind = 'availability'

    def __init__(self,
        availability: float = 0.5,
        slot_time: float = 2.0,
        availability_mode: AvailabilityMode = AvailabilityMode.CRASH
    ):
        _verify_range('availability', availability, 0, 1)
        _verify_positive('slot_time', slot_time)
        self.availability      = availability
        self.slot_time         = slot_time
        self.availability_mode = AvailabilityMode(availability_mode)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'kind': self.kind,
            'availability': self.availability,
            'slot_time': self.slot_time,
            'availability_mode': self.availability_mode.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AvailabilityFail':
        return cls(
            availability=float(data['availability']),
            slot_time=float(data['slot_time']),
            availability_mode=AvailabilityMode(data['availability_mode'])
        )


FAIL_MODELS: Dict[str, Type[FailModel]] = {
    CrashFail.kind: CrashFail,
    DisconnectFail.kind: DisconnectFail,
    AvailabilityFail.kind: AvailabilityFail
}


def fail_model_from_dict(data: Dict[str, Any]) -> FailModel:
    kind = data.get('kind')
    model = FAIL_MODELS.get(str(kind))

    if(model is None):
        raise ValueError(f'Unknown fail model kind: {kind}')

    try:
        return model.from_dict(data)
    except KeyError as ex:
        raise ValueError(f'Missing fail model param {ex}')
    except TypeError as ex:
        raise ValueError(f'Invalid fail model param: {ex}')
