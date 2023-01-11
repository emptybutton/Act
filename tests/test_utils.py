from pytest import mark

from pyhandling.branchers import ActionChain
from pyhandling.utils import Logger, showly, documenting_by, as_collection, times
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
