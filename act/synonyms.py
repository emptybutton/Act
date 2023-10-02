from contextlib import AbstractContextManager
from typing import NoReturn, Any, Callable, Mapping, Tuple
from inspect import Signature, Parameter

from pyannotating import Special

from act.annotations import Pm, V, R, E, reformer_of, L
from act.atomization import fun
from act.partiality import partial, partially
from act.representations import code_like_repr_of
from act.signatures import Decorator, call_signature_of, annotation_sum
from act.tools import to_check, as_action, documenting_by, _get


__all__ = (
    "raise_",
    "assert_",
    "on",
    "while_",
    "times",
    "try_",
    "with_",
    "keyword_unpackly",
    "tuple_of",
    "in_tuple",
    "with_keyword",
)


def raise_(error: Exception) -> NoReturn:
    """Function for functional use of `raise` statement."""

    raise error


def assert_(value: Any) -> None:
    """Function for functional use of `assert` statement."""

    assert value


@partially
class on:
    """
    Function that implements action choosing by condition.

    Creates a action that delegates the call to one other action selected by an
    input determinant.

    With non-callable determinant, compares an input value with this
    determinant.

    With non-callable implementations, returns those non-callable values.

    With default `else_` takes one value actions.
    """

    def __init__(
        self,
        determinant: Special[Callable[Pm, bool]],
        right_way: Callable[Pm, R] | R,
        /,
        else_: Callable[Pm, L] | L = _get
    ):
        self._condition_checker = to_check(determinant)
        self._right_action = as_action(right_way)
        self._left_action = as_action(else_)

        self.__signature__ = self.__get_signature()

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R | L:
        return (
            self._right_action
            if self._condition_checker(*args, **kwargs)
            else self._left_action
        )(*args, **kwargs)

    def __repr__(self) -> str:
        return "({} on {} else {})".format(
            code_like_repr_of(self._right_action),
            code_like_repr_of(self._condition_checker),
            code_like_repr_of(self._left_action),
        )

    def __get_signature(self) -> Signature:
        return call_signature_of(self._right_action).replace(
            return_annotation=annotation_sum(
                call_signature_of(self._right_action).return_annotation,
                call_signature_of(self._left_action).return_annotation,
            )
        )


@partially
class while_:
    """
    Function to call an input action multiple times.

    Initially calls an input action from an input value, after repeating the
    result of an input action itself.

    Repeats until an input determinant returns `False`.

    With non-callable determinant, compares an input value with this
    determinant.
    """

    def __init__(
        self,
        is_valid_to_repeat: Special[Callable[V, bool]],
        action: reformer_of[V],
    ):
        self._is_valid_to_repeat = to_check(is_valid_to_repeat)
        self._action = action

        self.__signature__ = self.__get_signature()

    def __call__(self, value: V) -> V:
        while self._is_valid_to_repeat(value):
            value = self._action(value)

        return value

    def __repr__(self) -> str:
        return "(while {}: {})".format(
            code_like_repr_of(self._is_valid_to_repeat),
            code_like_repr_of(self._action),
        )

    def __get_signature(self) -> Signature:
        return call_signature_of(self._action)


@partially
def times(number: int, action: Callable[V, V], value: V) -> V:
    for _ in range(number):
        value = action(value)

    return value


@partially
class try_:
    """
    Decorator function providing handling of possible errors in an input action.

    On error, an input rollbacker is first called with the same arguments that
    were passed to an input action, then an occured error.
    """

    def __init__(
        self,
        action: Callable[Pm, R],
        rollback: Callable[Pm, Callable[[Exception], E]],
    ):
        self._action = action
        self._rollback = rollback
        self.__signature__ = self.__get_signature()

    def __call__(self, *args: Pm.args, **kwargs: Pm.args) -> R | E:
        try:
            return self._action(*args, **kwargs)
        except Exception as error:
            return self._rollback(*args, **kwargs)(error)

    def __repr__(self) -> str:
        return "(try {} except {})".format(
            code_like_repr_of(self._action),
            code_like_repr_of(self._rollback),
        )

    def __get_signature(self) -> Signature:
        return call_signature_of(self._action).replace(
            return_annotation=annotation_sum(
                call_signature_of(self._action).return_annotation,
                call_signature_of(self._rollback).return_annotation,
            )
        )


@partially
def with_(context_manager: AbstractContextManager, action: Callable[..., R]) -> R:
    """Function emulating the `with as` context manager."""

    with context_manager as context:
        return action(context)


@documenting_by(
    """
    Decorator function to unpack the passed mapping object into the input action.
    """
)
@fun
class keyword_unpackly(Decorator):
    def __call__(self, arguments: Mapping[str, Any]) -> Any:
        return self._action(**arguments)

    @property
    def _force_signature(self) -> Signature:
        return call_signature_of(self._action).replace(parameters=[Parameter(
            "arguments",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=Mapping[str, Any],
        )])


def tuple_of(*args: V) -> Tuple[V, ...]:
    """Function to create a `tuple` from unlimited input arguments."""

    return args


def in_tuple(value: V) -> Tuple[V]:
    """Function to create a `tuple` with an input value."""

    return (value, )


def with_keyword(
    keyword: str,
    value: Any,
    action: Callable[..., R],
) -> Callable[..., R]:
    """Function for atomic partial application with keyword argument."""

    return partial(action, **{keyword: value})
