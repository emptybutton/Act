from datetime import datetime
from functools import wraps, partial
from math import inf
from typing import Iterable, Tuple, Any, Callable, Type

from pyannotating import many_or_one, Special

from pyhandling.annotations import handler, dirty, handler_of, checker_of, event_for, ResourceT
from pyhandling.branchers import ActionChain, returnly, rollbackable, mergely, eventually, on_condition, chain_constructor
from pyhandling.binders import close, post_partial
from pyhandling.checkers import Negationer
from pyhandling.language import then
from pyhandling.errors import BadResourceError
from pyhandling.shortcuts import take
from pyhandling.synonyms import return_, execute_operation, raise_
from pyhandling.tools import documenting_by, Clock, IBadResourceKeeper


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
    def logs(self) -> Tuple[str]:
        return tuple(self._logs)

    def __call__(self, message: str) -> None:
        self._logs.append(
            message
            if not self.is_date_logging
            else f"[{datetime.now()}] {message}"
        )

        if len(self._logs) > self.maximum_log_count:
            self._logs = self._logs[self.maximum_log_count:]


def showly(
    handler_resource: many_or_one[handler],
    *,
    writer: dirty[handler_of[str]] = print
) -> dirty[ActionChain]:
    """
    Decorator function for visualizing the outcomes of intermediate stages of a
    chain of actions, or simply the input and output results of a regular handler.
    """

    return ActionChain(*map(
        action_binding_of(returnly(str |then>> writer)),
        as_collection(handler_resource)
    ))


def returnly_rollbackable(handler: handler, error_checker: checker_of[Exception]) -> handler:
    """
    Decorator function for a handler that allows it to return a pack of its
    input resource and the error it encountered.
    """

    @wraps(handler)
    def wrapper(resource: Any) -> Any:
        try:
            return handler(resource)
        except Exception as error:
            if error_checker(error):
                return BadResourceError(resource, error)

            raise error

    return wrapper


as_collection: Callable[[many_or_one[ResourceT]], Tuple[ResourceT]]
as_collection = documenting_by(
    """
    Function to convert an input resource into a tuple collection.
    With a non-iterable resource, wraps it in a tuple.
    """
)(
    on_condition(isinstance |by| Iterable, tuple, else_=wrap_in_collection)
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
                close(setattr),
                take("ticks_to_disability"),
                post_partial(getattr, "initial_ticks_to_disability")
            ),
            else_=return_
        ))
        |then>> returnly(
            mergely(
                close(setattr),
                take("ticks_to_disability"),
                (
                    post_partial(getattr, "ticks_to_disability")
                    |then>> post_partial(execute_operation, '-', 1)
                )
            )
        )
        |then>> bool
    )
)


optional_raising_of: Callable[[Type[Exception]], handler_of[Exception]] = documenting_by(
    """
    Function that selectively raises an error (the type of which is the input,
    respectively).

    When called with another resource, returns it.
    """
)(
    close(isinstance, closer=post_partial)
    |then>> post_partial(on_condition, raise_, else_=return_)
)


maybe: chain_constructor = documenting_by(
    """
    Function to finish execution of an action chain when a bad resource keeper
    appears in it by returning this same keeper, skipping subsequent action
    chain nodes.
    """
)(
    as_collection
    |then>> close(map |then>> ActionChain)(
        partial(
            on_condition,
            Negationer(isinstance |by| IBadResourceKeeper),
            else_=return_
        )
    )
)


optional_bad_resource_from: Callable[[IBadResourceKeeper[ResourceT] | ResourceT], ResourceT] 
optional_bad_resource_from = documenting_by(
    """
    Function for getting a bad resource from his keeper when this keeper enters.
    Returns the input resource if it is not a bad resource keeper.
    """
)(
    on_condition(
        isinstance |by| IBadResourceKeeper,
        getattr |by| "bad_resource",
        else_=return_
    )
)


chain_breaking_on_error_that: Callable[[checker_of[Exception]], chain_constructor] = documenting_by(
    """
    Shortcut for maybe which is triggered on an error that satisfies the input
    checker conditions.
    """
)(
    close(returnly_rollbackable, closer=post_partial) |then>> close(map |then>> maybe)
)


bad_resource_wrapping_on: Callable[
    [checker_of[ResourceT]],
    Callable[[ResourceT], BadResourceWrapper[ResourceT] | ResourceT]
]
bad_resource_wrapping_on = documenting_by(
    """
    Function for optional wrapping in BadResourceWrapper under the conditions
    given by the input checker.

    The output function returns the input resource when the checker condition
    is negative.
    """
)(
    close(post_partial(on_condition, BadResourceWrapper, else_=return_))
)
)