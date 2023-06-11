from functools import partial
from typing import Callable, TypeVar

from pytest import mark

from pyhandling.scoping import *


_R = TypeVar('_R')


@mark.parametrize(
    "action, result",
    [
        (partial(value_in, 'c_'), 3),
        (partial(value_in, 'b_', scope_in=1), 2),
        (partial(value_in, 'a_', scope_in=2), 1),
    ]
)
def test_value_in(action: Callable[[], _R], result: _R):
    def a():
        a_ = 1
        return b()

    def b():
        b_ = 2
        return c()

    def c():
        c_ = 3
        return action()

    assert a() == result
