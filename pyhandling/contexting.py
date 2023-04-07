from functools import cached_property
from inspect import Signature
from operator import attrgetter, not_
from typing import Generic, Any, Iterator, Callable

from pyannotating import Special

from pyhandling.annotations import ValueT, ContextT, ActionT, ErrorT, ValueT, PointT, ResultT, P, checker_of, reformer_of
from pyhandling.atoming import atomic
from pyhandling.flags import flag, nothing, Flag
from pyhandling.immutability import property_of
from pyhandling.branching import binding_by, repeating, on
from pyhandling.language import then, by
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.tools import documenting_by


__all__ = (
    "contextual",
    "contextually",
    "ContextualError",
    "context_pointed",
    "context_oriented",
    "merged_contextual_floor",
    "merged_contextual_floors",
    "as_contextual",
    "to_contextual_form",
)


class contextual(Generic[ValueT, ContextT]):
    """Representer of an input value as a value with a context."""

    value = property_of("_value")
    context = property_of("_context")

    def __init__(self, value: ValueT, when: ContextT = nothing):
        self._value = value
        self._context = when

    def __repr__(self) -> str:
        return _contextual_repr_of(self)

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))


class contextually(ActionWrapper, Generic[ActionT, ContextT]):
    action = property_of("_action")
    context = property_of("_context")

    def __init__(self, action: Callable[P, ResultT], when: ContextT = nothing):
        self._context = when
        super().__init__(action)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._action(*args, **kwargs)

    def __repr__(self) -> str:
        return _contextual_repr_of(self)

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    @property
    def _force_signature(self) -> Signature:
        return calling_signature_of(self._action)


class ContextualError(Exception, Generic[ErrorT, ContextT]):
    """
    Error class to store the context of another error and itself.
    Iterates to unpack.
    """
   
    error = property_of("_ContextualError__error")
    context = property_of("_ContextualError__context")

    def __init__(self, error: ErrorT, context: ContextT):
        self.__error = error
        self.__context = context

        super().__init__(self._error_message)

    def __iter__(self) -> Iterator:
        return iter((self.__error, self.__context))

    @cached_property
    def _error_message(self) -> str:
        return _contextual_repr_of(self)


class context_pointed(Generic[ValueT, PointT]):
    """
    Class to replace a context of a `contextual-like` object with a flag
    pointing to the original context.

    Optionally selects flags.

    Getting a value and the newly created context is only available through
    unpacking.

    Has an atomic form, specified as the same value in context of point of the
    newly converted context (flag) atomic version.
    """

    value = property_of("_value")
    flag = property_of("_flag")

    def __init__(
        self,
        value_and_context: tuple[ValueT, PointT | Flag[PointT]],
        is_for_selection: checker_of[PointT] = lambda _: True,
    ):
        value, context = value_and_context

        self._value = value
        self._flag = flag_to(context).of(is_for_selection)

    def __repr__(self) -> str:
        return f"context_pointed({_contextual_repr_of((self._value, self._flag))})"

    def __iter__(self) -> Iterator:
        return iter((self._value, self._flag))

    def __getatom__(self) -> contextual[ValueT, PointT]:
        return contextual(self._value, when=atomic(self._flag).point)


def context_oriented(root_values: tuple[ValueT, ContextT]) -> contextual[ContextT, ValueT]:
    """Function to swap a context and value."""

    context, value = root_values

    return contextual(value, when=context)


def merged_contextual_floor(
    contextual_floor: contextual[contextual[ValueT, Any], Any]
) -> contextual[ValueT, Flag]:
    return contextual(
        contextual_floor.value.value,
        when=flag_to(contextual_floor.context, contextual_floor.value.context),
    )


merged_contextual_floors: reformer_of[contextual] = repeating(
    merged_contextual_floor,
    attrgetter("value") |then>> (isinstance |by| contextual),
)


as_contextual: Callable[[ValueT | contextual[ValueT, Any]], contextual[ValueT, Any]]
as_contextual = documenting_by(
    """
    Function to represent an input value in `contextual` form if it is not
    already present.
    """
)(
    on((isinstance |by| contextual) |then>> not_, contextual)
)


to_contextual_form = binding_by(as_contextual |then>> ...)


def _contextual_repr_of(value_and_context: tuple[Any, Special[Flag]]) -> str:
    """Function to render any `contextual-like` object."""

    value, context = value_and_context

    return f"{value} when {{}}".format(
        ' and '.join(map(lambda flag: str(flag.point), context))
        if isinstance(context, Flag) and context != nothing
        else context
    )
