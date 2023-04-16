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
    "trying_to",
    "with_",
    "with_unpacking",
    "with_keyword_unpacking",
    "collection_of",
    "with_keyword",
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





@fragmentarily
class trying_to:
    """
    Decorator function providing handling of possible errors in an input action.
    """

    def __init__(
        self,
        action: Callable[P, ResultT],
        rollback: Callable[[Exception], ErrorHandlingResultT],
    ):
        self._action = action
        self._rollback = rollback
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.args) -> ResultT | ErrorHandlingResultT:
        try:
            return self._action(*args, **kwargs)
        except Exception as error:
            return self._rollback(error)

    def __repr__(self) -> str:
        return f"trying_to({self._action}, rollback={self._rollback})"

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(
            return_annotation=annotation_sum(
                calling_signature_of(self._action).return_annotation,
                calling_signature_of(self._rollback).return_annotation,
            )
        )


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


def collection_of(*args: ValueT) -> Tuple[ValueT, ...]:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


def with_keyword(keyword: str, value: Any, action: action_for[ResultT]) -> action_for[ResultT]:
    return partial(action, **{keyword: value})
