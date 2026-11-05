import random

import pytest

from fogbed.fails.models import SelectionMethod, SplitMethod
from fogbed.fails.selection import select_nodes, split_amount


@pytest.mark.parametrize('total, fail_rate, method, expected', [
    (10, 0.3, SplitMethod.UP, 3),
    (10, 0.3, SplitMethod.DOWN, 3),
    (3, 0.5, SplitMethod.UP, 2),
    (3, 0.5, SplitMethod.DOWN, 1),
    (4, 0.0, SplitMethod.UP, 0),
    (4, 1.0, SplitMethod.DOWN, 4),
    (0, 0.5, SplitMethod.UP, 0)
])
def test_deterministic_split(total, fail_rate, method, expected):
    assert split_amount(total, fail_rate, method, random.Random(0)) == expected


def test_random_split_rounds_to_neighbors_with_expected_mean():
    rng = random.Random(42)
    samples = [split_amount(3, 0.5, SplitMethod.RANDOM, rng) for _ in range(4000)]

    assert set(samples) == {1, 2}
    assert sum(samples) / len(samples) == pytest.approx(1.5, abs=0.05)


def test_random_split_is_exact_when_there_is_no_remainder():
    rng = random.Random(1)
    assert {split_amount(4, 0.5, SplitMethod.RANDOM, rng) for _ in range(100)} == {2}


def test_sequential_selection_takes_first_nodes():
    names = ['d1', 'd2', 'd3', 'd4']
    assert select_nodes(names, 2, SelectionMethod.SEQUENTIAL, random.Random(0)) == ['d1', 'd2']


@pytest.mark.parametrize('seed', range(20))
def test_random_selection_returns_amount_in_original_order(seed):
    names = ['d1', 'd2', 'd3', 'd4', 'd5']
    selected = select_nodes(names, 3, SelectionMethod.RANDOM, random.Random(seed))

    assert len(selected) == 3
    assert selected == [name for name in names if name in selected]


def test_random_selection_is_reproducible_with_seed():
    names = [f'd{i}' for i in range(10)]
    first = select_nodes(names, 4, SelectionMethod.RANDOM, random.Random(7))
    second = select_nodes(names, 4, SelectionMethod.RANDOM, random.Random(7))
    assert first == second


@pytest.mark.parametrize('method', list(SelectionMethod))
def test_selection_handles_empty_and_oversized_amounts(method):
    names = ['d1', 'd2']
    assert select_nodes(names, 0, method, random.Random(0)) == []
    assert select_nodes([], 3, method, random.Random(0)) == []
    assert sorted(select_nodes(names, 5, method, random.Random(0))) == names
