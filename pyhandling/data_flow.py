from abc import ABC, abstractmethod
from functools import cached_property, partial
from inspect import Signature, Parameter, signature
from operator import not_
from typing import (
    Callable, Any, _CallableGenericAlias, Optional, Tuple, Self, Iterable
)

from pyhandling.annotations import (
    Pm, V, R, action_for, dirty, ArgumentsT, reformer_of
)
from pyhandling.atoming import atomically
from pyhandling.branching import mergely, bind, then
from pyhandling.errors import ReturningError
from pyhandling.partials import will, rpartial, flipped
from pyhandling.signature_assignmenting import Decorator, call_signature_of
from pyhandling.synonyms import returned, on
from pyhandling.tools import documenting_by, LeftCallable, action_repr_of


__all__ = (
    "returnly",
    "eventually",
    "with_result",
    "to_left",
    "to_right",
    "dynamically",
    "double",
    "once",
    "via_items",
    "PartialApplicationInfix",
    "to",
    "by",
    "shown",
    "yes",
    "no",
    "anything",
)


@atomically
class returnly(Decorator):
    """
    Decorator that causes an input action to return first argument that is
    incoming to it.
    """

    def __call__(self, value: V, *args, **kwargs) -> V:
        self._action(value, *args, **kwargs)

        return value

    @cached_property
    def _force_signature(self) -> Signature:
        parameters = tuple(call_signature_of(self._action).parameters.values())

        if len(parameters) == 0:
            raise ReturningError("Function must contain at least one parameter")

        return call_signature_of(self._action).replace(return_annotation=(
            parameters[0].annotation
        ))


@atomically
class eventually(Decorator):
    """
    Decorator function to call with predefined arguments instead of input ones.
    """

    def __init__(
        self,
        action: Callable[Pm, R],
        *args: Pm.args,
        **kwargs: Pm.kwargs,
    ):
        super().__init__(action)
        self._args = args
        self._kwargs = kwargs

    def __call__(self, *_, **__) -> R:
        return self._action(*self._args, **self._kwargs)

    def __repr__(self) -> str:
        formatted_kwargs = ', '.join(map(
            lambda item: action_repr_of(item[0]) + '=' + action_repr_of(item[1]),
            self._kwargs.items()
        ))

        return (
            f"{type(self).__name__}({self._action}"
            f"{', ' if self._args or self._kwargs else str()}"
            f"{', '.join(map(action_repr_of, self._args))}"
            f"{', ' if self._args and self._kwargs else str()}"
            f"{formatted_kwargs})"
        )

    @cached_property
    def _force_signature(self) -> Signature:
        return call_signature_of(self._action).replace(parameters=(
            Parameter('_', Parameter.VAR_POSITIONAL, annotation=Any),
            Parameter('__', Parameter.VAR_KEYWORD, annotation=Any),
        ))


def with_result(result: R, action: Callable[Pm, Any]) -> Callable[Pm, R]:
    """Function to force an input result for an input action."""

    return bind(action, to(result))


@atomically
class to_left(Decorator):
    """Decorator to ignore all arguments except the first."""

    def __call__(self, left_: V, *_, **__) -> R:
        return self._action(left_)

    @property
    def _force_signature(self) -> Signature:
        signature_ = call_signature_of(self._action)

        return signature_.replace(parameters=[
            tuple(signature_.parameters.values())[0],
            *call_signature_of(lambda *_, **__: ...).parameters.values(),
        ])


to_right: LeftCallable[Callable[V, R], Callable[[..., V], R]]
to_right = documenting_by(
    """Decorator to ignore all arguments except the last."""
)(
    atomically(to_left |then>> flipped)
)


def dynamically(
    action: Callable[Pm, R],
    *argument_placeholders: Callable[Pm, Any],
    **keyword_argument_placeholders: Callable[Pm, Any],
) -> action_for[R]:
    """
    Function to dynamically determine arguments for an input action.

    Evaluates arguments from old arguments to places equal to the places of
    actions by which they are evaluated (including keywords).

    When passing values as argument evaluators, final computed values of such
    evaluators will be these values.
    """

    replaced = on(bind(callable, not_), to)

    return mergely(
        to(action),
        *map(replaced, argument_placeholders),
        **{
            _: replaced(value)
            for _, value in keyword_argument_placeholders.items()
        },
    )


@atomically
class double(Decorator):
    """
    Decorator to double call an input action.

    The first call is the call of an input action itself with the first
    positional argument, and the second is the call of its resulting action
    with the remaining arguments.
    """

    def __call__(
        self,
        value: Any,
        *result_action_args,
        **result_action_kwargs,
    ) -> Any:
        return self._action(value)(*result_action_args, **result_action_kwargs)

    @property
    def _force_signature(self) -> Signature:
        signature_ = call_signature_of(self._action)

        return signature_.replace(return_annotation=(
            signature_.return_annotation.__args__[-1]
            if isinstance(signature_, _CallableGenericAlias)
            else Parameter.empty
        ))


