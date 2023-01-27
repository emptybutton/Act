from typing import Any, Iterable

from pyhandling.shortcuts import *
from tests.mocks import Box

from pytest import mark


@mark.parametrize(
    "first_node, second_node, input_resource",
    [(lambda x: x * 2, str, 16), (str, lambda x: x * 2, 1)]
)
def test_next_action_decorator_of(first_node: Callable, second_node: Callable[[Any], Any], input_resource: Any):
    assert (
        next_action_decorator_of(second_node)(first_node)(input_resource)
        == ActionChain(first_node, second_node)(input_resource)
    )


@mark.parametrize(
    "first_node, second_node, input_resource",
    [(lambda x: x * 2, str, 16), (str, lambda x: x * 2, 1)]
)
def test_previous_action_decorator_of(first_node: Callable, second_node: Callable[[Any], Any], input_resource: Any):
    assert (
        previous_action_decorator_of(first_node)(second_node)(input_resource)
        == ActionChain(first_node, second_node)(input_resource)
    )


@mark.parametrize(
    "resource, arguments",
    [
        (256, tuple()),
        (42, (1, 2, 3)),
        (None, (1, 2, 3)),
    ]
)
def test_take(resource: Any, arguments: Iterable):
    assert take(resource)(*arguments) == resource