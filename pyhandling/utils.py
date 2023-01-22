from datetime import datetime
from functools import wraps, partial
from math import inf
from typing import Callable, Iterable, Any, Type

from pyhandling.annotations import handler, dirty, handler_of, event_for, factory_of
from pyhandling.branchers import ActionChain, returnly, then, mergely, eventually, on_condition, rollbackable
from pyhandling.binders import close, post_partial
from pyhandling.errors import BadResourceError
from pyhandling.synonyms import setattr_of, return_, execute_operation, getattr_of, raise_, getitem_of, call
from pyhandling.tools import Clock, as_argument_pack, ArgumentKey, DelegatingProperty


class Logger:
    """
    Class for logging any messages.

    Stores messages via the input value of its call.

    Has the ability to clear logs when their limit is reached, controlled by the
    maximum_log_count attribute and the keyword argument.

    Able to save the date of logging in the logs. Controlled by is_date_logging
    attribute and keyword argument.

    Suggested to be used with showly function.
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
    def logs(self) -> tuple[str]:
        return tuple(self._logs)

    def __call__(self, message: str) -> None:
        self._logs.append(
            message
            if not self.is_date_logging
            else f'[{datetime.now()}] {message}'
        )

        if len(self._logs) > self.maximum_log_count:
            self._logs = self._logs[self.maximum_log_count:]


def showly(handler: handler, *, writer: dirty[handler_of[str]] = print) -> dirty[ActionChain]:
    """
    Decorator function for visualizing the outcomes of intermediate stages of a
    chain of actions, or simply the input and output results of a regular handler.
    """

    writer = returnly(str |then>> writer)

    return (
        handler.clone_with_intermediate(writer, is_on_input=True, is_on_output=True)
        if isinstance(handler, ActionChain)
        else wraps(handler)(writer |then>> handler |then>> writer)
    )


documenting_by: Callable[[str], dirty[Callable[[object], object]]] = (
    mergely(
        eventually(partial(return_, close(returnly(setattr_of)))),
        attribute_name=eventually(partial(return_, '__doc__')),
        attribute_value=return_
    )
)
documenting_by.__doc__ = (
    """
    Function of getting other function that getting resource with the input 
    documentation from this first function.
    """
)


as_collection: Callable[[Any], tuple] = documenting_by(
    """
    Function to convert an input resource into a tuple collection.
    With a non-iterable resource, wraps it in a tuple.
    """
)(
    on_condition(
        post_partial(isinstance, Iterable),
        tuple,
        else_=lambda resource: (resource, )
    )
)


take: Callable[[Any], factory_of[Any]] = documenting_by(
    """
    Shortcut function equivalent to eventually(partial(return_, input_resource).
    """
)(
    close(return_) |then>> eventually
)


times: Callable[[int], dirty[event_for[bool]]] = documenting_by(
    """
    Function to create a function that will return True the input value (for
    this function) number of times, then False once after the input count has
    passed, True again n times, and so on.
    """
)(
    post_partial(execute_operation, '+', 1)
    |then>> Clock
    |then>> close(
        returnly(on_condition(
            lambda clock: not clock,
            mergely(
                close(setattr_of),
                take('ticks_to_disability'),
                post_partial(getattr_of, 'initial_ticks_to_disability')
            ),
            else_=return_
        ))
        |then>> returnly(
            mergely(
                close(setattr_of),
                take('ticks_to_disability'),
                (
                    post_partial(getattr_of, 'ticks_to_disability')
                    |then>> post_partial(execute_operation, '-', 1)
                )
            )
        )
        |then>> bool
    )
)


raising: Callable[[Type[Exception]], handler_of[Exception]] = documenting_by(
    """
    Function that selectively raises an error (the type of which is the input,
    respectively).

    When called with another resource, returns it.
    """
)(
    close(isinstance, closer=post_partial)
    |then>> post_partial(on_condition, raise_, else_=return_)
)


saving_resource_on_error: Callable[[handler], handler] = documenting_by(
    """
    Decorator function that formats occurring errors to BadResourceError, saving
    information about the input resource and the error itself accordingly.
    """
)(
    close(
        as_argument_pack
        |then>> mergely(
            post_partial(getitem_of, ArgumentKey(1)) |then>> close(call, closer=post_partial),
            mergely(
                take(rollbackable),
                post_partial(getitem_of, ArgumentKey(0)),
                (
                    post_partial(getitem_of, ArgumentKey(1))
                    |then>> close(BadResourceError |then>> raise_)
                )
            )
        )
    )
)


maybe: Callable[[Iterable[Callable] | Callable], ActionChain] = documenting_by(
    """
    Function that decorates the input action chain or just a collection of
    handlers (ater on, the action chain anyway) and allowing to break this very
    action chain in case of an error, by returning a valid result of the last of
    the fully completed node.
    """
)(
    as_collection
    |then>> partial(map, saving_resource_on_error)
    |then>> ActionChain
    |then>> post_partial(
        rollbackable,
        on_condition(
            post_partial(isinstance, BadResourceError),
            post_partial(getattr_of, 'resource'),
            else_=raise_
        )
    )
)