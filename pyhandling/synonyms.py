from functools import wraps, partial
from typing import NoReturn, Any, Iterable, Callable, Mapping

from pyhandling.annotations import ValueT, action_for, ResultT, KeyT, event_for, ContextT, ArgumentsT
from pyhandling.protocols import ItemGetter, ItemSetter, ContextManager


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "collection_of",
    "with_positional_unpacking",
    "with_keyword_unpacking",
    "to_context",
    "with_context_by",
)


def returned(value: ValueT) -> ValueT:
    """
    Function representing the absence of an action.
    Returns the value passed to it back.
    """

    return value


def raise_(error: Exception) -> NoReturn:
    """Function for functional use of `raise` statement."""

    raise error


def assert_(value: Any) -> None:
    """Function for functional use of `assert` statement."""

    assert value


def collection_of(*args) -> tuple:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


def with_positional_unpacking(func: action_for[ResultT]) -> Callable[[Iterable], ResultT]:
    """Decorator function to unpack the passed collection into the input action."""

    return wraps(func)(lambda arguments: func(*arguments))


def with_keyword_unpacking(func: action_for[ResultT]) -> Callable[[Mapping[str, Any]], ResultT]:
    """
    Decorator function to unpack the passed mapping object into the input action.
    """

    return wraps(func)(lambda arguments: func(**arguments))


def to_context(action: Callable[[ContextT], ResultT]) -> Callable[[ContextManager[ContextT]], ResultT]:
    """Function emulating the `with as` context manager."""

    @wraps(action)
    def contextual_action(context_manager: ContextManager[ContextT]) -> ResultT:
        with context_manager as context:
            return action(context)

    return contextual_action


def with_context_by(
    get_context: Callable[[*ArgumentsT], ContextManager[ContextT]],
    action: Callable[[*ArgumentsT], ResultT]
) -> Callable[[*ArgumentsT], ResultT]:
    """Function to perform an input action in a specific context."""

    @wraps(action)
    def contextual_action(*args, **kwargs) -> Any:
        with get_context(*args, **kwargs):
            return action(*args, **kwargs)


    return contextual_action