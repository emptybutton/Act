from abc import ABC, abstractmethod
from functools import cached_property, update_wrapper
from inspect import Signature
from operator import attrgetter, not_
from typing import Generic, Any, Iterator, Callable, Iterable, GenericAlias, TypeVar, Optional

from pyannotating import Special

from pyhandling.annotations import ValueT, ContextT, ActionT, ErrorT, ValueT, PointT, ResultT, P, checker_of, reformer_of, FlagT, action_of
from pyhandling.atoming import atomic, atomically
from pyhandling.flags import flag, nothing, Flag, pointed, FlagVector
from pyhandling.immutability import property_to
from pyhandling.language import then, by
from pyhandling.partials import fragmentarily
from pyhandling.signature_assignmenting import ActionWrapper, calling_signature_of
from pyhandling.synonyms import with_unpacking, repeating
from pyhandling.tools import documenting_by, NotInitializable


__all__ = (
    "contextual_like",
    "ContextRoot",
    "contextual",
    "contextually",
    "ContextualError",
    "context_pointed",
    "context_oriented",
    "contexted",
    "with_context_that",
    "is_metacontextual",
    "with_reduced_metacontext",
    "without_metacontext",
)


class contextual_like(NotInitializable):
    def __class_getitem__(self, value_or_value_and_context: Any | tuple[Any, Any]) -> GenericAlias:
        value_and_context = (
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
        return f"{self._value} when {self._context}"

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        value, context = other

        return self._value == value and self._context == context

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))


class contextual(ContextRoot, Generic[ValueT, ContextT]):
    """Representer of an input value as a value with a context."""

    value = property_to("_value")
    context = property_to("_context")

    def __init__(self, value: ValueT, when: ContextT = nothing):
        self._value = value
        self._context = when


class contextually(ContextRoot, Generic[ActionT, ContextT]):
    action = property_to("_value")
    context = property_to("_context")

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


class ContextualError(Exception, ContextRoot, Generic[ErrorT, ContextT]):
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


class context_pointed(ContextRoot, Generic[ActionT, FlagT]):
    """
    Class to replace a context of a `contextual-like` object with a flag
    pointing to the original context.

    Optionally selects flags.

    Getting a value and the newly created context is only available through
    unpacking.

    Has an atomic form, specified as the same value in context of point of the
    newly converted context (flag) atomic version.
    """

    value = property_to("_value")
    flag = property_to("_context")

    def __init__(
        self,
        value_and_context: contextual_like[ValueT, PointT | Flag[PointT]],
        that: checker_of[PointT] = lambda _: True,
    ):
        value, context = value_and_context

        self._value = value
        self._context = pointed(context).that(that)

    def __repr__(self) -> str:
        return f"context_pointed({super().__repr__()})"

    def __getatom__(self) -> contextual[ValueT, PointT]:
        return contextual(self._value, when=atomic(self._context).point)


def context_oriented(root_values: contextual_like[ValueT, ContextT]) -> contextual[ContextT, ValueT]:
    """Function to swap a context and value."""

    return contextual(*reversed(tuple(root_values)))


_ExistingContextT = TypeVar("_ExistingContextT")


def contexted(
    value: ValueT | ContextRoot[ValueT, _ExistingContextT],
    when: Optional[Special[FlagVector, ContextT]] = None,
) -> ContextRoot[ValueT, _ExistingContextT | Flag | ContextT]:
    """
    Function to represent an input value in `contextual` form if it is not
    already present.
    """

    value, context = value if isinstance(value, ContextRoot) else contextual(value)

    if isinstance(when, FlagVector):
        context = when(context)
    elif when is not None:
        context = when

    return contextual(value, context)


@fragmentarily
def with_context_that(
    that: checker_of[PointT],
    value: ValueT | ContextRoot[ValueT, PointT | Flag[PointT]],
    *,
    and_nothing: bool = False,
) -> contextual[ValueT, nothing | PointT]:
    """
    Function for transform function `ContextRoot` with context filtered by input
    checker.

    When a context is `Flag`, the resulting context will be filtered by any of
    its values.

    Returns `nothing` if a context is invalid for an input checker.
    """

    root = atomic(context_pointed(contexted(value), that=that))

    if root.context == nothing and not and_nothing:
        raise ValueError(f"Missing context with condition of \"{that}\"")

    return root


def is_metacontextual(value: Special[ContextRoot[ContextRoot, Any], Any]) -> bool:
    """
    Function to check `ContextRoot`'s' describing another `ContextRoot` if it is
    at all `ContextRoot`.
    """

    return isinstance(value, ContextRoot) and isinstance(value.value, ContextRoot)


def with_reduced_metacontext(
    value: ContextRoot[ContextRoot[ValueT, Any], Any]
) -> contextual[ValueT, Flag]:
    """
    Function to remove nesting of two `ContextRoot`s.
    The resulting context is a flag sum from the top and bottom `ContextRoot`.
    """

    meta_root = contextual(*value)
    root = meta_root.value

    return contexted(root, +pointed(meta_root.context))


without_metacontext: Callable[[ContextRoot], contextual]
without_metacontext = documenting_by(
    """
    Function to fully glue nested `ContextRoot`s.
    The resulting context is a flag sum from all nested `ContextRoot`s.
    """
)(
    repeating(with_reduced_metacontext, while_=is_metacontextual)
)