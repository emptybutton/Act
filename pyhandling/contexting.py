from functools import cached_property
from inspect import Signature
from operator import attrgetter, not_
from typing import Generic, Any, Iterator, Callable, Iterable, GenericAlias

from pyannotating import Special

from pyhandling.annotations import ValueT, ContextT, ActionT, ErrorT, ValueT, PointT, ResultT, P, checker_of, reformer_of
from pyhandling.atoming import atomic
from pyhandling.flags import flag, nothing, Flag
from pyhandling.immutability import property_of
from pyhandling.branching import binding_by, repeating, on
from pyhandling.language import then, by
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.tools import documenting_by, NotInitializable


__all__ = (
    "contextual_like",
    "ContextRoot",
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


class contextual_like(NotInitializable):
    def __class_getitem__(self, value_or_value_and_context: Any | tuple[Any, Any]) -> GenericAlias:
        value_and_contextcontextual_like = (
            value_or_value_and_context
            if isinstance(value_or_value_and_context, Iterable)
            else (value_or_value_and_context, Any)
        )

        value, context = value_and_context

        return tuple[value, context]

    @classmethod
    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(instance, Iterable) and len(tuple(instance)) == 2


class ContextRoot(ABC, Generic[ValueT, ContextT]):
    _value: ValueT
    _context: ContextT

    def __repr__(self) -> str:
        return f"{self._value} when {{}}".format(
            ' and '.join(map(lambda flag: str(flag.point), self._context))
            if isinstance(self._context, Flag) and self._context != nothing
            else self._context
        )

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    def __eq__(self, other: contextual_like) -> bool:
        value, context = other

        return self._value == value and self._context == context

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))


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


class contextual(_ContextRoot, Generic[ValueT, ContextT]):
    """Representer of an input value as a value with a context."""

    value = property_to("_value")
    context = property_to("_context")

    def __init__(self, value: ValueT, when: ContextT = nothing):
        self._value = value
        self._context = when


class contextually(_ContextRoot, Generic[ActionT, ContextT]):
    action = property_to("_value")
    context = property_to("_context")

def merged_contextual_floor(
    contextual_floor: contextual[contextual[ValueT, Any], Any]
    def __init__(self, action: Callable[P, ResultT], when: ContextT = nothing):
        self._value = action
        self._context = when

        update_wrapper(self, self._value)
        self.__signature__ = self._get_signature()

    def __repr__(self) -> str:
        return f"contextually({super().__repr__()})"

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self._value(*args, **kwargs)

    def _get_signature(self) -> Signature:
        return calling_signature_of(self._value)


class ContextualError(Exception, _ContextRoot, Generic[ErrorT, ContextT]):
    """
    Error class to store the context of another error and itself.
    Iterates to unpack.
    """
   
    error = property_to("_value")
    context = property_to("_context")

    def __init__(self, error: ErrorT, context: ContextT):
        self._value = error
        self._context = context

        super().__init__(repr(self))

    def __repr__(self) -> str:
        return f"\"{self._value}\" error when {self._context}"


def context_oriented(root_values: contextual_like[ValueT, ContextT]) -> contextual[ContextT, ValueT]:
    """Function to swap a context and value."""

    return contextual(*reversed(root_values))
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


    )
