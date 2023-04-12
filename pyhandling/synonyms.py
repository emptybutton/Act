from contextlib import AbstractContextManager
from functools import update_wrapper
from typing import NoReturn, Any, Iterable, Callable, Mapping, Tuple
from inspect import Signature, Parameter

from pyhandling.annotations import P, ValueT, ResultT, ContextT
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "collection_of",
    "with_unpacking",
    "with_keyword_unpacking",
    "to_context_manager",
    "with_context_manager_by",
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

        return calling_signature_of(self._action).replace(parameters=[Parameter(
            "context_manager",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=AbstractContextManager[input_annotation_of_action]
        )])


class with_context_manager_by:
    """Function to perform an input action in a specific context."""

    def __init__(
        self,
        get_context: Callable[P, AbstractContextManager[ContextT]],
        action: Callable[P, ResultT],
    ):
        self._get_context = get_context
        self._action = action

        update_wrapper(self, self._action)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        with get_context(*args, **kwargs):
            return action(*args, **kwargs)

    def __repr__(self) -> str:
        return f"with_context_manager_by({self._get_context}, {self._action})"


def _unpacking_repr(action: Callable) -> str:
    return "*{sep}{action}".format(
        sep=(
            '\''
            if isinstance(self._action, with_unpacking | with_keyword_unpacking)
            else str()
        ),
        action=action,
    )
