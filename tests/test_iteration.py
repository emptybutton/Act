from typing import Iterable

from pytest import mark

from act.iteration import *
from act.testing import case_of


@mark.parametrize("items", [(1, 2, 3), range(10), "Hello world!", tuple(), str()])
def test_iteration_over(items: Iterable):
    iterate = iteration_over(items)

    for item in items:
        assert iterate() == item


@mark.parametrize("items", [(1, 2, 3), range(10), "Hello world!", tuple(), str()])
def test_iteration_over_by_generator(items: Iterable):
    iterate = iteration_over(item for item in items)

    for item in items:
        assert iterate() == item


test_infinite = case_of(
    (lambda: infinite(lambda _: StopIteration())(...), None),
    (lambda: infinite(lambda _: 8)(...), 8),
)


@mark.parametrize(
    "steps_to_false, number_of_runs",
    [(3, 12), (0, 10), (1, 4), (10, 33)]
)
def test_times(steps_to_false: int, number_of_runs: int):
    runner = times(steps_to_false)

    inital_steps_to_false = steps_to_false

    for _ in range(inital_steps_to_false):
        assert runner() is (steps_to_false > 0)

        if steps_to_false <= 0:
            steps_to_false = inital_steps_to_false

        steps_to_false -= 1
