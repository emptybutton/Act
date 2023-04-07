from functools import partial
from typing import Any, Iterable, Mapping, Callable, Type, Optional

from pyhandling.arguments import ArgumentPack, ArgumentKey
from pyhandling.annotations import one_value_action
from pyhandling.branching import *
from pyhandling.testing import calling_test_case_of
from tests.mocks import MockAction, Counter, fail_by_error

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


test_repeating = calling_test_case_of(
    (lambda: repeating(lambda x: x + 1, lambda x: x < 10)(0), 10),
    (lambda: repeating(lambda x: x - 1, lambda x: x > 0)(0), 0),
)


@mark.parametrize(
    "number_of_handler_calls, number_of_checker_calls",
    [(i, i + 1) for i in range(3)] + [(100, 101), (653, 654), (999, 1000)]
)
def test_repeating_execution_sequences(
    number_of_handler_calls: int,
    number_of_checker_calls: int
):
    handling_counter = Counter()
    checking_counter = Counter()

    repeating(
        lambda _: handling_counter(),
        lambda _: checking_counter() or checking_counter.counted < number_of_checker_calls
    )(None)

    assert number_of_handler_calls == handling_counter.counted
    assert number_of_checker_calls == checking_counter.counted


test_on = calling_test_case_of(
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(4), 256),
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(-4), -4),
    (lambda: on(lambda x: x > 0, lambda x: x ** x)(-4), -4),
    (lambda: on(lambda x: x > 0, lambda _: _, else_=lambda x: -x)(4), 4),
    (lambda: on(lambda x: x > 0, lambda _: _, else_=lambda x: -x)(-4), 4),
)


test_rollbackable_without_error = calling_test_case_of(
    (lambda: rollbackable(lambda a: 1 / a, fail_by_error)(10), 0.1),
    (lambda: rollbackable(lambda a, b: a + b, fail_by_error)(5, 3), 8),
    (lambda: rollbackable(lambda a, b: a + b, fail_by_error)(5, b=3), 8),
    (lambda: rollbackable(lambda: 256, fail_by_error)(), 256),
)


@mark.parametrize(
    "func, input_args, error_type",
    [
        (lambda x: x / 0, (42, ), ZeroDivisionError),
        (lambda x, y: x + y, (1, '2'), TypeError),
        (lambda mapping, key: mapping[key], (tuple(), 0), IndexError),
        (lambda mapping, key: mapping[key], (tuple(), 10), IndexError),
        (lambda mapping, key: mapping[key], ((1, 2), 2), IndexError),
        (lambda mapping, key: mapping[key], (dict(), 'a'), KeyError),
        (lambda mapping, key: mapping[key], ({'a': 42}, 'b'), KeyError),
        (lambda: int('1' + '0'*4300), tuple(), ValueError)
    ]
)
def test_rollbackable_with_error(
    func: Callable,
    input_args: Iterable,
    error_type: Type[Exception]
):
    assert type(rollbackable(func, lambda error: error)(*input_args)) is error_type


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