from datetime import datetime
from functools import wraps, partial
from math import inf
from typing import Iterable, Tuple, Any, Callable, Type

from pyannotating import many_or_one, Special

from pyhandling.annotations import handler, dirty, handler_of, checker_of, reformer_of, decorator, factory_for, event_for
from pyhandling.branchers import ActionChain, returnly, then, rollbackable, mergely, eventually, on_condition
from pyhandling.binders import close, post_partial
from pyhandling.checkers import Negationer
from pyhandling.errors import BadResourceError
from pyhandling.synonyms import return_, setattr_of, execute_operation, getattr_of, raise_
from pyhandling.tools import Clock, IBadResourceKeeper


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


documenting_by: Callable[[str], dirty[reformer_of[object]]] = (
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


calling_of: decorator = documenting_by(
    """
    Function to represent a proxy of some callable object to call it without
    direct referring to this very object.

    Can be used to later represent the proxy as a method.
    """
)(
    lambda object_: lambda *args, **kwargs: object_(*args, **kwargs)
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


take: Callable[[Any], factory_for[Any]] = documenting_by(
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


maybe: Callable[[many_or_one[Callable]], ActionChain] = documenting_by(
    """
    Function to finish execution of an action chain when a bad resource keeper
    appears in it by returning this same keeper, skipping subsequent action
    chain nodes.
    """
)(
    as_collection
    |then>> close(map)(
        partial(
            on_condition,
            Negationer(post_partial(isinstance, IBadResourceKeeper)),
            else_=return_
        )
    )
    |then>> ActionChain
)


optionally_get_bad_resource_from: handler_of[Special[IBadResourceKeeper]] = documenting_by(
    """
    Function for getting a bad resource from his keeper when this keeper enters.
    Returns the input resource if it is not a bad resource keeper.
    """
)(
    on_condition(
        post_partial(isinstance, IBadResourceKeeper),
        post_partial(getattr_of, 'bad_resource'),
        else_=return_
    )
)