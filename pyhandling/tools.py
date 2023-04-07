from datetime import datetime
from math import inf
from typing import Iterable, Tuple, NoReturn

from pyhandling.annotations import event_for, ObjectT, dirty, reformer_of
from pyhandling.immutability import property_of
from pyhandling.errors import InvalidInitializationError


__all__ = (
    "Clock",
    "Logger",
    "NotInitializable",
    "with_attributes",
    "documenting_by",
)


class Clock:
    """
    Atomic class for saving state.

    Has a number of ticks that determines its state.
    When ticks expire, it becomes `False` and may leave negative ticks.

    Keeps the original input ticks.
    """

    initial_ticks_to_disability = property_of("_initial_ticks_to_disability")

    def __init__(self, ticks_to_disability: int):
        self.ticks_to_disability = self._initial_ticks_to_disability = ticks_to_disability

    def __repr__(self) -> str:
        return f"{'in' if not self else str()}valid {self.__class__.__name__}({self.ticks_to_disability})"

    def __bool__(self) -> bool:
        return self.ticks_to_disability > 0


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


class NotInitializable:
    def __init__(self, *args, **kwargs) -> NoReturn:
        raise InvalidInitializationError(
            f"\"{type(self).__name__}\" type object cannot be initialized"
        )


def with_attributes(
    get_object: event_for[ObjectT] = type(
        "_with_attributes__default_object_type",
        tuple(),
        {'__doc__': (
            """
            Class used as a standard object factory for subsequent stuffing with
            attributes in `with_attributes`
            """
        )}
    ),
    **attributes,
) -> ObjectT:
    """
    Function to create an object with attributes from keyword arguments.
    Sets attributes manually.
    """

    attribute_keeper = get_object()
    attribute_keeper.__dict__ = attributes

    return attribute_keeper


def documenting_by(documentation: str) -> dirty[reformer_of[ObjectT]]:
    """
    Function of getting other function that getting value with the input 
    documentation from this first function.
    """

    def document(object_: ObjectT) -> ObjectT:
        """
        Function created with `documenting_by` function that sets the __doc__
        attribute and returns the input object.
        """

        object_.__doc__ = documentation
        return object_

    return document
