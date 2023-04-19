from functools import cached_property, update_wrapper
from inspect import Signature, Parameter, signature
from typing import Callable, Any, _CallableGenericAlias, Optional, Tuple
from operator import is_

from pyhandling.annotations import P, ValueT, ResultT, action_for, one_value_action, dirty, ArgumentsT
from pyhandling.arguments import ArgumentPack
from pyhandling.atoming import atomically
from pyhandling.branching import mergely
from pyhandling.errors import ReturningError
from pyhandling.language import then, by
from pyhandling.partials import will
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.synonyms import returned, on
from pyhandling.tools import documenting_by


__all__ = (
    "returnly",
    "eventually",
    "with_result",
    "dynamically",
    "double",
    "once",
    "taken",
    "yes",
    "no",
    "via_items",
)


@atomically
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


@atomically
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
        **{
            _: maybe_replaced(value)
            for _, value in keyword_argument_placeholders.items()
        },
    )


@atomically
class double(ActionWrapper):
    def __call__(self, value: Any, *result_action_args, **result_action_kwargs) -> Any:
        return self._action(value)(*result_action_args, **result_action_kwargs)

    @property
    def _force_signature(self) -> Signature:
        signature_ = calling_signature_of(self._action)

        return signature_.replace(return_annotation=(
            signature_.return_annotation.__args__[-1]
            if isinstance(signature_, _CallableGenericAlias)
            else Parameter.empty
        ))


@dirty
@atomically
class once:
    _result: Optional[ResultT] = None
    _was_called: bool = False

    def __init__(self, action: Callable[P, ResultT]):
        self._action = action
        self.__signature__ = calling_signature_of(self._action)

    def __repr__(self) -> str:
        return f"once({{}}{self._action})".format(
            f"{self._result} from " if self._was_called else str()
        )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        if self._was_called:
            return self._result

        self._was_called = True
        self._result = self._action(*args, **kwargs)

        self.__signature__ = signature(lambda *_, **__: ...).replace(
            return_annotation=calling_signature_of(self._action).return_annotation
        )

        return self._result


taken: Callable[ValueT, action_for[ValueT]] = documenting_by(
    """Shortcut function for `eventually(returned, ...)`."""
)(
    atomically(will(returned) |then>> eventually)
)


yes: action_for[bool] = documenting_by("""Shortcut for `taken(True)`.""")(taken(True))
no: action_for[bool] = documenting_by("""Shortcut for `taken(False)`.""")(taken(False))


@atomically
class via_items:
    def __init__(self, action: Callable[[ValueT], ResultT] | Callable[[*ArgumentsT], ResultT]):
        self._action = action

    def __repr__(self) -> str:
        return f"({self._action})[{str(calling_signature_of(self._action))[1:-1]}]"

    def __getitem__(self, key: ValueT | Tuple[*ArgumentsT]) -> ResultT:
        arguments = key if isinstance(key, tuple) else (key, )

        return self._action(*arguments)
