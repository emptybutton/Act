from typing import Callable, Iterable

from pytest import mark

from pyhandling.branchers import ActionChain
from pyhandling.language import then, to, by


@mark.parametrize(
    'opening_handler, node_handler, input_args',
    [
        (lambda x, y: x + y, lambda x: x ** x, (5, 3)),
        (lambda x: x**2 + 12, lambda x: x ** 4, (42, )),
        (lambda: 12, lambda x: x + 30, tuple())
    ]
)
def test_then_operator(
    opening_handler: Callable,
    node_handler: Callable,
    input_args: Iterable
):
    assert (
        (opening_handler |then>> node_handler)(*input_args)
        == ActionChain(opening_handler, node_handler)(*input_args)
    )


def test_to_position_infix():
    func = lambda a, b, c: (a + b) * c

    assert (func |to| 2)(2, 4) == 16


def test_to_keyword_infix():
    func = lambda a, b, c: (a + b) * c

    assert (func |to* (3, 5))(8) == 64


def test_of_position_infix():
    func = lambda a, b, c: (a + b) * c

    assert (func |by| 4)(2, 2) == 16


def test_of_keyword_infix():
    func = lambda a, b, c: (a + b) * c

    assert (func |by* (5, 8))(3) == 64