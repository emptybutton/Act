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
