from functools import partial
from typing import Any, Iterable, Mapping, Callable, Type, Optional

from pyhandling.annotations import atomic_action
from pyhandling.branchers import *
from pyhandling.errors import NeutralActionChainError
from pyhandling.tools import ArgumentKey
from tests.mocks import MockAction, Counter

from pytest import mark, fail, raises


@mark.parametrize(
    "args, kwargs",
    [
        ((1, 2, 3), dict()),
        (tuple(), dict(first=1, second=2)),
        ((1, 2, 3), dict(first=1, second=2)),
        (tuple(), dict()),
    ]
)
def test_neutral_action_chain_error_raising(args: Iterable, kwargs: Mapping):
    with raises(NeutralActionChainError):
        ActionChain()(*args, **kwargs)


test_action_chain_calling = calling_test_from(
    (ActionChain([lambda x: x + 2, lambda x: x ** x]), 256, [ArgumentPack.of(2)]),
    (ActionChain([lambda _: None]), None, [ArgumentPack.of(256)]),
    (ActionChain(), None, [ArgumentPack.of(None)]),
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
def test_action_chain_connection_to_other(first_nodes: Iterable[atomic_action], second_nodes: Iterable[atomic_action]):
    assert (
        tuple(ActionChain((*first_nodes, *second_nodes)))
        == tuple(ActionChain(first_nodes) >> ActionChain(second_nodes))
        == tuple(ActionChain(first_nodes) | ActionChain(second_nodes))
        == (*first_nodes, *second_nodes)
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


test_repeating = calling_test_from(
    (repeating(lambda x: x + 1, lambda x: x < 10), 10, ArgumentPack.of(0)),
    (repeating(lambda x: x - 1, lambda x: x > 0), 0, ArgumentPack.of(0)),
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


@mark.parametrize(
    "input_number, result",
    [
        (0, 1),
        (3, 27),
        (10, 10 ** 10),
        (20, 400),
        (100, 10_000)
    ]
)
def test_on_condition_by_numeric_functions(
    input_number: int | float,
    result: Any
):
    assert on_condition(
        lambda x: x <= 10,
        lambda x: x ** x,
        else_=lambda x: x * x
    )(input_number) == result


test_on_condition = calling_test_from(
    (on_condition(lambda x: x > 0, lambda x: x ** x), 256, ArgumentPack.of(4)),
    (on_condition(lambda x: x > 0, lambda x: x ** x), None, ArgumentPack.of(-4)),
    (on_condition(lambda x: x > 0, lambda x: x ** x), None, ArgumentPack.of(-4)),
    (on_condition(lambda x: x > 0, lambda _: _, else_=lambda x: -x), 4, ArgumentPack.of(4)),
    (on_condition(lambda x: x > 0, lambda _: _, else_=lambda x: -x), 4, ArgumentPack.of(-4)),
)


test_rollbackable_without_error = calling_test_from(
    (rollbackable(lambda a: 1 / a, fail_by_error), 0.1, ArgumentPack.of(10)),
    (rollbackable(lambda a, b: a + b, fail_by_error), 8, ArgumentPack.of(5, 3)),
    (rollbackable(lambda a, b: a + b, fail_by_error), 8, ArgumentPack.of(5, b=3)),
    (rollbackable(lambda: 256, fail_by_error), 256, ArgumentPack()),
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