from datetime import datetime
from functools import partial
from math import inf
from operator import eq
from typing import Iterable, Tuple, NoReturn

from pyhandling.annotations import (
    event_for, V, dirty, reformer_of, checker_of, ActionT, action_for
)
from pyhandling.errors import InvalidInitializationError
from pyhandling.immutability import property_to


__all__ = (
    "Clock",
    "Logger",
    "NotInitializable",
    "with_attributes",
    "documenting_by",
    "to_check",
    "as_action",
)


class Clock:
    """
    Atomic class for saving state.

    Has a number of ticks that determines its state.
    When ticks expire, it becomes `False` and may leave negative ticks.

    Keeps the original input ticks.
    """

    initial_ticks_to_disability = property_to("_initial_ticks_to_disability")

    def __init__(self, ticks_to_disability: int):
        self.ticks_to_disability = ticks_to_disability
        self._initial_ticks_to_disability = ticks_to_disability

    def __repr__(self) -> str:
        return (
            f"{'in' if not self else str()}valid {self.__class__.__name__}"
            f"({self.ticks_to_disability})"
        )

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
    get_object: event_for[V] = type(
        "_AttributeStorage",
        tuple(),
        {
            '__doc__': (
                """
                Class used as a standard object factory for subsequent stuffing
                with attributes in `with_attributes`
                """
            ),
            '__repr__': lambda object_: "<{}>".format(', '.join(
                f"{name}={value}" for name, value in object_.__dict__.items()
            )),
        }
    ),
    **attributes,
) -> V:
    """
    Function to create an object with attributes from keyword arguments.
    Sets attributes manually.
    """

    attribute_keeper = get_object()
    attribute_keeper.__dict__ = attributes

    return attribute_keeper


def documenting_by(documentation: str) -> dirty[reformer_of[V]]:
    """
    Function of getting other function that getting value with the input
    documentation from this first function.
    """

    def document(object_: V) -> V:
        """
        Function created with `documenting_by` function that sets the __doc__
        attribute and returns the input object.
        """

        object_.__doc__ = documentation
        return object_

    return document


def to_check(determinant: checker_of[V] | V) -> checker_of[V]:
    return determinant if callable(determinant) else partial(eq, determinant)


def as_action(value: ActionT | V) -> ActionT | action_for[V]:
    return value if callable(value) else lambda *_, **__: value
