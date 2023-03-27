from typing import Any, Iterable, Type, Callable, Mapping, Optional

from pyannotating import number, many_or_one
from pytest import mark, raises

from pyhandling.annotations import checker_of, ResourceT, event_for
from pyhandling.branchers import ActionChain
from pyhandling.synonyms import with_context_by
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import ArgumentPack
from pyhandling.utils import *
from tests.mocks import with_attributes, CustomContext, Counter, MockAction


@mark.parametrize(
    "object_, method_name, result",
    (
        (CustomContext(), "__repr__", "<CustomContext instance>"),
        (with_attributes(method=lambda: 256), "method", 256)
    )
)
def test_callmethod(object_: object, method_name: str, result: Any):
    assert callmethod(object_, method_name) == result


@mark.parametrize(
    'sign, first_operand, second_operand, result',
    (('+', 2, 2, 4), ('/', 16, 4, 4), ('+', (1, 2), (3, 4), (1, 2, 3, 4)))
)
def test_operation_of(sign: str, first_operand: Any, second_operand: Any, result: Any):
    assert operation_of(sign)(first_operand, second_operand) == result


test_action_inserting_in = calling_test_case_of(
    (lambda: binding_by([..., (lambda b: b / 2)])(lambda a: a + 3)(13), 8),
    (lambda: binding_by([(lambda a: a + 3), ...])(lambda b: b / 2)(13), 8),
    (lambda: binding_by([..., ...])(lambda a: a + 2)(12), 16)
)


@mark.parametrize(
    "checker, number, result",
    ((lambda number: number < 10, 3, 3), (lambda number: number < 10, 11, 12))
)
def test_becoming_skipping_on(checker: checker_of[number], number: number, result: Any):
    assert becoming_skipping_on(checker)(lambda number: number + 1)(number) == result


)
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
def test_taken(resource: Any, arguments: Iterable):
    assert taken(resource)(*arguments) == resource


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
            MockAction()
            if number_of_handlers == 1
            else ActionChain((MockAction(), ) * number_of_handlers)
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


test_monadically = calling_test_case_of(
    (lambda: tuple(monadically(lambda _: _)(print)), (print, )),
    (lambda: tuple(monadically(lambda _: _)([print, sum])), (print, sum)),
    (
        lambda: (
            monadically(
                lambda node: lambda resources: (*resources, node(resources[-1]))
            )(
                [lambda a: a + 1, lambda b: b + 2, lambda c: c + 3]
            )
        )([0]),
        (0, 1, 3, 6),
    ),
)


test_inside_context_roots = calling_test_case_of(
    (
        lambda: inside_context_roots(lambda a: a + 10)(ContextRoot(6, None)),
        ContextRoot(16, None),
    ),
    (
        lambda: inside_context_roots([lambda a: a + 1, lambda a: a + 3])(
            ContextRoot(12, None)
        ),
        ContextRoot(16, None),
    ),
)


test_for_context = calling_test_case_of(
    (
        lambda: for_context(lambda c: c + 10)(ContextRoot(None, 32)),
        ContextRoot(None, 42),
    ),
    (
        lambda: for_context([lambda c: c + 5, lambda c: c * 2])(ContextRoot(None, 3)),
        ContextRoot(None, 16),
    )
)


test_in_context = calling_test_case_of(
    (lambda: in_context(4).resource, 4),
    (lambda: in_context(None), ContextRoot(None, None)),
)


test_wrapping_in_context_on = calling_test_case_of(
    (lambda: wrapping_in_context_on(yes)(4), ContextRoot(4, None)),
    (lambda: wrapping_in_context_on(no)(4), 4),
    (
        lambda: wrapping_in_context_on(lambda a: a > 0, context_from=lambda a: a * 2)(4),
        ContextRoot(4, 8),
    ),
    (
        lambda: wrapping_in_context_on(lambda a: a > 0, context_from=lambda a: a * 2)(-4),
        -4,
    ),
)


test_maybe = calling_test_case_of(
    (
        lambda: ContextRoot(14, "Input context") >= maybe([
            lambda a: a + 2, lambda _: bad, lambda _: "last node result"
        ]),
        ContextRoot(16, bad),
    ),
    (
        lambda: ContextRoot(10, "Input context") >= maybe([
            lambda a: a + 3, lambda b: b + 2, lambda c: c + 1
        ]),
        ContextRoot(16, "Input context"),
    ),
)


@mark.parametrize(
    "error_type, input_resource",
    [
        (Exception, str()),
        (TypeError, int()),
        (AttributeError, (1, 2, 3)),
        (AttributeError, (item for item in range(10))),
    ]
)
def test_returning_of_optional_raising_of(
    error_type: Type[Exception],
    input_resource: Any
):
    assert optional_raising_of(error_type)(input_resource) == input_resource



@mark.parametrize(
    "func, input_resources, expected_result, expected_error_type",
    [
        (lambda x: x + 2, (30, ), 32, None),
        (lambda x, y: x + y, (128, 128), 256, None),
        (lambda x: x, (None, ), None, None),
        (lambda x: x / 0, (30, ), None, ZeroDivisionError),
        (lambda x: x.non_existent_attribute, (None, ), None, AttributeError),
        (lambda line: line + 64, ("Some line", ), None, TypeError),
    ]
)
def test_with_error(
    func: Callable,
    input_resources: Iterable,
    expected_result: Any,
    expected_error_type: Optional[Type[Exception]]
):
    result, error = with_error(func)(*input_resources)

    assert result == expected_result

    if expected_error_type is not None:
        assert type(error) is expected_error_type
    else:
        assert error is None


test_until_error_occurs = calling_test_case_of(
    (
        lambda: until_error_occurs(lambda a: a + 3)(ContextRoot(1, "input context")),
        ContextRoot(4, "input context"),
    ),
    (
        lambda: until_error_occurs([lambda a: a + 1, lambda b: b + 2])(
            ContextRoot(1, "input context")
        ),
        ContextRoot(4, "input context"),
    ),
    (
        lambda: (lambda root: (root.resource, type(root.context)))(
            until_error_occurs([
                lambda a: a + 2, lambda b: b / 0, lambda _: "last node result"
            ])(ContextRoot(4, "input context"))
        ),
        (6, ZeroDivisionError),
    ),
)