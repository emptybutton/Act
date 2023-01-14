from functools import partial
from typing import Type, Iterable, Callable

from pytest import mark, raises

from pyhandling.branchers import ActionChain, eventually
from pyhandling.errors import BadResourceError
from pyhandling.synonyms import raise_
from pyhandling.tools import ArgumentPack
from pyhandling.utils import Logger, showly, documenting_by, as_collection, times, raising, saving_resource_on_error, maybe
from tests.mocks import Counter, MockHandler, MockObject


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
    (
        ((0, 2), )
        + tuple(map(lambda x: (x, x + 1), range(1, 4)))
        + ((31, 32), (63, 64), (127, 128), (515, 516))
    )
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
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    )
)
def test_documenting_by(documentation: str):
    mock = MockObject()

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation


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
def test_as_collection(input_resource: any, result: tuple):
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
def test_error_raising_of_raising(error_type: Type[Exception], error: Exception):
    with raises(error_type):
        raising(error_type)(error)

