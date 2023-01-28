from typing import Callable, Iterable

from pytest import mark

from pyhandling.branchers import ActionChain
from pyhandling.language import then, of, by


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


