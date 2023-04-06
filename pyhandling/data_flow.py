from functools import cached_property
from inspect import Signature, Parameter
from typing import Callable, Any

from pyhandling.annotations import P, ValueT, ResultT, action_for, ActionT, handler_of
from pyhandling.arguments import ArgumentPack
from pyhandling.atoming import atomically
from pyhandling.errors import ReturningError
from pyhandling.language import then
from pyhandling.partials import closed
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.synonyms import returned
from pyhandling.tools import documenting_by


__all__ = (
    "returnly",
    "eventually",
    "unpackly",
    "with_result",
    "taken",
    "yes",
    "no",
)


class returnly(ActionWrapper):
    """
    Decorator that causes the input function to return not the result of its
    execution, but some argument that is incoming to it.

    Returns the first argument by default.
    """

    def __call__(self, value: ValueT, *args, **kwargs) -> ValueT:
        self._action(value, *args, **kwargs)

        return value

    @cached_property
    def _force_signature(self) -> Signature:
        parameters = tuple(calling_signature_of(self._action).parameters.values())

        if len(parameters) == 0:
            raise ReturningError("Function must contain at least one parameter")

        return calling_signature_of(self._action).replace(return_annotation=(
            parameters[0].annotation
        ))


class eventually(ActionWrapper):
    """
    Decorator function to call with predefined arguments instead of input ones.
    """

    def __init__(self, action: Callable[P, ResultT], *args: P.args, **kwargs: P.kwargs):
        super().__init__(action)
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *_, **__) -> ResultT:
        return self._action(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self._action}"
            f"{', ' if self._args or self._kwargs else str()}"
            f"{', '.join(map(str, self._args))}"
            f"{', ' if self._args and self._kwargs else str()}"
            f"{', '.join(map(lambda item: str(item[0]) + '=' + str(item[1]), self._kwargs.items()))})"
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action).replace(parameters=(
            Parameter('_', Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter('__', Parameter.VAR_KEYWORD, annotation=Any),
        ))


class unpackly(ActionWrapper):
    """
    Decorator function to unpack the input `ArgumentPack` into the input function.
    """

    def __call__(self, pack: ArgumentPack) -> Any:
        return pack.call(self._action)

    @cached_property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self).replace(
            return_annotation=calling_signature_of(self._action).return_annotation
        )


def with_result(result: ResultT, action: Callable[P, Any]) -> Callable[P, ResultT]:
    """Function to force an input result for an input action."""

    return atomically(action |then>> taken(result))


taken: Callable[[ValueT], action_for[ValueT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    atomically(closed(returned) |then>> eventually)
)

yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))