from contextlib import AbstractContextManager
from functools import wraps, partial
from typing import NoReturn, Any, Iterable, Callable, Mapping, Tuple
from inspect import Signature, Parameter

from pyhandling.annotations import P, ValueT, action_for, ResultT, KeyT, event_for, ContextT
from pyhandling.tools import ActionWrapper, calling_signature_of


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "collection_of",
    "with_unpacking",
    "with_keyword_unpacking",
    "to_context_manager",
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


class to_context_manager(ActionWrapper):
    """Function emulating the `with as` context manager."""

    def __call__(self, context_manager: AbstractContextManager) -> Any:
        with context_manager as context:
            return self._action(context)

    @property
    def _force_signature(self) -> Signature:
        input_annotation_of_action = tuple(
            calling_signature_of(self._action).parameters.values()
        )[0].annotation

        return calling_signature_of(self._action).replace(parameters=Parameter(
            "context_manager",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=AbstractContextManager[input_annotation_of_action]
        ))


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