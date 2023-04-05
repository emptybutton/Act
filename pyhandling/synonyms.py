from contextlib import AbstractContextManager
from functools import wraps, partial
from typing import NoReturn, Any, Iterable, Callable, Mapping, Tuple

from pyhandling.annotations import P, ValueT, action_for, ResultT, KeyT, event_for, ContextT


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "collection_of",
    "with_unpacking",
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


def collection_of(*args: ValueT) -> Tuple[ValueT, ...]:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


class with_unpacking(ActionWrapper):
    """Decorator function to unpack the passed collection into the input action."""

    def __call__(self, arguments: Iterable) -> Any:
        return self._action(*arguments)

    @property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=Parameter(
            "arguments", Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable
        ))

def with_keyword_unpacking(func: action_for[ResultT]) -> Callable[[Mapping[str, Any]], ResultT]:
    def __repr__(self) -> str:
        return _unpacking_repr(self._action)


    """
    Decorator function to unpack the passed mapping object into the input action.
    """

    return wraps(func)(lambda arguments: func(**arguments))


def to_context(
    action: Callable[[ContextT], ResultT]
) -> Callable[[AbstractContextManager[ContextT]], ResultT]:
    """Function emulating the `with as` context manager."""

    @wraps(action)
    def contextual_action(context_manager: AbstractContextManager[ContextT]) -> ResultT:
        with context_manager as context:
            return action(context)

    return contextual_action


def with_context_by(
    get_context: Callable[P, AbstractContextManager[ContextT]],
    action: Callable[P, ResultT]
) -> Callable[P, ResultT]:
    """Function to perform an input action in a specific context."""

    @wraps(action)
    def contextual_action(*args: P.args, **kwargs: P.kwargs) -> ResultT:
        with get_context(*args, **kwargs):
            return action(*args, **kwargs)


    return contextual_action