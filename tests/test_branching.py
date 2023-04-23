from functools import partial
from typing import Any, Iterable, Mapping, Callable, Type, Optional

from pyhandling.arguments import ArgumentPack, ArgumentKey
from pyhandling.annotations import one_value_action
from pyhandling.branching import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import MockAction

from pytest import mark, fail, raises


test_action_chain_calling = calling_test_case_of(
    (lambda: ActionChain([lambda x: x + 2, lambda x: x ** x])(2), 256),
    (lambda: ActionChain([lambda _: None])(256), None),
    (lambda: ActionChain()(None), None),
)


@mark.parametrize(
    'first_nodes, second_nodes',
    [
        [(MockAction(), lambda x: x + 1), (MockAction(), MockAction())],
        [(MockAction(), lambda x: x + 1, MockAction()), (MockAction(), )],
        [(MockAction(), ), (MockAction(), MockAction())],
        [(MockAction(), lambda x: x + 1), tuple()],
        [tuple(), (MockAction(), )],
        [tuple(), tuple()]
    ]
)
def test_action_chain_connection_to_other(first_nodes: Iterable[one_value_action], second_nodes: Iterable[one_value_action]):
    assert (
        tuple(ActionChain((*first_nodes, *second_nodes)))
        == tuple(ActionChain(first_nodes) >> ActionChain(second_nodes))
        == tuple(ActionChain(first_nodes) | ActionChain(second_nodes))
        == (*first_nodes, *second_nodes)
    )


test_merged = calling_test_case_of(
    (
        lambda: merged(lambda a: a - 1, lambda _: _, lambda a: a + 1)(2),
        (1, 2, 3),
    ),
)


@mark.parametrize(
    "factor, original_x, original_y, original_z",
    [
        (1, 2, 4, 4), (0.5, 4, 4, 12), (2, 8, 1, -78), (10, 12, 3, 12),
        (0, 1000, 2000, 3000), (100, 10, 10, 0), (-3, 2, -3, 14), (-1, -2, -3, -4)
    ]
)
def test_mergely_by_formula_function(
    factor: int | float,
    original_x: int | float,
    original_y: int | float,
    original_z: int | float,
):
    assert mergely(
        lambda factor: (lambda x, y, z: factor * (x ** y + z)),
        lambda factor: factor * original_x,
        lambda factor: factor * original_y,
        lambda factor: factor * original_z,
    )(factor) == factor * ((factor * original_x) ** (factor * original_y) + (factor * original_z))


def test_action_chain_one_resource_call_operator(input_resource: int | float = 30):
    chain = ActionChain((lambda x: x * x + 12, lambda x: x ** x))

    result_of_chain_normal_call = chain(input_resource)

    assert (input_resource >= chain) == result_of_chain_normal_call
    assert (chain <= input_resource) == result_of_chain_normal_call


test_action_inserting_in = calling_test_case_of(
    (lambda: binding_by([..., (lambda b: b / 2)])(lambda a: a + 3)(13), 8),
    (lambda: binding_by([(lambda a: a + 3), ...])(lambda b: b / 2)(13), 8),
    (lambda: binding_by([..., ...])(lambda a: a + 2)(12), 16)
)


test_test_bind = calling_test_case_of(
    (lambda: bind(lambda a: a / 2, lambda a: a + 6)(4), 8),
)


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