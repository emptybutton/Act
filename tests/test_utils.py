from typing import Any, Iterable, Type, Callable, Mapping

from pyannotating import number
from pytest import mark, raises

from pyhandling.annotations import checker_of, ResourceT
from pyhandling.branchers import ActionChain
from pyhandling.error_controllers import BadResourceWrapper, BadResourceError, IBadResourceKeeper
from pyhandling.synonyms import raise_
from pyhandling.tools import ArgumentPack
from pyhandling.utils import *
from tests.mocks import Box, Counter, MockHandler


@mark.parametrize('result, object_, method_name', (('<Box instance>', Box(), '__repr__'), ))
def test_callmethod(result: Any, object_: object, method_name: str):
    assert callmethod(object_, method_name) == result


@mark.parametrize(
    'sign, first_operand, second_operand, result',
    (('+', 2, 2, 4), ('/', 16, 4, 4), ('+', (1, 2), (3, 4), (1, 2, 3, 4)))
)
def test_operation_of(sign: str, first_operand: Any, second_operand: Any, result: Any):
    assert operation_of(sign)(first_operand, second_operand) == result


@mark.parametrize(
    "checker, resource, result",
    (
        ((lambda number: number <= 0), 4, 4),
        ((lambda number: number <= 0), 0, BadResourceWrapper(0)),
        ((lambda number: number <= 0), -64, BadResourceWrapper(-64))
    )
)
def test_bad_resource_wrapping_on(checker: checker_of[ResourceT], resource: ResourceT, result: Any):
    resource_wrapper = bad_resource_wrapping_on(checker)(resource)

    if type(resource_wrapper) is BadResourceWrapper and type(result) is BadResourceWrapper:
        assert resource_wrapper.bad_resource == result.bad_resource
    else:
        assert resource_wrapper == result


@mark.parametrize(
    "checker, number, result",
    ((lambda number: number < 10, 3, 3), (lambda number: number < 10, 11, 12))
)
def test_skipping_on(checker: checker_of[number], number: number, result: Any):
    assert skipping_on(checker)(lambda number: number + 1)(number) == result


@mark.parametrize(
    "func, arguments",
    (
        (lambda a, b, c: a + b + c, (1, 2, 3)),
        (lambda number: number + 4, (60, )),
        (lambda: 256, tuple()),
    )
)
def test_collection_unpacking_in(func: Callable, arguments: Iterable):
    assert collection_unpacking_in(func)(arguments) == func(*arguments)


@mark.parametrize(
    "func, arguments",
    (
        (lambda a, b, c: a + b + c, dict(a=1, b=2, c=3)),
        (lambda number: number + 4, dict(number=60)),
        (lambda: 256, dict()),
    )
)
def test_keyword_unpacking_in(func: Callable, arguments: Mapping):
    assert keyword_unpacking_in(func)(arguments) == func(**arguments)


@mark.parametrize(
    'input_collections, output_collection',
    [
        [((1, 2, 3), (4, 5)), (1, 2, 3, 4, 5)],
        [((1, 2), tuple(), (3, 4, 5), tuple(), (6, 7)), (1, 2, 3, 4, 5, 6, 7)],
        [((1, 2, 3), (4, (5, 6))), (1, 2, 3, 4, (5, 6))],
        [[[[[[42]]]]], ([[[42]]], )],
        [tuple(), tuple()],
    ]
)
def test_summed_collection_from(input_collections: Iterable[Iterable], output_collection: tuple):
    assert summed_collection_from(*input_collections) == output_collection


@mark.parametrize(
    "first_node, second_node, input_resource",
    [(lambda x: x * 2, str, 16), (str, lambda x: x * 2, 1)]
)
def test_action_binding_of(first_node: Callable, second_node: Callable[[Any], Any], input_resource: Any):
    assert (
        action_binding_of(second_node)(first_node)(input_resource)
        == ActionChain((first_node, second_node))(input_resource)
    )


@mark.parametrize(
    "first_node, second_node, input_resource",
    [(lambda x: x * 2, str, 16), (str, lambda x: x * 2, 1)]
)
def test_left_action_binding_of(first_node: Callable, second_node: Callable[[Any], Any], input_resource: Any):
    assert (
        left_action_binding_of(first_node)(second_node)(input_resource)
        == ActionChain((first_node, second_node))(input_resource)
    )


@mark.parametrize(
    "func, arguments, extra_arguments",
    [(pow, (4, 2), tuple()), (pow, (4, 4), (1, 2, 3))]
)
def test_event_as(func: Callable, arguments: Iterable, extra_arguments: Iterable):
    assert event_as(func, *arguments)(extra_arguments) == func(*arguments)


@mark.parametrize("items", [(1, 2, 3), "Hello world!", range(10)])
def test_collection_from(items: Iterable):
    assert collection_from(*items) == tuple(items)


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


@mark.parametrize(
    'initial_log_number, logging_amount',
    [(0, 0), (4, 0), (4, 8), (0, 8), (32, 16), (128, 128)]
)
def test_number_of_logger_logs(initial_log_number: int, logging_amount: int):
    logger = Logger((str(), ) * initial_log_number)

    for _ in range(logging_amount):
        logger(str())

    assert len(logger.logs) == initial_log_number + logging_amount


@mark.parametrize(
    "number_of_handlers, number_of_writer_calls",
    tuple(map(
        lambda number: (number, number),
        (*range(0, 4), 32, 64, 128, 516)
    ))
)
def test_showly_by_logger(number_of_handlers: int, number_of_writer_calls: int):
    writing_counter = Counter()

    showly(
        (
            MockHandler()
            if number_of_handlers == 1
            else ActionChain((MockHandler(), ) * number_of_handlers)
        ),
        writer=lambda _: writing_counter()
    )(None)

    assert writing_counter.counted == number_of_writer_calls


