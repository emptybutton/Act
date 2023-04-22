from contextlib import AbstractContextManager
from functools import update_wrapper, partial
from typing import NoReturn, Any, Iterable, Callable, Mapping, Tuple
from inspect import Signature, Parameter

from pyannotating import Special

from pyhandling.annotations import P, ValueT, ResultT, ContextT, ErrorHandlingResultT, action_for, PositiveConditionResultT, NegativeConditionResultT, reformer_of, checker_of, RightT, LeftT
from pyhandling.atoming import atomically
from pyhandling.partials import fragmentarily
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of, annotation_sum
from pyhandling.tools import to_check, as_action


__all__ = (
    "returned",
    "raise_",
    "assert_",
    "on",
    "repeating",
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


@atomically
class on:
    """
    Function that implements action choosing by condition.

    Creates a action that delegates the call to one other action selected by
    the results of `condition_checker`.

    If the condition is positive, selects `positive_condition_action`, if it is
    negative, selects `else_`.

    With default `else_` takes one value actions.
    """

    def __init__(
        self,
        determinant: Special[Callable[P, bool]],
        right_way: Callable[P, RightT] | RightT,
        /,
        *,
        else_: Callable[P, LeftT] | LeftT = returned
    ):
        self._condition_checker = to_check(determinant)
        self._right_action = as_action(right_way)
        self._left_action = as_action(else_)

        self.__signature__ = self.__get_signature()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> RightT | LeftT:
        return (
            self._right_action
            if self._condition_checker(*args, **kwargs)
            else self._left_action
        )(*args, **kwargs)

    def __repr__(self) -> str:
        return (
            f"({self._right_action} on {self._condition_checker} "
            f"else {self._left_action})"
        )

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._right_action).replace(
            return_annotation=annotation_sum(
                calling_signature_of(self._right_action).return_annotation,
                calling_signature_of(self._left_action).return_annotation,
            )
        )


@atomically
class repeating:
    """
    Function to call an input action multiple times.

    Initially calls an input action from an input value, after repeating the
    result of an input action itself.
    """

    def __init__(self, action: reformer_of[ValueT], while_: checker_of[ValueT]):
        self._action = action
        self._is_valid_to_repeat = while_

        self.__signature__ = self.__get_signature()

    def __call__(self, value: ValueT) -> ValueT:
        while self._is_valid_to_repeat(value):
            value = self._action(value)
        
        return value

    def __repr__(self) -> str:
        return f"({self._action} while {self._is_valid_to_repeat})"

    def __get_signature(self) -> Signature:
        return calling_signature_of(self._action)


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


@atomically
class with_unpacking(ActionWrapper):
    """Decorator function to unpack the passed collection into the input action."""

    def __call__(self, arguments: Iterable) -> Any:
        return self._action(*arguments)

    @property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=[Parameter(
            "arguments", Parameter.POSITIONAL_OR_KEYWORD, annotation=Iterable
        )])


@atomically
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


def collection_of(*args: ValueT) -> Tuple[ValueT, ...]:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


def with_keyword(keyword: str, value: Any, action: action_for[ResultT]) -> action_for[ResultT]:
    return partial(action, **{keyword: value})