@dirty
@atomically
class once:
    """
    Decorator for lazy action call.

    Calls an input action once, then returns a value of that first call,
    ignoring input arguments.
    """

    _result: Optional[R] = None
    _was_called: bool = False

    def __init__(self, action: Callable[Pm, R]):
        self._action = action
        self.__signature__ = call_signature_of(self._action)

    def __repr__(self) -> str:
        return f"once({{}}{action_repr_of(self._action)})".format(
            f"{action_repr_of(self._result)} from "
            if self._was_called
            else str()
        )

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        if self._was_called:
            return self._result

        self._was_called = True
        self._result = self._action(*args, **kwargs)

        self.__signature__ = signature(lambda *_, **__: ...).replace(
            return_annotation=call_signature_of(self._action).return_annotation
        )

        return self._result


@atomically
class via_items:
    """
    Decorator for an action, allowing it to be called via `[]` call rather than
    `()`.
    """

    def __init__(
        self,
        action: Callable[[V], R] | Callable[[*ArgumentsT], R],
    ):
        self._action = action

    def __repr__(self) -> str:
        return "({})[{}]".format(
            action_repr_of(self._action),
            str(call_signature_of(self._action))[1:-1],
        )

    def __getitem__(self, key: V | Tuple[*ArgumentsT]) -> R:
        arguments = key if isinstance(key, tuple) else (key, )

        return self._action(*arguments)


class PartialApplicationInfix(ABC):
    """
    Infix class for action partial application.

    Used in the form `action |instance| argument` or `action |instance* arguments`
    if you want to unpack the arguments.
    """

    @abstractmethod
    def __or__(self, argument: Any) -> Callable:
        ...

    @abstractmethod
    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        ...

    @abstractmethod
    def __mul__(self, arguments: Iterable) -> Callable:
        ...


class _CustomPartialApplicationInfix(PartialApplicationInfix):
    """Named implementation of `PartialApplicationInfix` from input values."""

    def __init__(
        self,
        transform: Callable[[Callable, *ArgumentsT], Callable],
        *,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[*ArgumentsT]] = None,
        name: Optional[str] = None,
    ):
        self._transform = transform
        self._action_to_transform = action_to_transform
        self._arguments = arguments
        self._name = "<PartialApplicationInfix>" if name is None else name

    def __repr__(self) -> str:
        return self._name

    def __or__(self, argument: Any) -> Callable:
        return self._transform(self._action_to_transform, argument)

    def __ror__(self, action_to_transform: Callable) -> Self | Callable:
        return (
            type(self)(
                self._transform,
                action_to_transform=action_to_transform,
                name=self._name,
            )
            if self._arguments is None
            else self._transform(action_to_transform, *self._arguments)
        )

    def __mul__(self, arguments: Iterable) -> Callable:
        return type(self)(self._transform, arguments=arguments, name=self._name)


class _CallableCustomPartialApplicationInfix(_CustomPartialApplicationInfix):
    """
    `_CustomPartialApplicationInfix` delegating its call to the input action.
    """

    def __init__(
        self,
        transform: Callable[[Callable, V], Callable],
        *,
        action_to_call: Callable[Pm, R] = returned,
        action_to_transform: Optional[Callable] = None,
        arguments: Optional[Iterable[V]] = None,
        name: Optional[str] = None
    ):
        super().__init__(
            transform,
            action_to_transform=action_to_transform,
            arguments=arguments,
            name=name,
        )
        self._action_to_call = action_to_call

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._action_to_call(*args, **kwargs)


to = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `partial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.

    When called, creates a function that returns an input value, ignoring input
    arguments.
    """
)(
    _CallableCustomPartialApplicationInfix(
        partial,
        name='to',
        action_to_call=atomically(will(returned) |then>> eventually),
    )
)


by = documenting_by(
    """
    `PartialApplicationInfix` instance that implements `rpartial` as a pseudo
    operator.

    See `PartialApplicationInfix` for usage information.
    """
)(
    _CustomPartialApplicationInfix(rpartial, name='by')
)


shown: dirty[reformer_of[V]]
shown = documenting_by("""Shortcut function for `returnly(print)`.""")(
    returnly(print)
)


yes: action_for[bool] = documenting_by("""Shortcut for `to(True)`.""")(to(True))
no: action_for[bool] = documenting_by("""Shortcut for `to(False)`.""")(to(False))


class _ForceComparable:
    """Class for objects that are aware of the results of their `==` checks."""

    def __init__(self, name: str, *, forced_sign: bool):
        self._name = name
        self._forced_sign = forced_sign

    def __repr__(self) -> str:
        return self._name

    def __eq__(self, _: Any) -> bool:
        return self._forced_sign


anything = documenting_by(
    """Special object always returning `True` when `==` is checked."""
)(
    _ForceComparable("anything", forced_sign=True)
)