@mark.parametrize(
    "input_resource, result",
    [
        (42, (42, )),
        (None, (None, )),
        ([1, 2, 3], (1, 2, 3)),
        (map(lambda x: x ** 2, [4, 8, 16]), (16, 64, 256)),
        ((3, 9, 12), (3, 9, 12)),
        (tuple(), tuple()),
        (list(), tuple()),
        ('Hello', ('H', 'e', 'l', 'l', 'o'))
    ]
)
def test_as_collection(input_resource: Any, result: tuple):
    assert as_collection(input_resource) == result


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


@mark.parametrize(
    "error_type, error",
    [
        (TypeError, TypeError()),
        (IndexError, IndexError()),
        (KeyError, KeyError()),
        (Exception, Exception()),
        (Exception, KeyError())
    ]
)
def test_error_raising_of_optional_raising_of(error_type: Type[Exception], error: Exception):
    with raises(error_type):
        optional_raising_of(error_type)(error)


@mark.parametrize(
    "error_type, input_resource",
    [
        (Exception, str()),
        (TypeError, int()),
        (AttributeError, (1, 2, 3)),
        (AttributeError, (item for item in range(10))),
    ]
)
def test_resource_returning_of_optional_raising_of(
    error_type: Type[Exception],
    input_resource: Any
):
    assert optional_raising_of(error_type)(input_resource) == input_resource


@mark.parametrize(
    "handler, error_checker, input_resource, result",
    [
        (lambda x: x + 10, lambda _: True, 32, 42),
        (
            lambda x: x / 0,
            lambda error: isinstance(error, ZeroDivisionError),
            256,
            BadResourceError(256, ZeroDivisionError())
        ),
        (
            lambda x: x.non_existent_attribute,
            lambda error: isinstance(error, AttributeError),
            str(),
            BadResourceError(str(), AttributeError())
        ),
    ]
)
def test_returnly_rollbackable(
    handler: Callable[[Any], Any],
    error_checker: Callable[[Exception], Any],
    input_resource: Any,
    result: Any
):
    returnly_rollbackable_result = returnly_rollbackable(handler, error_checker)(input_resource)

    if type(result) is BadResourceError:
        assert returnly_rollbackable_result.bad_resource == result.bad_resource
        assert type(returnly_rollbackable_result.error) is type(result.error)

    else:
        assert returnly_rollbackable_result == result


@mark.parametrize(
    "handler, error_checker, input_resource, expected_error_type",
    [
        (lambda x: x / 0, lambda error: isinstance(error, TypeError), 32, ZeroDivisionError),
        (lambda x: 21 + x, lambda error: isinstance(error, AttributeError), '21', TypeError),
        (lambda x: x.non_existent_attribute, lambda error: isinstance(error, SyntaxError), tuple(), AttributeError),
    ]
)
def test_returnly_rollbackable_error_returning(
    handler: Callable[[Any], Any],
    error_checker: Callable[[Exception], Any],
    input_resource: Any,
    expected_error_type: Type[Exception]
):
    with raises(expected_error_type):
        returnly_rollbackable(handler, error_checker)(input_resource)


@mark.parametrize(
    "nodes, input_resource, result",
    [
        (ActionChain((lambda x: x + 2, BadResourceWrapper, lambda x: x.resource * 2)), 40, 42),
        (
            [
                returnly_rollbackable(
                    lambda x: x / 0,
                    lambda error: isinstance(error, ZeroDivisionError)
                )
            ],
            42,
            42
        ),
        (ActionChain(), 42, 42),
        (tuple(), 256, 256),
        ([lambda x: x ** x], 4, 256),
        ([lambda x: x ** 2, lambda x: x ** x], 2, 256),
        (
            [
                lambda x: x ** 2,
                lambda x: x ** x,
                lambda x: x + 80,
                lambda x: x >> 3,
                BadResourceWrapper
            ],
            2,
            42
        )
    ]
)
def test_maybe(
    nodes: Iterable[Callable],
    input_resource: Any,
    result: Any
):
    maybe_result = maybe(nodes)(input_resource)

    assert (
        (maybe_result.bad_resource if isinstance(maybe_result, IBadResourceKeeper) else maybe_result)
        == result
    )


@mark.parametrize(
    "input_resource, result",
    [
        (42, 42),
        ((item for item in range(64)), ) * 2,
        (BadResourceWrapper("Some bad resource"), "Some bad resource"),
        (BadResourceError(256, Exception()), 256)
    ]
)
def test_optional_bad_resource_from(input_resource: Any, result: Any):
    assert optional_bad_resource_from(input_resource) == result


@mark.parametrize(
    "error_checker, chain, input_resource, expected_result",
    [
        (lambda err: isinstance(err, ZeroDivisionError), [lambda x: x + 1, lambda x: x / 0], 255, 256),
        (lambda err: isinstance(err, ZeroDivisionError), [lambda x: x / 2, lambda x: x / 0], 128, 64),
        (lambda err: isinstance(err, ZeroDivisionError), [lambda x: x / 2, lambda x: x * 4], 128, 256),
    ]
)
def test_chain_breaking_on_error_that(
    error_checker: Callable[[Exception], bool],
    chain: Iterable[Callable],
    input_resource: Any,
    expected_result: Any
):
    result = chain_breaking_on_error_that(error_checker)(chain)(input_resource)
    
    if isinstance(result, IBadResourceKeeper):
        assert result.bad_resource == expected_result
    else:
        assert result == expected_result