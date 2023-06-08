from datetime import datetime
from math import inf
from typing import Iterable, Tuple, Generator, Optional

from pyhandling.annotations import dirty, V
from pyhandling.atoming import atomically
from pyhandling.branching import binding_by, then
from pyhandling.data_flow import eventually, by, to
from pyhandling.error_flow import catching
from pyhandling.partials import will
from pyhandling.synonyms import trying_to
from pyhandling.tools import documenting_by, LeftCallable


__all__ = (
    "Logger",
    "iteration_over",
    "times",
)


class Logger:
    """
    Class for logging any messages.

    Stores messages via the input value of its call.

    Has the ability to clear logs when their limit is reached, controlled by the
    `maximum_log_count` attribute and the keyword argument.

    Able to save the date of logging in the logs. Controlled by `is_date_logging`
    attribute and keyword argument.
    """

    def __init__(
        self,
        logs: Iterable[str] = tuple(),
        *,
        maximum_log_count: int | float = inf,
        is_date_logging: bool = False
    ):
        self._logs = list()
        self.maximum_log_count = maximum_log_count
        self.is_date_logging = is_date_logging

        for log in logs:
            self(log)

    @property
    def logs(self) -> Tuple[str, ...]:
        return tuple(self._logs)

    def __call__(self, message: str) -> None:
        self._logs.append(
            message
            if not self.is_date_logging
            else f"[{datetime.now()}] {message}"
        )

        if len(self._logs) > self.maximum_log_count:
            self._logs = self._logs[self.maximum_log_count:]


iteration_over: LeftCallable[Iterable[V], LeftCallable[..., Optional[V]]]
iteration_over = documenting_by(
    """
    Decorator to atomically iterate over input generator via call.
    When `StopIteration` occurs, returns it.
    """
)(
    atomically(iter |then>> will(eventually)(
        next |then>> (trying_to |by| to(catching(StopIteration, to(None))))
    ))
)


@dirty
@documenting_by(
    """
    Function for a function returning `True` an input number of times, then
    `False` once, and again.

    Return function ignores its input arguments.
    """
)
@binding_by(... |then>> iteration_over)
def times(max_steps: int, /) -> Generator[bool, None, None]:
    steps = max_steps

    while True:
        yield steps > 0
        steps -= 1

        if steps < 0:
            steps = max_steps
