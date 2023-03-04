from typing import Callable, Iterable, Any

from pytest import mark

from pyhandling.branchers import ActionChain
from pyhandling.language import then, BindingInfix, to, by


@mark.parametrize(
    'first_node, second_node, input_args',
    [
        (lambda x, y: x + y, lambda x: x ** x, (5, 3)),
        (lambda x: x**2 + 12, lambda x: x ** 4, (42, )),
        (lambda: 12, lambda x: x + 30, tuple())
    ]
)
def test_then_operator(
    first_node: Callable,
    second_node: Callable,
    input_args: Iterable
):
    assert (
        (first_node |then>> second_node)(*input_args)
        == ActionChain((first_node, second_node))(*input_args)
    )


@mark.parametrize(
    'infix, result',
    [
        (to, 16), (by, 12)
    ]
)
def test_single_binding_infix(infix: BindingInfix, result: Any):
    assert ((lambda a, b, c: (a + b) * c) |infix| 2)(2, 4) == result


@mark.parametrize(
    'infix, result',
    [
        (to, 39), (by, 64)
    ]
)
def test_keyword_binding_infix(infix: BindingInfix, result: Any):
    assert ((lambda a, b, c: (a + b) * c) |infix* (5, 8))(3) == result