from contextlib import AbstractContextManager
from functools import update_wrapper
from typing import NoReturn, Any, Iterable, Callable, Mapping, Tuple
from inspect import Signature, Parameter

from pyhandling.annotations import P, ValueT, ResultT, ContextT, ErrorHandlingResultT, action_for
from pyhandling.partials import fragmentarily
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "collection_of",
    "with_",
    "with_unpacking",
    "with_keyword_unpacking",
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


@fragmentarily
def with_(context_manager: AbstractContextManager, action: action_for[ResultT]) -> ResultT:
    """Function emulating the `with as` context manager."""

    with context_manager as context:
        return action(context)


class with_unpacking(ActionWrapper):
    """Decorator function to unpack the passed collection into the input action."""

    def __call__(self, arguments: Iterable) -> Any:
        return self._action(*arguments)

    @property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=[Parameter(
            "arguments", Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable
        )])

    def __repr__(self) -> str:
        return _unpacking_repr(self._action)


class with_keyword_unpacking(ActionWrapper):
    """
    Decorator function to unpack the passed mapping object into the input action.
    """

    def __call__(self, arguments: Mapping[str, Any]) -> Any:
        return self._action(**arguments)

    @property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=[Parameter(
            "arguments", Parameter.POSITIONAL_OR_KEYWORD, annotation=Mapping[str, Any]
        )])

    def __repr__(self) -> str:
        return f"*{_unpacking_repr(self._action)}"