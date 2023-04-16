from functools import cached_property
from inspect import Signature, Parameter, _empty
from typing import Callable, Any, _CallableGenericAlias
from operator import is_

from pyhandling.annotations import P, ValueT, ResultT, action_for, one_value_action
from pyhandling.arguments import ArgumentPack
from pyhandling.atoming import atomically
from pyhandling.branching import mergely, on
from pyhandling.errors import ReturningError
from pyhandling.language import then, by
from pyhandling.partials import will
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.structure_management import table_value_map
from pyhandling.synonyms import returned
from pyhandling.tools import documenting_by


__all__ = (
    "returnly",
    "eventually",
    "with_result",
    "dynamically",
    "combinatly",
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


def with_result(result: ResultT, action: Callable[P, Any]) -> Callable[P, ResultT]:
    """Function to force an input result for an input action."""

    return atomically(action |then>> taken(result))


def dynamically(
    action: action_for[ResultT],
    *argument_placeholders: one_value_action | Ellipsis,
    **keyword_argument_placeholders: one_value_action  | Ellipsis,
) -> action_for[ResultT]:
    """Function to dynamically determine arguments for an input action."""

    maybe_replaced = on(is_ |by| Ellipsis, taken(returned))

    return mergely(
        taken(action),
        *map(maybe_replaced, argument_placeholders),
        **table_value_map(maybe_replaced, keyword_argument_placeholders),
    )


class combinatly(ActionWrapper):
    def __call__(self, value: Any, *result_action_args, **result_action_kwargs) -> Any:
        return self._action(value)(*result_action_args, **result_action_kwargs)

    @property
    def _force_signature(self) -> Signature:
        signature_ = calling_signature_of(self._action)

        return signature_.replace(return_annotation=(
            signature_.return_annotation.__args__[-1]
            if isinstance(signature_, _CallableGenericAlias)
            else _empty
        ))


taken: Callable[ValueT, action_for[ValueT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    atomically(will(returned) |then>> eventually)
)


yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))