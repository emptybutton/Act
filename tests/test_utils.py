from typing import Any, Iterable, Type, Callable, Optional

from pytest import mark

from pyhandling.flags import nothing
from pyhandling.utils import *


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
