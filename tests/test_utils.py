from typing import Any, Iterable, Type, Callable, Mapping, Optional

from pyannotating import number, many_or_one
from pytest import mark, raises

from pyhandling.annotations import checker_of, event_for
from pyhandling.branchers import ActionChain
from pyhandling.synonyms import with_context_by
from pyhandling.testing import calling_test_case_of
from pyhandling.tools import with_attributes, ArgumentPack, nothing, Logger
from pyhandling.utils import *
from tests.mocks import CustomContext, Counter, MockAction


test_context_oriented = calling_test_case_of(
    (lambda: context_oriented(['val', 'con']), ContextRoot('con', 'val')),
)


test_atomically = calling_test_case_of(
    (lambda: isinstance(atomically(ActionChain([int, str])), ActionChain), False),
    (lambda: len(tuple(ActionChain([atomically(ActionChain([int, str])), print]))), 2),
    (lambda: atomically(lambda a: a)(4), 4)
)


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


test_test_bind = calling_test_case_of(
    (lambda: 4 >= bind(lambda a: a / 2, lambda a: a + 6), 8),
)


@mark.parametrize(
    "value, arguments",
    [
        (256, tuple()),
        (42, (1, 2, 3)),
        (None, (1, 2, 3)),
    ]
)
def test_taken(value: Any, arguments: Iterable):
    assert taken(value)(*arguments) == value


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
        show=lambda _: writing_counter()
    )(None)

    assert writing_counter.counted == number_of_writer_calls


@mark.parametrize(
    "input_value, result",
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
def test_as_collection(input_value: Any, result: tuple):
    assert as_collection(input_value) == result


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


test_monadically = calling_test_case_of(
    (lambda: tuple(monadically(lambda _: _)(print)), (print, )),
    (lambda: tuple(monadically(lambda _: _)([print, sum])), (print, sum)),
    (
        lambda: (
            monadically(
                lambda node: lambda values: (*values, node(values[-1]))
            )(
                [lambda a: a + 1, lambda b: b + 2, lambda c: c + 3]
            )
        )([0]),
        (0, 1, 3, 6),
    ),
)


test_saving_context = calling_test_case_of(
    (
        lambda: saving_context(lambda a: a + 10)(ContextRoot(6, None)),
        ContextRoot(16, None),
    ),
    (
        lambda: saving_context([lambda a: a + 1, lambda a: a + 3])(
            ContextRoot(12, None)
        ),
        ContextRoot(16, None),
    ),
)


test_contextual = calling_test_case_of(
    (lambda: contextual(4).value, 4),
    (lambda: contextual(None), ContextRoot(None, nothing)),
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
    "func, input_values, expected_result, expected_error_type",
    [
        (lambda x: x + 2, (30, ), 32, nothing),
        (lambda x, y: x + y, (128, 128), 256, nothing),
        (lambda x: x, (None, ), None, nothing),
        (lambda x: x / 0, (30, ), nothing, ZeroDivisionError),
        (lambda x: x.non_existent_attribute, (None, ), nothing, AttributeError),
        (lambda line: line + 64, ("Some line", ), nothing, TypeError),
    ]
)
def test_with_error(
    func: Callable,
    input_values: Iterable,
    expected_result: Any,
    expected_error_type: Optional[Type[Exception]]
):
    result, error = with_error(func)(*input_values)

    assert result == expected_result

    if expected_error_type is not nothing:
        assert type(error) is expected_error_type
    else:
        assert error is expected_error_type


test_until_error = calling_test_case_of(
    (
        lambda: until_error(lambda a: a + 3)(ContextRoot(1, "input context")),
        ContextRoot(4, "input context"),
    ),
    (
        lambda: until_error([lambda a: a + 1, lambda b: b + 2])(
            ContextRoot(1, "input context")
        ),
        ContextRoot(4, "input context"),
    ),
    (
        lambda: (lambda root: (root.value, type(root.context)))(
            until_error([
                lambda a: a + 2, lambda b: b / 0, lambda _: "last node result"
            ])(ContextRoot(4, "input context"))
        ),
        (6, ZeroDivisionError),
    ),
)


test_map_ = calling_test_case_of((
    lambda: map_(lambda i: i + 1, range(9)), tuple(range(1, 10))
))


test_filter_ = calling_test_case_of((
    lambda: filter_(lambda i: i % 2 == 0, range(11)), tuple(range(0, 11, 2))
))

test_zip_ = calling_test_case_of((
    lambda: zip_(['a', 'b'], range(10)), (('a', 0), ('b', 1))
))