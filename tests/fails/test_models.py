import json

import pytest

from fogbed.fails.models import (
    AvailabilityFail,
    AvailabilityMode,
    CrashFail,
    DisconnectFail,
    SelectionMethod,
    SplitMethod,
    as_fraction,
    fail_model_from_dict
)


@pytest.mark.parametrize('model', [
    CrashFail(),
    CrashFail(fail_rate=0.3, split_method=SplitMethod.RANDOM, life_time=12.5, selection_method=SelectionMethod.RANDOM),
    DisconnectFail(fail_rate=1, split_method=SplitMethod.DOWN, life_time=0),
    AvailabilityFail(),
    AvailabilityFail(availability=0.25, slot_time=0.5, availability_mode=AvailabilityMode.DISCONNECT)
])
def test_fail_model_survives_json_round_trip(model):
    data = json.loads(json.dumps(model.to_dict()))
    restored = fail_model_from_dict(data)

    assert type(restored) is type(model)
    assert restored == model


def test_crash_and_disconnect_are_distinct_kinds():
    assert CrashFail().to_dict()['kind'] == 'crash'
    assert DisconnectFail().to_dict()['kind'] == 'disconnect'
    assert CrashFail() != DisconnectFail()


def test_enums_are_serialized_by_value():
    data = AvailabilityFail(availability_mode=AvailabilityMode.DISCONNECT).to_dict()
    assert data['availability_mode'] == 'disconnect'


@pytest.mark.parametrize('factory', [
    lambda: CrashFail(fail_rate=-0.1),
    lambda: CrashFail(fail_rate=1.1),
    lambda: DisconnectFail(life_time=-1),
    lambda: AvailabilityFail(availability=1.5),
    lambda: AvailabilityFail(slot_time=0)
])
def test_invalid_params_are_rejected(factory):
    with pytest.raises(ValueError):
        factory()


@pytest.mark.parametrize('data', [
    {},
    {'kind': 'unknown'},
    {'kind': 'crash'},
    {'kind': 'crash', 'fail_rate': None, 'split_method': 'up', 'life_time': 1, 'selection_method': 'sequential'},
    {'kind': 'crash', 'fail_rate': 0.5, 'split_method': 'sideways', 'life_time': 1, 'selection_method': 'sequential'},
    {'kind': 'availability', 'availability': 2, 'slot_time': 1, 'availability_mode': 'crash'}
])
def test_invalid_dicts_are_rejected(data):
    with pytest.raises(ValueError):
        fail_model_from_dict(data)


def test_as_fraction_avoids_float_noise():
    assert as_fraction(0.1 * 3) == as_fraction(0.3)
    assert as_fraction(0.25).denominator == 4
    assert as_fraction(0.7).denominator == 10
