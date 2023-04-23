from pytest import mark

from pyhandling.tools import *


@mark.parametrize(
    "documentation",
    (
        "Is a handler.", "Is a checker.", "Something.", str(),
        "\n\tIs something.\n\tOr not?", "\tIs a handler.\n\tIs a handler",
    )
)
def test_documenting_by(documentation: str):
    mock = with_attributes()

    documenting_by(documentation)(mock)

    assert '__doc__' in mock.__dict__.keys()
    assert mock.__doc__ == documentation


@mark.parametrize(
    'clock, ticks_to_subtract, result_ticks',
    [
        (Clock(0), 0, 0),
        (Clock(10), 3, 7),
        (Clock(30), -12, 42),
        (Clock(-5), 3, -8),
        (Clock(-40), -8, -32),
    ]
)
def test_clock(clock: Clock, ticks_to_subtract: int, result_ticks: int):
    initual_ticks = clock.initial_ticks_to_disability

    clock.ticks_to_disability -= ticks_to_subtract

    assert clock.initial_ticks_to_disability == initual_ticks
    assert clock.ticks_to_disability == result_ticks


@mark.parametrize(
    'initial_log_number, logging_amount',
    [(0, 0), (4, 0), (4, 8), (0, 8), (32, 16), (128, 128)]
)
def test_number_of_logger_logs(initial_log_number: int, logging_amount: int):
    logger = Logger((str(), ) * initial_log_number)

    for _ in range(logging_amount):
        logger(str())

    assert len(logger.logs) == initial_log_number + logging_amount