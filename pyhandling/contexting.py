from abc import ABC, abstractmethod
from functools import update_wrapper
from inspect import Signature
from typing import (
    Generic, Any, Iterator, Callable, Iterable, GenericAlias, Optional, Self
)

from pyannotating import Special

from pyhandling.annotations import (
    ActionT, ErrorT, P, Pm, checker_of, FlagT, A, B, C, V, R, E
)
from pyhandling.atoming import atomic
from pyhandling.flags import nothing, Flag, pointed, FlagVector
from pyhandling.immutability import property_to
from pyhandling.partials import partially
from pyhandling.signature_assignmenting import call_signature_of
from pyhandling.synonyms import repeating
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
    "saving_context",
    "to_context",
    "to_write",
    "to_read",
    "with_context_that",
    "is_metacontextual",
    "with_reduced_metacontext",
    "without_metacontext",
)


class contextual_like(NotInitializable):
    """
    Annotation class of objects that can be cast to `ContextRoot`.

    Such objects are iterable objects consisting the main value and the context
    describing the main value.

    Checks using the `isinstance` function.

    The `[]` callback can be used to create an appropriate annotation.
    """

    def __class_getitem__(
        cls,
        value_or_value_and_context: Any | tuple[Any, Any],
    ) -> GenericAlias:
        value_and_context = (
            value_or_value_and_context
            if isinstance(value_or_value_and_context, Iterable)
            else (value_or_value_and_context, Any)
        )

        value, context = value_and_context

        return tuple[value, context]

    @classmethod
    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, Iterable) and len(tuple(instance)) == 2


class ContextRoot(ABC, Generic[V, C]):
    """
    Abstract value form class, for holding an additional value, describing the
    main value.

    Comparable by form implementation and stored values.

    Iterable over stored values for unpacking capability, where the first value
    is the main value and the second is the context describing the main value.

    Attributes for stored values are defined in concrete forms.
    """

    _value: V
    _context: C

    def __repr__(self) -> str:
        return f"{self._repr_of(self._value)} when {self._repr_of(self._context)}"

    def __eq__(self, other: Any) -> bool:
        if type(self) is not type(other):
            return False

        value, context = other

        return self._value == value and self._context == context

    def __iter__(self) -> Iterator:
        return iter((self._value, self._context))

    def _repr_of(self, value: Special["contextual"]) -> str:
        return (
            f"({value})"
            if (
                type(value) in (contextual, ContextualError)
                and type(self) is type(value)
            )
            else str(value)
        )


class _BinaryForm(ABC, Generic[V, C]):
    def __init__(self, value: V | Self, *contexts: C):
        if len(contexts) > 1:
            value = type(self)(value, *contexts[:-1])

        self._reset(value, nothing if len(contexts) == 0 else contexts[-1])

    @abstractmethod
    def _reset(self, value: V, context: C) -> None:
        ...


class contextual(ContextRoot, _BinaryForm, Generic[V, C]):
    """Basic `ContextRoot` form representing values with no additional effect."""

    value = property_to("_value")
    context = property_to("_context")

    def _reset(self, value: V, context: C) -> None:
        self._value = value
        self._context = context


class contextually(ContextRoot, _BinaryForm, Generic[ActionT, C]):
    """`ContextRoot` form for annotating actions with saving their call."""

    action = property_to("_value")
    context = property_to("_context")

    def __init__(self, action: Callable[Pm, R], contexts: C = nothing):
        _BinaryForm.__init__(self, action, *contexts)

        update_wrapper(self, self._value)
        self.__signature__ = self._get_signature()

    def __repr__(self) -> str:
        return f"contextually({super().__repr__()})"

    def __call__(self, *args: Pm.args, **kwargs: Pm.kwargs) -> R:
        return self._value(*args, **kwargs)

    def _reset(self, value: Callable[Pm, R], context: C) -> None:
        self._action = value
        self._context = context

    def _get_signature(self) -> Signature:
        return call_signature_of(self._value)


class ContextualError(Exception, ContextRoot, _BinaryForm, Generic[ErrorT, C]):
    """
    `ContextRoot` form for annotating an error with a context while retaining
    the ability to `raise` the call.
    """

    error = property_to("_value")
    context = property_to("_context")

    def __init__(self, error: ErrorT, context: C):
        _BinaryForm.__init__(self, error, context)
        super().__init__(repr(self))

    def __repr__(self) -> str:
        return f"\"{self._value}\" error when {self._context}"

    def _reset(self, value: ErrorT, context: C) -> None:
        self._value = value
        self._context = context


class context_pointed(ContextRoot, Generic[ActionT, FlagT]):
    """
    Extract `ContextRoot` form from a `contextual_like` object  with a context
    flag pointing the original context.

    Optionally selects flags at initialization.

    Has an atomic form, specified as the same value in context of point of the
    newly converted context (flag) atomic version.
    """

    value = property_to("_value")
    flag = property_to("_context")

    def __init__(
        self,
        value_and_context: contextual_like[V, P | Flag[P]],
        that: checker_of[P] = lambda _: True,
    ):
        value, context = value_and_context

        self._value = value
        self._context = pointed(context).that(that)

    def __repr__(self) -> str:
        return f"context_pointed({super().__repr__()})"

    def __getatom__(self) -> contextual[V, P]:
        return contextual(self._value, when=atomic(self._context).point)


def context_oriented(root_values: contextual_like[V, C]) -> contextual[C, V]:
    """Function to swap a context and value."""

    return contextual(*reversed(tuple(root_values)))


_ExistingC = TypeVar("_ExistingC")


def contexted(
    value: V | ContextRoot[V, _ExistingC],
    when: Optional[Special[FlagVector, C]] = None,
) -> ContextRoot[V, _ExistingC | Flag | C]:
    """
    Function to represent an input value in `contextual` form if it is not
    already present.

    When passing a forced context in the form of `FlagVector`, add an additional
    flag to the context by this vector, otherwise sets a forced context.
    """

    value, context = (
        value if isinstance(value, ContextRoot) else contextual(value)
    )

    if isinstance(when, FlagVector):
        context = when(pointed(context))
    elif when is not None:
        context = when

    return contextual(value, context)


@partially
def saving_context(
    action: Callable[[A], B],
    value_and_context: contextual_like[A, C],
) -> ContextRoot[B, C]:
    """Execution context without effect."""

    value, context = value_and_context

    return contextual(action(value), when=context)


@partially
def to_context(
    action: Callable[[A], B],
    value_and_context: contextual_like[V, A],
) -> ContextRoot[V, B]:
    """Execution context for context value context calculations."""

    return context_oriented(saving_context(
        action,
        context_oriented(value_and_context),
    ))


@partially
def to_write(
    action: Callable[[V, C], R],
    value: contextual_like[V, C],
) -> contextual[V, R]:
    stored_value, context = value

    return contextual(context, action(stored_value, context))


@partially
def to_read(
    action: Callable[[V, C], R],
    value: contextual_like[V, C],
) -> contextual[R, V]:
    return context_oriented(to_write(action, context_oriented(value)))


@partially
def with_context_that(
    that: checker_of[P],
    value: V | ContextRoot[V, P | Flag[P]],
    *,
    and_nothing: bool = True,
) -> contextual[V, nothing | P]:
    """
    Function for transform `ContextRoot` with context filtered by input
    checker.

    When a context is `Flag`, the resulting context will be filtered by any of
    its values.

    Returns `nothing` if a context is invalid for an input checker or throws an
    error when `and_nothing=True`.
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
    value: ContextRoot[ContextRoot[V, Any], Any]
) -> contextual[V, Flag]:
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
